"""Labby start command.

Handles all start related actions for labby resources.

Example:
> labby start --help
"""
from enum import Enum
from typing import Optional

import typer

from labby import utils
from labby import config


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
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

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
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    device = prj.search_node(name=node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Start node
    device.start()
    utils.console.log(device)
