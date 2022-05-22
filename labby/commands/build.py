"""Labby build command.

Handles the complete build of a Labby Project.

Example:
> labby build project --project-file "myproject.yaml"
"""
from pathlib import Path
from typing import Optional

import typer
from netaddr import IPNetwork
from nornir.core.helpers.jinja_helper import render_from_file
from nornir_utils.plugins.functions import print_result
from rich.prompt import Prompt

from labby import utils
from labby.models import LabbyProject
from labby.project_data import ProjectData, get_project_from_file
from labby.nornir_tasks import config_task


app = typer.Typer(help="Builds a complete Network Provider Lab in a declarative way.")


def bootstrap_nodes(
    project: LabbyProject,
    project_data: ProjectData,
    user: str,
    password: str,
    boot_delay: int = 5,
    delay_multiplier: int = 1,
):
    """Runs the bootstrap tasks for all devices in the project.

    Args:
        project (LabbyProject): The project to build.
        project_data (ProjectData): The project data processed from project file.
        user (str): The username to use for the devices.
        password (str): The password to use for the devices.
        boot_delay (int, optional): The boot delay to use for the devices. Defaults to 5.
        delay_multiplier (int, optional): The delay multiplier to use for the devices. Defaults to 1.
    """
    for node_spec in project_data.nodes_spec:

        # Skip devices that are not going to be configured
        if node_spec.get("config_managed", True) is False:
            continue

        for node_name in node_spec.get("nodes", []):

            device = project.search_node(name=node_name)

            # Validate devices exists in the project
            if device is None:
                utils.console.log(
                    f"[b]({project.name})[/] Node is not created: [i dark_orange3]{node_name}", style="error"
                )
                continue

            # Render bootstrap config
            if node_spec.get("bootstrap_config_template"):
                cfg_template = Path(node_spec["bootstrap_config_template"])
                utils.console.log(
                    f"[b]({project.name})[/] Rendering bootstrap config from template [cyan i]{cfg_template}[/]"
                )
                cfg_data = render_from_file(
                    path=str(cfg_template),
                    template=cfg_template.name,
                    jinja_filters={"ipaddr": utils.ipaddr_renderer},
                    **node_spec,
                )

            else:
                utils.console.log(f"[b]({project.name})({device.name})[/] Rendering bootstrap config")
                if device.mgmt_port is None:
                    utils.console.log(
                        f"Node [cyan i]{node_name}[/] mgmt_port parameter must be set. Run update command",
                        style="error",
                    )
                    continue
                if device.mgmt_addr is None:
                    utils.console.log(
                        f"Node [cyan i]{node_name}[/] mgmt_addr parameter must be set. Run update command",
                        style="error",
                    )
                    continue

                if device.net_os is None:
                    utils.console.log(
                        f"Node [cyan i]{node_name}[/] net_os parameter must be set. Verify node template name",
                        style="error",
                    )
                    continue

                # Render bootstrap config
                cfg_template = Path(__file__).parent.parent / "templates" / f"nodes_bootstrap/{device.net_os}.cfg.j2"

                # Validate template exists
                if not cfg_template.exists():
                    utils.console.log(
                        f"[b]({project.name})[/] Bootstrap config template not found: [cyan i]{cfg_template}[/]",
                        style="error",
                    )
                    continue

                cfg_data = render_from_file(
                    path=str(cfg_template.parent),
                    template=cfg_template.name,
                    jinja_filters={"ipaddr": utils.ipaddr_renderer},
                    **dict(
                        mgmt_port=device.mgmt_port,
                        mgmt_addr=device.mgmt_addr,
                        user=user,
                        password=password,
                        node_name=node_name,
                    ),
                )
            utils.console.log(f"[b]({project.name})({device.name})[/] Bootstrap config rendered", style="good")

            # Run node bootstrap config process
            device.bootstrap(config=cfg_data, boot_delay=boot_delay, delay_multiplier=delay_multiplier)


