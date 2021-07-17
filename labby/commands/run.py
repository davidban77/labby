"""Labby run command.

Handles all ad-hoc actions for labby resources.

Example:
> labby run --help
"""
import typer
from enum import Enum
from typing import Optional, Literal

from pathlib import Path
# from labby.providers import get_config_provider
from labby import utils, config
from netaddr import IPNetwork
from nornir.core.helpers.jinja_helper import render_from_file


IpAddressFilter = Literal["address", "netmask"]


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


def ipaddr_renderer(value: str, *, render: IpAddressFilter) -> str:
    """Renders an IP address related values.

    Args:
        value (str): IP address/prefix to render the information from.
        action (str, optional): Action to determine method to render. Defaults to "address".

    Returns:
        str: address value
    """
    to_render = ""
    if render == "address":
        to_render = str(IPNetwork(addr=value).ip)
    elif render == "netmask":
        to_render = str(IPNetwork(addr=value).netmask)
    else:
        raise ValueError()
    return to_render


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
            jinja_filters={"ipaddr": ipaddr_renderer},
            **dict(mgmt_port=mgmt_port, mgmt_addr=mgmt_addr, user=user, password=password, node_name=node_name),
        )
        utils.console.log(f"[b]({project.name})({node.name})[/] Bootstrap config rendered", style="good")

    # Run node bootstrap config process
    node.bootstrap(config=cfg_data, boot_delay=boot_delay)
