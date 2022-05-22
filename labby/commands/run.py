"""Labby run command.

Handles all ad-hoc actions for labby resources.

Example:
> labby run --help
"""
from enum import Enum
from typing import Any, Dict, Optional
from pathlib import Path

import typer
from nornir.core.helpers.jinja_helper import render_from_file
from nornir_utils.plugins.functions import print_result

from labby.commands.build import config_task
from labby.project_data import sync_project_data
from labby.nornir_tasks import save_task
from labby import utils, config


app = typer.Typer(help="Runs actions on Network Provider Lab Resources")
project_app = typer.Typer(help="Runs actions on a Network Provider Project")
node_app = typer.Typer(help="Runs actions on a Network Provider Node")

app.add_typer(project_app, name="project")
app.add_typer(node_app, name="node")


class DeviceTypes(str, Enum):
    """Device Types Enum."""

    # pylint: disable=invalid-name
    cisco_ios = "cisco_ios"
    cisco_xr = "cisco_xr"
    cisco_nxos = "cisco_nxos"
    arista_eos = "arista_eos"
    juniper_junos = "juniper_junos"


def file_check(value: Path) -> Path:
    """Check file is valid.

    Args:
        value (Path): Path of the file to check.

    Raises:
        typer.Exit: The file does not exists
        typer.Exit: Is not a valid file

    Returns:
        Path: File path
    """
    if not value.exists():
        utils.console.log(f"The file {value} doesn't exist", style="error")
        raise typer.Exit(code=1)
    if not value.is_file():
        utils.console.log(f"{value} is not a valid file", style="error")
        raise typer.Exit(code=1)
    return value


@project_app.command(short_help="Launches a project on a browser")
def launch(project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT")):
    """
    Launches a Project on a browser.

    Example:
    > labby run project-launch --project lab01
    """
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Launch project on browser
    typer.launch(prj.get_web_url())


@node_app.command(short_help="Initial bootsrtap config on a Node")
def bootstrap(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    boot_delay: int = typer.Option(5, help="Time in seconds to wait on device boot if it has not been started"),
    bconfig: Optional[Path] = typer.Option(None, "--config", "-c", help="Bootstrap configuration file."),
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Initial user to configure on the system.", envvar="LABBY_NODE_USER"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-w", help="Initial password to configure on the system.", envvar="LABBY_NODE_PASSWORD"
    ),
    delay_multiplier: int = typer.Option(
        1, help="Delay multiplier to apply to boot/config delay before timeouts. Applicable over console connection."
    ),
):
    r"""
    Sets a bootstrap config on a Node.

    There are 2 modes to run a bootstrap sequence.

    - By passing the bootstrap configuration directly from a file:

    > labby run node bootstrap --project lab01 --config r1.txt r1

    - By using labby bootstrap templates

    > labby run node bootstrap -p lab01 --user netops --password netops123 r1
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Get node to bootstrap
    device = prj.search_node(node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Render bootstrap config
    if bconfig:
        utils.console.log(f"[b]({prj.name})({device.name})[/] Reading bootstrap config from file")
        file_check(bconfig)
        cfg_data = bconfig.read_text()

    else:
        utils.console.log(f"[b]({prj.name})({device.name})[/] Rendering bootstrap config")
        mgmt_port = device.mgmt_port
        if mgmt_port is None:
            utils.console.log(
                f"Node [cyan i]{node_name}[/] mgmt_port parameter must be set. Run update command", style="error"
            )
            raise typer.Exit(code=1)
        mgmt_addr = device.mgmt_addr
        if mgmt_addr is None:
            utils.console.log(
                f"Node [cyan i]{node_name}[/] mgmt_addr parameter must be set. Run update command", style="error"
            )
            raise typer.Exit(code=1)
        # Check all other parameters are set
        if any(param is None for param in [user, password]):
            utils.console.log("All arguments must be set: user, password", style="error")
            raise typer.Exit(code=1)

        if device.net_os is None:
            utils.console.log(
                f"Node [cyan i]{node_name}[/] net_os parameter must be set. Verify node template name", style="error"
            )
            raise typer.Exit(code=1)

        # Render bootstrap config
        template = Path(__file__).parent.parent / "templates" / f"nodes_bootstrap/{device.net_os}.cfg.j2"
        cfg_data = render_from_file(
            path=str(template.parent),
            template=template.name,
            jinja_filters={"ipaddr": utils.ipaddr_renderer},
            **dict(mgmt_port=mgmt_port, mgmt_addr=mgmt_addr, user=user, password=password, node_name=node_name),
        )
        utils.console.log(f"[b]({prj.name})({device.name})[/] Bootstrap config rendered", style="good")

    # Run node bootstrap config process
    device.bootstrap(config=cfg_data, boot_delay=boot_delay, delay_multiplier=delay_multiplier)


@node_app.command(name="config", short_help="Configures a Node.")
def node_config(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    config_template: Path = typer.Option(..., "--template", "-t", help="Config template file"),
    vars_file: Path = typer.Option(..., "--vars", "-v", help="Variables YAML file. For example: vars.yml"),
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="User to use for the node connection", envvar="LABBY_NODE_USER"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-w", help="Password to use for the node connection", envvar="LABBY_NODE_PASSWORD"
    ),
    console: bool = typer.Option(False, "--console", "-c", help="Apply configuration over console"),
    delay_multiplier: int = typer.Option(
        1, help="Delay multiplier to apply to boot/config delay before timeouts. Applicable over console connection."
    ),
):
    """
    Configures a Node.

    By default, the configuration is applied over the node mgmt_port. If you want to retrieve the configuration over
    console, you can use the `--console` option.

    Example:

    > labby run node config r1 -p lab01 --user netops --template bgp.conf.j2 --vars r1.yml --console
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Get node to configure
    device = prj.search_node(node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Check all other parameters are set
    if device.net_os is None:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] net_os parameter must be set. Verify node template name", style="error"
        )
        raise typer.Exit(code=1)

    if device.mgmt_port is None:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] mgmt_port parameter must be set. Run update command", style="error"
        )
        raise typer.Exit(code=1)
    if device.mgmt_addr is None:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] mgmt_addr parameter must be set. Run update command", style="error"
        )
        raise typer.Exit(code=1)

    if any(param is None for param in [user, password]):
        utils.console.log("All arguments must be set: user, password", style="error")
        raise typer.Exit(code=1)

    # Render config
    config_template_vars: Dict[str, Any] = utils.load_yaml_file(str(vars_file))
    cfg_data = render_from_file(
        path=str(config_template.parent),
        template=config_template.name,
        jinja_filters={"ipaddr": utils.ipaddr_renderer},
        **config_template_vars,
    )
    utils.console.log(f"[b]({prj.name})({device.name})[/] Node config rendered", style="good")

    # Apply node configuration
    if console:
        applied = device.apply_config_over_console(
            config=cfg_data, user=user, password=password, delay_multiplier=delay_multiplier
        )
    else:
        applied = device.apply_config(config=cfg_data, user=user, password=password)
    if applied:
        utils.console.log(f"[b]({prj.name})({device.name})[/] Node config applied", style="good")
    else:
        utils.console.log(f"[b]({prj.name})({device.name})[/] Node config not applied", style="error")


