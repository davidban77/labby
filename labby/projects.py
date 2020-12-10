import typer

from enum import Enum
from typing import Optional
from labby.models import Project
from labby import settings, utils
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
@utils.error_catcher
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
    provider = provider_setup("Project lists")
    utils.console.print(
        provider.reporter.table_projects_list(field=filter, value=value),
        justify="center",
    )


@app.command(short_help="Retrieves details of a project")            # type: ignore
@utils.error_catcher(parameter="check_project")
def detail():
    """
    Retrieves Project details. A project can be referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby --project lab01 project detail
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Project Details: {name}")
    project = Project(name=name)                                     # type: ignore
    provider.get_project_details(project)


@app.command(short_help="Creates a project")                         # type: ignore
@utils.error_catcher(parameter="check_project")
def create():
    """
    Creates a Project. A project can be referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby project create project01
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Creating Project: {name}")
    project = Project(name=name)                                     # type: ignore
    provider.create_project(project)


@app.command(short_help="Updates a project")                         # type: ignore
@utils.error_catcher(parameter="check_project")
def update(
    parameter: str = typer.Argument(..., help="Parameter to set"),
    value: str = typer.Argument(..., help="Value to be set"),
):
    """
    Updates a Project instance based on a parameter and its value. A project can be
    referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby -p lab01 project update name lab02
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Updatings Project: {name}")
    project = Project(name=name)                                     # type: ignore
    provider.update_project(project, parameter=parameter, value=value)


@app.command(short_help="Deletes a project")                         # type: ignore
@utils.error_catcher(parameter="check_project")
def delete():
    """
    Deletes a Project. A project can be referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby project delete project01
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Deleting Project: {name}")
    project = Project(name=name)                                     # type: ignore
    provider.delete_project(project)


@app.command(short_help="Starts a project")                          # type: ignore
@utils.error_catcher(parameter="check_project")
def start(
    start_nodes: StartNodes = typer.Option(
        "none", help="Strategy to use to start nodes in project"
    ),
    delay: int = typer.Option(10, help="Time to wait starting nodes"),
):
    """
    Starts a Project and gives a sequence to start the nodes. A project can be
    referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby -p project01 project start --start-nodes one_by_one --delay 20
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Starting Project: {name}")
    project = Project(name=name)                                     # type: ignore
    provider.start_project(
        project=project, start_nodes=start_nodes, nodes_delay=delay
    )


@app.command(short_help="Stops a project")                           # type: ignore
@utils.error_catcher(parameter="check_project")
def stop(
    stop_nodes: bool = typer.Option(
        False, help="Strategy to use to start nodes in project"
    ),
):
    """
    Stops a Project. A project can be referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby project stop project01
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Stopping Project: {name}")
    project = Project(name=name)                                     # type: ignore
    provider.stop_project(project=project, stop_nodes=stop_nodes)


@app.command(short_help="Launches a project on a browser")           # type: ignore
@utils.error_catcher(parameter="check_project")
def launch():
    """
    Launches a Project on a browser. A project can be referenced the following ways:

    * With "--project / -p" optional parameter at the start of the command

    * As an environment variable. For example: "export LABBY_PROJECT=lab01"

    * Specified in the configuration file

    For example:

    > labby --project lab01 project launch
    """
    name = settings.SETTINGS.labby.project
    provider = provider_setup(f"Launching Project: {name}")
    project = Project(name=name)                                     # type: ignore
    typer.launch(provider.get_project_web_url(project))
