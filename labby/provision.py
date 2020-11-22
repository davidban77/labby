import typer
import labby.utils as utils
from enum import Enum
from pathlib import Path
from rich.console import Console
from labby.providers import services
from labby.models import Project, Node


console = Console(color_system="auto")
app = typer.Typer(help="Management of Lab Config Provision")
config = {"gns3_server_url": "http://gns3-server:80"}
provider = services.get("GNS3", **config)


class DeviceTypes(str, Enum):
    cisco_iosxe = "cisco_iosxe"
    cisco_iosxr = "cisco_iosxr"
    cisco_nxos = "cisco_nxos"
    arista_eos = "arista_eos"
    juniper_junos = "juniper_junos"


def config_callback(value: Path):
    if not value.exists():
        console.print("The config doesn't exists")
        raise typer.Abort()
    elif not value.is_file():
        console.print("No config file")
        raise typer.Abort()
    return value


@app.command(short_help="Bootstrap provision process")
def bootstrap(
    node: str = typer.Argument(..., help="Node to start bootstrap process"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the node belongs to"
    ),
    config: Path = typer.Option(
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
    # if not config.exists():
    #     console.print("The config doesn't exists")
    #     raise typer.Abort()
    # elif not config.is_file():
    #     console.print("No config file")
    #     raise typer.Abort()
    utils.header(f"Running boostrap config process for [bold]{node}[/]")
    prj = Project(name=project)
    nd = Node(name=node, project=project)
    provider.bootstrap_node(
        node=nd, project=prj, config=config, device_type=device_type
    )


if __name__ == "__main__":
    app()