def config_nodes(
    project: LabbyProject,
    project_data: ProjectData,
    model: Optional[str] = None,
    net_os: Optional[str] = None,
    name: Optional[str] = None,
    silent: bool = False,
):
    """Runs configuration tasks for all devices in the project.

    Args:
        project (LabbyProject): The project to build.
        project_data (ProjectData): The project data processed from project file.
        model (str): The model to filter the devices from.
        net_os (str): The net_os to filter the devices from.
        name (str): The name blob to filter the devices from.
        silent (bool, optional): If true, will not print the result. Defaults to False.
    """
    # Apply filters
    if model:
        nr_filtered = project.nornir.filter(filter_func=lambda n: model == n.data["labby_obj"].model)  # type: ignore
    elif net_os:
        nr_filtered = project.nornir.filter(filter_func=lambda n: net_os == n.data["labby_obj"].net_os)  # type: ignore
    elif name:
        nr_filtered = project.nornir.filter(filter_func=lambda n: name in n.data["labby_obj"].name)  # type: ignore
    else:
        nr_filtered = project.nornir.filter(filter_func=lambda n: n.data["labby_obj"].config_managed)  # type: ignore

    utils.console.log(
        f"[b]({project.name})[/] Devices to configure: [i dark_orange3]{list(nr_filtered.inventory.hosts.keys())}[/]"
    )
    result = nr_filtered.run(task=config_task, project_data=project_data, project=project)
    if not silent:
        utils.console.rule(title="Start section")
        print_result(result)  # type: ignore
        utils.console.rule(title="End section")
    utils.console.log(
        f"[b]({project.name})[/] Devices configured: [i dark_orange3]{list(nr_filtered.inventory.hosts.keys())}[/]"
    )


def build_topology(project: LabbyProject, project_data: ProjectData):
    # pylint: disable=too-many-locals
    """Builds a project topology.

    Args:
        project (LabbyProject): The project to build.
        project_data (ProjectData): The project data processed from project file.
    """
    # Determine mgmt network
    mgmt_ips = project_data.mgmt_ips
    prefixlen = IPNetwork(project_data.mgmt_network["network"]).prefixlen

    # Create nodes
    index = 0
    for node_spec in project_data.nodes_spec:
        for node_name in node_spec.get("nodes", []):

            device = project.search_node(name=node_name)

            # Validate devices exists in the project
            if device:
                utils.console.log(f"[b]({project.name})[/] Node already created: [i dark_orange3]{node_name}")
                continue

            labels = node_spec.get("labels", [])

            extra_params = {}
            if node_spec.get("config_managed") is not None:
                extra_params["config_managed"] = node_spec.get("config_managed")

            # TODO: Add support to detect changes in node.mgmt_addr assignments
            mgmt_port = node_spec.get("mgmt_port")

            # Assign IP Address
            addr = f"{mgmt_ips[index]}/{prefixlen}"
            mgmt_addr = None
            if project_data.mgmt_network.get("gateway") == addr:
                # Skip the gw address (TODO: To improve)
                index += 1
                mgmt_addr == mgmt_ips[index]  # pylint: disable=pointless-statement
            else:
                mgmt_addr = addr
            index += 1

            utils.console.log(f"[b]({project.name})[/] Creating node: [i dark_orange3]{node_name}")
            _ = project.create_node(
                name=node_name,
                template=node_spec["template"],
                labels=labels,
                mgmt_port=mgmt_port,
                mgmt_addr=mgmt_addr,
                **extra_params,
            )

    # Create links
    for link_spec in project_data.links_spec:
        for link_info in link_spec.get("links", []):
            link_name = f"{link_spec['node']}: {link_info['port']} <==> {link_info['port_b']}: {link_info['node_b']}"
            utils.console.log(f"[b]({project.name})[/] Creating link: [i dark_orange3]{link_name}")
            _ = project.create_link(
                node_a=link_spec["node"],
                port_a=link_info["port"],
                port_b=link_info["port_b"],
                node_b=link_info["node_b"],
                filters=link_info.get("filters"),
                labels=link_info.get("labels", []),
            )


