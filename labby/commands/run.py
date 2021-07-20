"""Labby run command.

Handles all ad-hoc actions for labby resources.

Example:
> labby run --help
"""
import os
from netaddr.ip import IPNetwork
import typer
from enum import Enum
from typing import Any, Dict, Optional

from pathlib import Path
from labby import utils, config
from nornir.core.helpers.jinja_helper import render_from_file


app = typer.Typer(help="Runs actions on Network Provider Lab Resources")
project_app = typer.Typer(help="Runs actions on a Network Provider Project")
node_app = typer.Typer(help="Runs actions on a Network Provider Node")

app.add_typer(project_app, name="project")
app.add_typer(node_app, name="node")


class DeviceTypes(str, Enum):  # noqa: D101
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
    elif not value.is_file():
        utils.console.log(f"{value} is not a valid file", style="error")
        raise typer.Exit(code=1)
    return value


@project_app.command(short_help="Launches a project on a browser")
def launch(project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT")):
    """
    Launches a Project on a browser.

    Example:
    > labby run project-launch --project lab01
    """
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Launch project on browser
    typer.launch(project.get_web_url())


@node_app.command(short_help="Initial bootsrtap config on a Node")
def bootstrap(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
    boot_delay: int = typer.Option(5, help="Time in seconds to wait on device boot if it has not been started"),
    bconfig: Optional[Path] = typer.Option(None, "--config", "-c", help="Bootstrap configuration file."),
    user: Optional[str] = typer.Option(None, help="Initial user to configure on the system."),
    password: Optional[str] = typer.Option(None, help="Initial password to configure on the system."),
):
    r"""
    Sets a bootstrap config on a Node.

    There are 2 modes to run a bootstrap sequence.

    - By passing the bootstrap configuration directly from a file:

    > labby run node bootstrap --project lab01 --config r1.txt --node r1

    - By using labby bootstrap templates

    > labby run node bootstrap --user netops --password netops123 --project lab01 --node r1
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Get node to bootstrap
    node = project.search_node(node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Render bootstrap config
    if bconfig:
        utils.console.log(f"[b]({project.name})({node.name})[/] Reading bootstrap config from file")
        file_check(bconfig)
        cfg_data = bconfig.read_text()

    else:
        utils.console.log(f"[b]({project.name})({node.name})[/] Rendering bootstrap config")
        mgmt_port = node.mgmt_port
        if mgmt_port is None:
            utils.console.log(
                f"Node [cyan i]{node_name}[/] mgmt_port parameter must be set. Run update command", style="error"
            )
            raise typer.Exit(code=1)
        mgmt_addr = node.mgmt_addr
        if mgmt_addr is None:
            utils.console.log(
                f"Node [cyan i]{node_name}[/] mgmt_addr parameter must be set. Run update command", style="error"
            )
            raise typer.Exit(code=1)
        # Check all other parameters are set
        if any(param is None for param in [user, password]):
            utils.console.log("All arguments must be set: user, password", style="error")
            raise typer.Exit(code=1)

        if node.net_os is None:
            utils.console.log(
                f"Node [cyan i]{node_name}[/] net_os parameter must be set. Verify node template name", style="error"
            )
            raise typer.Exit(code=1)

        # Render bootstrap config
        template = Path(__file__).parent.parent / "templates" / f"nodes_bootstrap/{node.net_os}.cfg.j2"
        cfg_data = render_from_file(
            path=str(template.parent),
            template=template.name,
            jinja_filters={"ipaddr": utils.ipaddr_renderer},
            **dict(mgmt_port=mgmt_port, mgmt_addr=mgmt_addr, user=user, password=password, node_name=node_name),
        )
        utils.console.log(f"[b]({project.name})({node.name})[/] Bootstrap config rendered", style="good")

    # Run node bootstrap config process
    node.bootstrap(config=cfg_data, boot_delay=boot_delay)


@node_app.command(name="config", short_help="Configures a Node.")
def node_config(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
    config_template: Path = typer.Option(..., "--template", "-t", help="Config template file"),
    vars_file: Path = typer.Option(..., "--vars", "-v", help="Variables YAML file. For example: vars.yml"),
    user: str = typer.Option(None, help="Node user"),
    password: str = typer.Option(None, help="Node password"),
    console: bool = typer.Option(False, "--console", "-c", help="Apply configuration over console"),
):
    """
    Configures a Node.

    > labby run node config -p lab01 -n r1 --user netops --password netops123 -t bgp.conf.j2 -v r1.yml
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Get node to configure
    node = project.search_node(node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Check all other parameters are set
    if node.net_os is None:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] net_os parameter must be set. Verify node template name", style="error"
        )
        raise typer.Exit(code=1)

    if node.mgmt_port is None:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] mgmt_port parameter must be set. Run update command", style="error"
        )
        raise typer.Exit(code=1)
    if node.mgmt_addr is None:
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
    utils.console.log(f"[b]({project.name})({node.name})[/] Node config rendered", style="good")

    # Apply node configuration
    if console:
        applied = node.apply_config_over_console(config=cfg_data, user=user, password=password)
    else:
        applied = node.apply_config(config=cfg_data, user=user, password=password)
    if applied:
        utils.console.log(f"[b]({project.name})({node.name})[/] Node config applied", style="good")
    else:
        utils.console.log(f"[b]({project.name})({node.name})[/] Node config not applied", style="error")


@node_app.command(name="connect", short_help="Connects to a node.")
def node_connect(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
    user: str = typer.Option(None, help="Node user"),
    # password: str = typer.Option(None, help="Node password"),
    console: bool = typer.Option(False, "--console", "-c", help="Apply configuration over console"),
):
    """
    Connects to a Node bia SSH (default and if applicable) or Telnet console.

    For console connection to work, you must have a Telnet client installed.

    Example:

    > labby run node connect -p lab01 -n r1 --user netops --password netops123
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Get node to connect
    node = project.search_node(node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    if node.mgmt_addr is None and console is False:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] mgmt_addr parameter must be set. Run update command", style="error"
        )
        raise typer.Exit(code=1)

    if any(param is None for param in [user]):
        utils.console.log("All arguments must be set: user", style="error")
        raise typer.Exit(code=1)

    # Connect to node
    if console:
        server_host = utils.dissect_url(node._base._connector.base_url)[1]  # type: ignore
        os.system(f"telnet {server_host} {node.console}")
    else:
        os.system(f"ssh {user}@{IPNetwork(node.mgmt_addr).ip}")
