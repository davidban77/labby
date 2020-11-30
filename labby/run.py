import typer
from enum import Enum
from pathlib import Path
from labby.providers import provider_setup
from labby import utils
from labby.models import Project, Node
from labby import settings
from labby import nornir_module


app = typer.Typer(help="Runs Labs provisioning tasks with Nornir")


class DeviceTypes(str, Enum):
    cisco_iosxe = "cisco_iosxe"
    cisco_iosxr = "cisco_iosxr"
    cisco_nxos = "cisco_nxos"
    arista_eos = "arista_eos"
    juniper_junos = "juniper_junos"


def config_callback(value: Path):
    if not value.exists():
        utils.console.print("The config doesn't exist")
        raise typer.Exit(code=1)
    elif not value.is_file():
        utils.console.print("No config file")
        raise typer.Exit(code=1)
    return value


def project_callback(value: Path):
    if not value.is_dir():
        utils.console.print("The project folder doesn't exist")
        raise typer.Exit(code=1)
    return value


@app.command(short_help="Build a project from scratch using Nornir")
def build(
    ctx: typer.Context,
    project: str = typer.Option(
        ...,
        "--project",
        "-p",
        help="Project the node belongs to",
        envvar="LABBY_PROJECT",
    ),
    project_path: Path = typer.Option(
        Path.cwd(),
        "--project-path",
        "-p",
        help="Nornir project directory",
        callback=project_callback
    ),
):
    """
    It builds a project from scratch using the provider and Nornir.

    > labby run build --project-path example_project/
    """
    try:
        project_file = list(project_path.glob(f"{project}.toml"))
        if project_file:
            # Re-apply the settings with the project file
            settings.load(config_file=ctx.obj, project_file=project_file[0])
        nornir_module.build(project)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Bootstrap provision process")
def bootstrap(
    node: str = typer.Argument(..., help="Node to start bootstrap process"),
    project: str = typer.Option(
        ...,
        "--project",
        "-p",
        help="Project the node belongs to",
        envvar="LABBY_PROJECT",
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

    > labby run bootstrap node01 --project project01 --config ./node01_boot.txt
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
