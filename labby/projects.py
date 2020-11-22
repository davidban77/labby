import typer
import labby.utils as utils
from enum import Enum
from typing import Optional
from rich.console import Console
from labby.providers import services
from labby.models import Project


console = Console(color_system="auto")
app = typer.Typer(help="Management of Lab Projects")
config = {"gns3_server_url": "http://gns3-server:80"}
provider = services.get("GNS3", **config)


class ProjectFilter(str, Enum):
    status = "status"
    auto_start = "auto_start"
    auto_open = "auto_open"
    auto_close = "auto_close"


class StartNodes(str, Enum):
    none = "none"
    one_by_one = "one_by_one"
    all = "all"


@app.command(name="list", short_help="Retrieves summary list of projects")
def cli_list(
    ctx: typer.Context,
    filter: Optional[ProjectFilter] = typer.Option(
        None, help="If used you MUST provide expected `--value`"
    ),
    value: Optional[str] = typer.Option(
        None,
        help="Value to be used with `--filter`",
    ),
):
    """
    Retrieve a summary list of projects configured on server.

    For example:

    > labby project list --filter status --value opened
    """
    utils.header("Project lists")
    console.print(
        provider.reporter.table_projects_list(field=filter, value=value),
        justify="center",
    )


@app.command(short_help="Retrieves details of a project")
def detail(name: str):
    """
    Retrieves Project details

    For example:

    > labby project detail project01
    """
    utils.header(f"Project Details: {name}")
    project = Project(name=name)
    provider.get_project_details(project)


@app.command(short_help="Creates a Project")
def create(name: str):
    """
    Creates a Project

    For example:

    > labby project create project01
    """
    utils.header(f"Creating Project: {name}")
    project = Project(name=name)
    provider.create_project(project)


@app.command(short_help="Deletes a project")
def delete(name: str):
    """
    Deletes a Project

    For example:

    > labby project delete project01
    """
    utils.header(f"Deleting Project: {name}")
    project = Project(name=name)
    provider.delete_project(project)


@app.command(short_help="Starts a project")
def start(
    name: str = typer.Argument(..., help="Project to start"),
    start_nodes: StartNodes = typer.Option(
        "none", help="Strategy to use to start nodes in project"
    ),
    nodes_delay: int = typer.Option(10, help="Time to wait starting nodes"),
):
    """
    Starts a Project and gives a sequence to start the nodes

    For example:

    > labby project start project01 --start_nodes one_by_one --nodes_delay 20
    """
    utils.header(f"Starting Project: {name}")
    project = Project(name=name)
    provider.start_project(
        project=project, start_nodes=start_nodes, nodes_delay=nodes_delay
    )


@app.command(short_help="Stops a project")
def stop(
    name: str = typer.Argument(..., help="Project to start"),
    stop_nodes: bool = typer.Option(
        False, help="Strategy to use to start nodes in project"
    ),
):
    """
    Stops a Project

    For example:

    > labby project stop project01
    """
    utils.header(f"Stopping Project: {name}")
    project = Project(name=name)
    provider.stop_project(
        project=project, stop_nodes=stop_nodes
    )


if __name__ == "__main__":
    app()
