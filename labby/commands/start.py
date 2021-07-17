"""Labby start command.

Handles all start related actions for labby resources.

Example:
> labby start --help
"""
import typer
from enum import Enum
from typing import Optional
from labby import utils
from labby import config


app = typer.Typer(help="Runs Start/Boot actions on Network Provider Lab Resources")


class StartNodes(str, Enum):  # noqa: D101
    one_by_one = "one_by_one"
    all = "all"


@app.command(short_help="Starts a project")
def project(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    start_nodes: Optional[StartNodes] = typer.Option(None, help="Strategy to use to start nodes in project"),
    delay: int = typer.Option(10, help="Time to wait starting nodes"),
):
    """
    Starts a Project and optionally you can start the nodes.

    Example:
    > labby start project --project lab01 --start-nodes one_by_one --delay 20
    """
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Start project
    project.start(start_nodes=start_nodes, nodes_delay=delay)


@app.command(short_help="Starts a node")
def node(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
):
    """
    Starts a Node.

    Example:
    > labby start node --project lab01 --node r1
    """
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    node = project.search_node(name=node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Start node
    node.start()
    utils.console.log(node)
