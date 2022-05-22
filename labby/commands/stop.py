"""Labby stop command.

Handles all stop related actions for labby resources.

Example:
> labby stop --help
"""
import typer

from labby import utils
from labby import config


app = typer.Typer(help="Runs Stop/Halt actions on Network Provider Lab Resources")


@app.command(short_help="Stops a project")
def project(
    project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT"),
    stop_nodes: bool = typer.Option(True, help="Strategy to use to start nodes in project"),
):
    """
    Stops a Project and optionally stops the nodes preemptively.

    Example:

    > labby stop project lab01
    """
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Stop project
    prj.stop(stop_nodes=stop_nodes)


@app.command(short_help="Stops a node")
def node(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
):
    """
    Stops a Node.

    Example:

    > labby stop node r1 --project lab01
    """
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    device = prj.search_node(name=node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Stop node
    device.stop()
    utils.console.log(device)
