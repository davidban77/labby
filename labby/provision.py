import typer
from enum import Enum
from pathlib import Path
from labby.providers import provider_setup
from labby import utils
from labby.models import Project, Node


app = typer.Typer(help="Management of Lab Config Provision")


class DeviceTypes(str, Enum):
    cisco_iosxe = "cisco_iosxe"
    cisco_iosxr = "cisco_iosxr"
    cisco_nxos = "cisco_nxos"
    arista_eos = "arista_eos"
    juniper_junos = "juniper_junos"


def config_callback(value: Path):
    if not value.exists():
        utils.console.print("The config doesn't exists")
        raise typer.Exit(code=1)
    elif not value.is_file():
        utils.console.print("No config file")
        raise typer.Exit(code=1)
    return value


@app.command(short_help="Bootstrap provision process")
def bootstrap(
    node: str = typer.Argument(..., help="Node to start bootstrap process"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the node belongs to"
    ),
    bconfig: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Bootstrap configuration file",
        callback=config_callback,
    ),
    device_type: DeviceTypes = typer.Option(
        ..., "--type", "-t", help="The device type to execute the correct process"
    ),
):
    """
    It runs a bootstrap process for a given node on a given project.

    > labby provision bootstrap node01 --project project01 --config ./node01_boot.txt
    --type arista_eos
    """
    try:
        provider = provider_setup(
            f"Running boostrap config process for [bold]{node}[/]"
        )
        prj = Project(name=project)
        nd = Node(name=node, project=project)
        provider.bootstrap_node(
            node=nd, project=prj, config=bconfig, device_type=device_type
        )
    except Exception:
        utils.console.print_exception()
