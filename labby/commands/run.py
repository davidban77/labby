from enum import Enum
from typing import Optional
import typer

from pathlib import Path
from labby.providers import get_provider
from labby import utils
from labby import config
from netaddr import IPNetwork
from nornir.core.helpers.jinja_helper import render_from_file


app = typer.Typer(help="Runs actions on Network Provider Lab Resources")
project_app = typer.Typer(help="Runs actions on a Network Provider Project")
node_app = typer.Typer(help="Runs actions on a Network Provider Node")

app.add_typer(project_app, name="project")
app.add_typer(node_app, name="node")


class DeviceTypes(str, Enum):
    cisco_ios = "cisco_ios"
    cisco_xr = "cisco_xr"
    cisco_nxos = "cisco_nxos"
    arista_eos = "arista_eos"
    juniper_junos = "juniper_junos"


def file_check(value: Path):
    if not value.exists():
        utils.console.log("The config doesn't exist", style="error")
        raise typer.Exit(code=1)
    elif not value.is_file():
        utils.console.log("No config file", style="error")
        raise typer.Exit(code=1)
    return value


def ipaddr(value: str, action: str = "address") -> str:
    to_render = ""
    if action == "address":
        to_render = str(IPNetwork(addr=value).ip)
    elif action == "netmask":
        to_render = str(IPNetwork(addr=value).netmask)
    return to_render


@project_app.command(short_help="Launches a project on a browser")
def launch(project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT")):
    """
    Launches a Project on a browser.

    Example:

    > labby run project-launch --project lab01
    """
    provider = get_provider(
        provider_name=config.SETTINGS.environment.provider.name, provider_settings=config.SETTINGS.environment.provider
    )
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    typer.launch(project.get_web_url())


@node_app.command(short_help="Initial bootsrtap config on a Node")
def bootstrap(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
    boot_delay: int = typer.Option(5, help="Time in seconds to wait on device boot if it has not been started"),
    bconfig: Optional[Path] = typer.Option(None, "--config", "-c", help="Bootstrap configuration file."),
    mgmt_port: Optional[str] = typer.Option(None, help="Management Interface to configure on the device"),
    mgmt_addr: Optional[str] = typer.Option(None, help="IP Prefix to configure on mgmt_port. i.e. 192.168.77.77/24"),
    user: Optional[str] = typer.Option(None, help="Initial user to configure on the system."),
    password: Optional[str] = typer.Option(None, help="Initial password to configure on the system."),
):
    r"""
    Sets a bootstrap config on a Node.

    There are 2 modes to run a bootstrap sequence.

    - By passing the bootstrap configuration directly from a file:

    > labby run node bootstrap --project lab01 --config r1.txt --node r1

    - By using labby bootstrap templates

    > labby run node bootstrap --mgmt_port Management1 --mgmt_addr 192.168.77.77/24 --user netops --password netops123
    --project lab01 --node r1
    """
    # Get network lab provider
    provider = get_provider(
        provider_name=config.SETTINGS.environment.provider.name, provider_settings=config.SETTINGS.environment.provider
    )

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
        # Check all other parameters are set
        if any(param is None for param in [mgmt_addr, mgmt_port, user, password]):
            utils.console.log("All arguments must be set: mgmt_addr, mgmt_port, user, password", style="error")
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
            jinja_filters={"ipaddr": ipaddr},
            **dict(mgmt_port=mgmt_port, mgmt_addr=mgmt_addr, user=user, password=password, node_name=node_name),
        )
        utils.console.log(f"[b]({project.name})({node.name})[/] Bootstrap config rendered", style="good")

    # Run node bootstrap config process
    node.bootstrap(config=cfg_data, boot_delay=boot_delay)
