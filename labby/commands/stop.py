"""Labby stop command.

Handles all stop related actions for labby resources.

Example:
> labby stop --help
"""
import typer

from labby.commands.common import get_labby_objs_from_node, get_labby_objs_from_project
from labby import utils


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
    # Get Labby objects from project definition
    _, prj = get_labby_objs_from_project(project_name=project_name)

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
    # Get Labby objects from project and node definition
    _, _, device = get_labby_objs_from_node(project_name=project_name, node_name=node_name)

    # Stop node
    device.stop()
    utils.console.log(device)