@app.command(short_help="Builds a Project in a declarative way.", name="project")
def labby_project(
    project_file: Path = typer.Option(
        Path("labby_project.yml"), "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"
    ),
    user: str = typer.Option(
        ..., "--user", "-u", help="Initial user to configure on the system.", envvar="LABBY_NODE_USER"
    ),
    password: str = typer.Option(
        ..., "--password", "-w", help="Initial password to configure on the system.", envvar="LABBY_NODE_PASSWORD"
    ),
    boot_delay: int = typer.Option(5, help="Time in seconds to wait on device boot if it has not been started"),
    delay_multiplier: int = typer.Option(
        1, help="Delay multiplier to apply to boot/config delay before timeouts. Applicable over console connection."
    ),
):
    """
    Build a Project in a declarative way.

    The project is built based on the contents of the project file.

    Example:

    > labby build project --project-file "myproject.yaml"
    """
    prj, project_data = get_project_from_file(project_file)

    # Build project
    build_topology(project=prj, project_data=project_data)

    # Bootstrap nodes
    is_bootstrap_required = Prompt.ask(
        "Do you want to bootstrap the nodes?", console=utils.console, choices=["yes", "no"], default="yes"
    )
    if is_bootstrap_required == "yes":
        bootstrap_nodes(
            project=prj,
            project_data=project_data,
            user=user,
            password=password,
            boot_delay=boot_delay,
            delay_multiplier=delay_multiplier,
        )

    # Configure nodes
    is_config_required = Prompt.ask(
        "Do you want to configure the nodes?", console=utils.console, choices=["yes", "no"], default="yes"
    )
    if is_config_required == "yes":
        config_nodes(project=prj, project_data=project_data)


@app.command(short_help="Builds a Project Topology.")
def topology(
    project_file: Path = typer.Option(
        Path("labby_project.yml"), "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"
    ),
):
    """
    Builds a topology from a given project file.

    Example:

    > labby build topology --project-file "myproject.yml"
    """
    prj, project_data = get_project_from_file(project_file)

    build_topology(project=prj, project_data=project_data)


@app.command(short_help="Runs the bootstrap config process on the devices of a Project.")
def bootstrap(
    project_file: Path = typer.Option(
        Path("labby_project.yml"), "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"
    ),
    user: str = typer.Option(
        ..., "--user", "-u", help="Initial user to configure on the system.", envvar="LABBY_NODE_USER"
    ),
    password: str = typer.Option(
        ..., "--password", "-w", help="Initial password to configure on the system.", envvar="LABBY_NODE_PASSWORD"
    ),
    boot_delay: int = typer.Option(5, help="Time in seconds to wait on device boot if it has not been started"),
    delay_multiplier: int = typer.Option(
        1, help="Delay multiplier to apply to boot/config delay before timeouts. Applicable over console connection."
    ),
):
    """
    Runs the bootstrap config process on the devices of a Project.

    Example:

    > labby build bootstrap --project-file "myproject.yml"
    """
    prj, project_data = get_project_from_file(project_file)

    bootstrap_nodes(
        project=prj,
        project_data=project_data,
        user=user,
        password=password,
        boot_delay=boot_delay,
        delay_multiplier=delay_multiplier,
    )


@app.command(short_help="Runs the configuration process on the devices of a Project.")
def configs(
    project_file: Path = typer.Option(
        Path("labby_project.yml"), "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter devices based on the model provided"),
    net_os: Optional[str] = typer.Option(None, "--net-os", "-n", help="Filter devices based on the net_os provided"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter devices based on the name"),
    silent: bool = typer.Option(False, "--silent", "-s", help="Silent mode", envvar="LABBY_SILENT"),
):
    """
    Runs the configuration process on the devices of a Project.

    Example:

    > labby build configs --project-file "myproject.yml"
    """
    prj, project_data = get_project_from_file(project_file)

    # Config Nodes
    config_nodes(project=prj, project_data=project_data, model=model, net_os=net_os, name=name, silent=silent)
