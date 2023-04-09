"""Labby restart command.

Handles all restart/reload actions for labby resources.

Example:
> labby restart --help
"""
import typer

from labby.commands.common import get_labby_objs_from_node
from labby import utils


app = typer.Typer(
    help="[b orange1]Run restart[/b orange1] actions on a [i]resource[/i] from a [link=https://github.com/davidban77/labby/blob/develop/README.md#42-environments-and-providers]Network Provider Lab[/link]"
)


@app.command(short_help="[b i]Restarts[/b i] a node")
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