@project_app.command(name="nodes-save", short_help="Save Nodes Configuration from a project file.")
def project_save(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter devices based on the model provided"),
    net_os: Optional[str] = typer.Option(None, "--net-os", "-n", help="Filter devices based on the net_os provided"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter devices based on the name"),
    backup: Optional[Path] = typer.Option(None, "--backup", "-b", help="Backup directory location"),
    silent: bool = typer.Option(False, "--silent", "-s", help="Silent mode", envvar="LABBY_SILENT"),
):
    """
    Saves nodes configuration.

    Example:

    > labby run project nodes-save --project-file "myproject.yml" --backup /path/to/backup/folder
    """
    project, _ = sync_project_data(project_file)

    # Check backup directory
    if backup:
        if not backup.exists():
            backup.mkdir(parents=True)

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
    result = nr_filtered.run(task=save_task, backup=backup)
    if not silent:
        utils.console.rule(title="Start section")
        print_result(result)  # type: ignore
        utils.console.rule(title="End section")
    utils.console.log(
        f"[b]({project.name})[/] Devices config saved: [i dark_orange3]{list(nr_filtered.inventory.hosts.keys())}[/]"
    )


@project_app.command(name="node-configs", short_help="Configures Nodes from a project file.")
def project_config(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter devices based on the model provided"),
    net_os: Optional[str] = typer.Option(None, "--net-os", "-n", help="Filter devices based on the net_os provided"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Filter devices based on the name"),
):
    """
    Builds and applies configuration to the nodes specified on the project file.

    Example:

    > labby run project node-configs --project-file "myproject.yml" --backup /path/to/backup/folder
    """
    project, project_data = sync_project_data(project_file)

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
    utils.console.rule(title="Start section")
    print_result(result)  # type: ignore
    utils.console.rule(title="End section")
