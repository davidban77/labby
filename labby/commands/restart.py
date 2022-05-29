"""Labby restart command.

Handles all restart/reload actions for labby resources.

Example:
> labby restart --help
"""
import typer

from labby.commands.common import get_labby_objs_from_node
from labby import utils


app = typer.Typer(help="Runs Restart actions on Network Provider Lab Resources")


@app.command(short_help="Restarts a node")
def node(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
):
    """
    Restarts a Node.

    Example:

    > labby restart node r1 --project lab01
    """
    # Get Labby objects from project and node definition
    _, _, device = get_labby_objs_from_node(project_name=project_name, node_name=node_name)

    # Restart node
    device.restart()
    utils.console.log(device)
