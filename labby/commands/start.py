"""Labby start command.

Handles all start related actions for labby resources.

Example:
> labby start --help
"""
from enum import Enum
from typing import Optional

import typer

from labby.commands.common import get_labby_objs_from_node, get_labby_objs_from_project
from labby import utils


app = typer.Typer(help="Runs Start/Boot actions on Network Provider Lab Resources")


class StartNodes(str, Enum):
    """Start Nodes Enum."""

    # pylint: disable=invalid-name
    one_by_one = "one_by_one"
    all = "all"


@app.command(short_help="Starts a project")
def project(
    project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT"),
    start_nodes: Optional[StartNodes] = typer.Option(None, help="Strategy to use to start nodes in project"),
    delay: int = typer.Option(10, help="Time to wait starting nodes"),
):
    """
    Starts a Project and optionally you can start the nodes.

    Example:
    > labby start project lab01 --start-nodes one_by_one --delay 20
    """
    # Get Labby objects from project definition
    _, prj = get_labby_objs_from_project(project_name=project_name)

    # Start project
    prj.start(start_nodes=start_nodes, nodes_delay=delay)


@app.command(short_help="Starts a node")
def node(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
):
    """
    Starts a Node.

    Example:

    > labby start node r1 --project lab01
    """
    # Get Labby objects from project and node definition
    _, _, device = get_labby_objs_from_node(project_name=project_name, node_name=node_name)

    # Start node
    device.start()
    utils.console.log(device)
