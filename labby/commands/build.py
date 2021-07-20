"""Labby build command.

Handles the complete build of a Labby Project.

Example:
> labby build project --project-file "myproject.yaml"
"""
from typing import Optional, Tuple

from labby.models import LabbyProject
import typer
from pathlib import Path
from labby import utils, config
from nornir.core.task import Task, AggregatedResult
from nornir_scrapli.tasks import send_config, send_command
from nornir.core.helpers.jinja_helper import render_from_file
from nornir_utils.plugins.functions import print_result
from netaddr import IPNetwork


app = typer.Typer(help="Builds a complete Network Provider Lab in a declarative way.")


SHOW_RUN_COMMANDS = {
    "arista_eos": "show run",
    "cisco_ios": "show run",
    "cisco_iosxe": "show run",
    "cisco_nxos": "show run",
}


SAVE_COMMANDS = {
    "arista_eos": "wr mem",
    "cisco_ios": "wr mem",
    "cisco_iosxe": "wr mem",
    "cisco_nxos": "copy running-config startup-config",
}


class ProjectData:
    def __init__(self, project_file: Path) -> None:
        if project_file.is_file():
            self.project_file = project_file
            self.project_data = self.get_project_data()
            for required in config.REQUIRED_PROJECT_FIELDS:
                if required not in self.project_data:
                    raise ValueError(f"Missing required fields in project file: {required}")
            self.name = self.project_data["main"]["name"]
            self.mgmt_network = self.project_data["main"]["mgmt_network"]
            self.mgmt_creds = self.project_data["main"]["mgmt_creds"]
            self.version = self.project_data["main"].get("version", "1.0")
            self.description = self.project_data["main"].get("description", "")
            self.contributors = self.project_data["main"].get("contributors", [])
            self.template = self.project_data["main"].get("template", "")
            self.labels = self.project_data["main"].get("labels", [])

            # Check creds
            self.check_creds()

            # Project nodes and links
            self.nodes_spec = self.project_data.get("nodes_spec", [])
            self.links_spec = self.project_data.get("links_spec", [])

            # Vars
            self.vars = self.project_data.get("vars", {})

            # Extra properties
            self.extra_properties = self.project_data.get("extra_properties", {})

        else:
            raise FileNotFoundError(f"Project file not found: {project_file}")

    def get_project_data(self) -> dict:
        """Get the project data from the project file."""
        return utils.load_yaml_file(str(self.project_file))

    def check_creds(self) -> None:
        """Check if the credentials are valid."""
        if not utils.check_creds(self.mgmt_network, self.mgmt_creds):
            raise ValueError("Invalid credentials for the management network")


def backup_task(task: Task):
    task.run(task=send_command, command=SHOW_RUN_COMMANDS[task.host.platform])  # type: ignore


def save_task(task: Task):
    task.run(task=send_command, command=SAVE_COMMANDS[task.host.platform])  # type: ignore


def config_task(task: Task, project_data: ProjectData, project: LabbyProject):
    cfg_data = render_from_file(
        path=str(Path(project_data.template).parent),
        template=Path(project_data.template).name,
        jinja_filters={"ipaddr": utils.ipaddr_renderer},
        **dict(project=project, node=task.host.data["labby_obj"], **project_data.vars),
    )
    task.run(task=send_config, config=cfg_data)


def get_project_from_file(project_file: Path) -> Tuple[LabbyProject, ProjectData]:
    """Get the project from the project file."""
    project_data = ProjectData(project_file)
    utils.console.log(f"[b]({project_data.name})[/] Retrieving project specification")
    provider = config.get_provider()
    project = provider.search_project(project_name=project_data.name)
    if project:
        utils.console.log(f"[b]({project.name})[/] Project already exists")
    else:
        project_args = dict(project_name=project_data.name, labels=project_data.labels, **project_data.extra_properties)
        project = provider.create_project(**project_args)
        utils.console.log(f"[b]({project.name})[/] Project created")
    return project, project_data


