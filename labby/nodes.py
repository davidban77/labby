import typer
import labby.utils as utils
from enum import Enum
from typing import Optional
from labby.providers import provider_setup
from labby.models import Project, Node


app = typer.Typer(help="Management of Lab Nodes for a Project")


class ProjectFilter(str, Enum):
    node_type = "node_type"
    category = "category"
    status = "status"
    # template = "template"


@app.command(name="list", short_help="Retrieves a list of nodes from a project")
def cli_list(
    project: str = typer.Option(
        ..., "--project", "-p", help="Project to collect nodes information"
    ),
    field: Optional[ProjectFilter] = typer.Option(
        None, "--filter", "-f", help="If used you MUST provide expected `--value`"
    ),
    value: Optional[str] = typer.Option(
        None,
        help="Value to be used with `--filter`",
    ),
):
    """
    Retrieve a summary list of nodes for a given project.

    For example:

    > labby node list project01 --filter status --value started
    """
    try:
        provider = provider_setup(f"Nodes list for project: [bold]{project}[/]")
        prj = Project(name=project)
        provider.get_nodes_list(project=prj, field=field, value=value)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Retrieves details of a node")
def detail(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
):
    """
    Retrieves Node details

    > labby node detail node-1 --project project01
    """
    try:
        provider = provider_setup(
            f"Node details for [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project)
        provider.get_node_details(node=node, project=prj)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Creates a node")
def create(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
    template: str = typer.Option(
        ..., "--template", "-t", help="Base template to derive new node"
    ),
):
    """
    Creates a Node

    > labby node create router01 --project project01 --template IOSv
    """
    try:
        provider = provider_setup(
            f"Create node [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project, template=template)
        provider.create_node(node=node, project=prj)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Deletes a node")
def delete(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
):
    """
    Deletes a Node

    > labby node delete router01 --project project01
    """
    try:
        provider = provider_setup(
            f"Delete node [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project)
        provider.delete_node(node=node, project=prj)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Starts a node")
def start(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
):
    """
    Starts a Node

    > labby node start router01 --project project01
    """
    try:
        provider = provider_setup(
            f"Start node [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project)
        provider.start_node(node=node, project=prj)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Stops a node")
def stop(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
):
    """
    Stops a Node

    > labby node stop router01 --project project01
    """
    try:
        provider = provider_setup(
            f"Start node [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project)
        provider.stop_node(node=node, project=prj)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Suspends a node")
def suspend(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
):
    """
    Suspend a Node

    > labby node suspend router01 --project project01
    """
    try:
        provider = provider_setup(
            f"Suspends node [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project)
        provider.suspend_node(node=node, project=prj)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Reloads a node")
def reload(
    name: str = typer.Argument(..., help="Name of node"),
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the Node belongs"
    ),
):
    """
    Reloads a Node

    > labby node reload router01 --project project01
    """
    try:
        provider = provider_setup(
            f"Reload node [bold]{name}[/] on project [bold]{project}[/]"
        )
        prj = Project(name=project)
        node = Node(name=name, project=project)
        provider.reload_node(node=node, project=prj)
    except Exception:
        utils.console.print_exception()
