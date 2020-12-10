import typer
import labby.utils as utils
from enum import Enum
from typing import Optional
from labby import settings
from labby.providers import provider_setup
from labby.models import Project, Node


app = typer.Typer(help="Management of Lab Nodes for a Project")


class ProjectFilter(str, Enum):
    node_type = "node_type"
    category = "category"
    status = "status"
    # template = "template"


@app.command(
    name="list", short_help="Retrieves a list of nodes from a project"
)  # type: ignore
@utils.error_catcher(parameter="check_project")
def cli_list(
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

    > labby --project lab01 node list --filter status --value started
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(f"Nodes list for project: [bold]{project}[/]")
    prj = Project(name=project)  # type: ignore
    provider.get_nodes_list(project=prj, field=field, value=value)


@app.command(short_help="Retrieves details of a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def detail(
    name: str = typer.Argument(..., help="Name of node"),
):
    """
    Retrieves Node details

    > labby --project lab01 node detail node-1
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Node details for [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project)  # type: ignore
    provider.get_node_details(node=node, project=prj)


@app.command(short_help="Creates a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def create(
    name: str = typer.Argument(..., help="Name of node"),
    template: str = typer.Option(
        ..., "--template", "-t", help="Base template to derive new node"
    ),
):
    """
    Creates a Node

    > labby --project lab01 node create router01 --template IOSv
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Create node [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project, template=template)  # type: ignore
    provider.create_node(node=node, project=prj)


@app.command(short_help="Deletes a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def delete(
    name: str = typer.Argument(..., help="Name of node"),
):
    """
    Deletes a Node

    > labby --project lab01 node delete router01
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Delete node [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project)  # type: ignore
    provider.delete_node(node=node, project=prj)


@app.command(short_help="Starts a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def start(
    name: str = typer.Argument(..., help="Name of node"),
):
    """
    Starts a Node

    > labby --project lab01 node start router01
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Start node [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project)  # type: ignore
    provider.start_node(node=node, project=prj)


@app.command(short_help="Stops a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def stop(
    name: str = typer.Argument(..., help="Name of node"),
):
    """
    Stops a Node

    > labby --project lab01 node stop router01
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Start node [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project)  # type: ignore
    provider.stop_node(node=node, project=prj)


@app.command(short_help="Suspends a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def suspend(
    name: str = typer.Argument(..., help="Name of node"),
):
    """
    Suspend a Node

    > labby --project lab01 node suspend router01
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Suspends node [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project)  # type: ignore
    provider.suspend_node(node=node, project=prj)


@app.command(short_help="Reloads a node")  # type: ignore
@utils.error_catcher(parameter="check_project")
def reload(
    name: str = typer.Argument(..., help="Name of node"),
):
    """
    Reloads a Node

    > labby --project lab01 node reload router01
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(
        f"Reload node [bold]{name}[/] on project [bold]{project}[/]"
    )
    prj = Project(name=project)  # type: ignore
    node = Node(name=name, project=project)  # type: ignore
    provider.reload_node(node=node, project=prj)
