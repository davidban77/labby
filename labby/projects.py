import typer

from enum import Enum
from typing import Optional
from labby.models import Project
from labby import utils
from labby.providers import provider_setup


app = typer.Typer(help="Management of Lab Projects")


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
    try:
        provider = provider_setup("Project lists")
        utils.console.print(
            provider.reporter.table_projects_list(field=filter, value=value),
            justify="center",
        )
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Retrieves details of a project")
def detail(
    name: str = typer.Argument(
        ..., help="Project to get details from", envvar="LABBY_PROJECT"
    )
):
    """
    Retrieves Project details

    For example:

    > labby project detail project01
    """
    try:
        provider = provider_setup(f"Project Details: {name}")
        project = Project(name=name)
        provider.get_project_details(project)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Creates a Project")
def create(
    name: str = typer.Argument(..., help="Project to create", envvar="LABBY_PROJECT")
):
    """
    Creates a Project

    For example:

    > labby project create project01
    """
    try:
        provider = provider_setup(f"Creating Project: {name}")
        project = Project(name=name)
        provider.create_project(project)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Deletes a project")
def delete(
    name: str = typer.Argument(..., help="Project to delete", envvar="LABBY_PROJECT")
):
    """
    Deletes a Project

    For example:

    > labby project delete project01
    """
    try:
        provider = provider_setup(f"Deleting Project: {name}")
        project = Project(name=name)
        provider.delete_project(project)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Starts a project")
def start(
    name: str = typer.Argument(..., help="Project to start", envvar="LABBY_PROJECT"),
    start_nodes: StartNodes = typer.Option(
        "none", help="Strategy to use to start nodes in project"
    ),
    delay: int = typer.Option(10, help="Time to wait starting nodes"),
):
    """
    Starts a Project and gives a sequence to start the nodes

    For example:

    > labby project start project01 --start-nodes one_by_one --delay 20
    """
    try:
        provider = provider_setup(f"Starting Project: {name}")
        project = Project(name=name)
        provider.start_project(
            project=project, start_nodes=start_nodes, nodes_delay=delay
        )
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Stops a project")
def stop(
    name: str = typer.Argument(..., help="Project to start", envvar="LABBY_PROJECT"),
    stop_nodes: bool = typer.Option(
        False, help="Strategy to use to start nodes in project"
    ),
):
    """
    Stops a Project

    For example:

    > labby project stop project01
    """
    try:
        provider = provider_setup(f"Stopping Project: {name}")
        project = Project(name=name)
        provider.stop_project(project=project, stop_nodes=stop_nodes)
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Launches a Project")
def launch(
    name: str = typer.Argument(..., help="Project to start", envvar="LABBY_PROJECT"),
):
    """
    Launches a Project on a browser

    For example:

    > labby project launch project01
    """
    try:
        provider = provider_setup(f"Launching Project: {name}")
        project = Project(name=name)
        typer.launch(provider.get_project_web_url(project))
    except Exception:
        utils.console.print_exception()