@app.command(short_help="Builds a Project in a declarative way.")
def project(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
):
    """
    Build a Project in a declarative way.

    The project is built based on the contents of the project file.

    Example:

    > labby build project --project-file "myproject.yaml"
    """
    project, project_data = get_project_from_file(project_file)

    # Create nodes
    for node_spec in project_data.nodes_spec:
        for node in node_spec.get("nodes", []):
            node_name = node["name"]
            print(f"Creating node: {node_name}")
            node = project.create_node(name=node_name, template=node_spec["template"], **node)

            # Bootstrap noode
            node.bootstrap(config="this where the config should be for bootstrap")

    # Create links
    for link_spec in project_data.links_spec:
        for link_info in link_spec.get("links", []):
            # link_name = link_info["name"]
            # print(f"Creating link: {link_name}")
            link = project.create_link(
                node_a=link_spec["node"],
                port_a=link_info["port"],
                port_b=link_info["port_b"],
                node_b=link_info["node_b"],
                filters=link_info.get("filters"),
                **link_info,
            )
            print(f"Created link: {link}")

    # Render configs
    if project_data.template:
        for node_name, node in project.nodes.items():
            cfg_data = render_from_file(
                path=str(Path(project_data.template).parent),
                template=Path(project_data.template).name,
                jinja_filters={"ipaddr": utils.ipaddr_renderer},
                **dict(project=project, node=node, **project_data.vars),
            )

            # Configure nodes
            project.init_nornir()
            if project.nornir is None:
                raise ValueError("Nornir not initialized")
            responses: AggregatedResult = project.nornir.run(task=config_task, config=cfg_data)
            print(responses)


@app.command(short_help="Builds a Project Topology.")
def topology(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
):
    """
    Builds a topology from a given project file.

    Example:

    > labby build topology --project-file "myproject.yml"
    """
    project, project_data = get_project_from_file(project_file)

    # Create nodes
    for node_spec in project_data.nodes_spec:
        for node_name in node_spec.get("nodes", []):
            print(f"Creating node: {node_name}")
            _ = project.create_node(name=node_name, template=node_spec["template"], **node_spec)

    # Create links
    for link_spec in project_data.links_spec:
        for link_info in link_spec.get("links", []):
            # link_name = link_info["name"]
            # print(f"Creating link: {link_name}")
            link = project.create_link(
                node_a=link_spec["node"],
                port_a=link_info["port"],
                port_b=link_info["port_b"],
                node_b=link_info["node_b"],
                filters=link_info.get("filters"),
                **link_info,
            )
            print(f"Created link: {link}")


@app.command(name="save", short_help="Save Nodes Configuration.")
def nodes_save(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter devices based on the model provided"),
    net_os: Optional[str] = typer.Option(None, "--net-os", "-n", help="Filter devices based on the net_os provided"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter devices based on the name"),
):
    """
    Builds a topology from a given project file.

    Example:

    > labby build save --project-file "myproject.yml" --backup /path/to/backup/folder
    """
    project, project_data = get_project_from_file(project_file)

    mgmt_network = IPNetwork(project_data.mgmt_network)
    # Verify nodes created to be managed match the ones in the project
    index = 0
    for node_spec in project_data.nodes_spec:
        for node_name in node_spec.get("nodes", []):
            # TODO: Add logs for DEBUG example, like this one:
            # utils.console.log(f"[b]({project.name})[/] Checking parameters on node: [i dark_orange3]{node_name}")
            node = project.search_node(name=node_name)

            # Validate devices exists in the project
            if not node:
                utils.console.log(f"[b]({project.name})[/] Node not found: [i red]{node_name}")
                raise typer.Exit(1)

            # Update properties
            for label in node_spec.get("labels", []):
                if label not in node.labels:
                    node.labels.append(label)

            node.config_managed = node_spec.get("config_managed", node.config_managed)

            # TODO: Add support to detect changes in node.mgmt_addr assignments
            node.mgmt_port = node_spec.get("mgmt_port", node.mgmt_port)
            node.mgmt_addr = (
                f"{list(mgmt_network.iter_hosts())[index]}/{mgmt_network.prefixlen}"
                if node.mgmt_addr is None
                else node.mgmt_addr
            )
            index += 1

    # Refresh Nornir Inventory
    project.init_nornir()

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
    result = nr_filtered.run(task=save_task)
    utils.console.rule(title="Start section")
    print_result(result)
    utils.console.rule(title="End section")
