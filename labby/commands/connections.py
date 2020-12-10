import typer
import labby.utils as utils
from enum import Enum
from typing import Optional
from labby import settings
from labby.providers import provider_setup
from labby.models import Project, Connection


app = typer.Typer(help="Management of Lab Links for a Project")


class ProjectFilter(str, Enum):
    node_type = "node_type"
    category = "category"
    status = "status"
    # template = "template"


@app.command(
    name="list",
    short_help="Retrieves a summary list of links in a project",
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
    Retrieve a summary list of links for a given project.

    For example:

    > labby --project lab01 link list --filter status --value started
    """
    project = settings.SETTINGS.labby.project
    provider = provider_setup(f"Connections list for project: [bold]{project}[/]")
    prj = Project(name=project)  # type: ignore
    provider.get_connections_list(project=prj, field=field, value=value)


@app.command(short_help="Finds a link in a project")  # type: ignore
@utils.error_catcher(parameter="check_project")
def find(
    node_a: str = typer.Option(
        ..., "--node_a", "-na", help="Node name from ENDPOINT A"
    ),
    port_a: str = typer.Option(
        ..., "--port_a", "-pa", help="Port name from node on ENDPOINT A"
    ),
    node_b: str = typer.Option(
        ..., "--node_b", "-nb", help="Node name from ENDPOINT B"
    ),
    port_b: str = typer.Option(
        ..., "--port_b", "-pb", help="Port name from node on ENDPOINT B"
    ),
):
    """
    Find a Link in a project.

    > labby --project lab01 link find --node_a router01 --port_a eth1
        --node_b router02 --port_b eth2
    """
    project = settings.SETTINGS.labby.project
    _name = f"{node_a}: {port_a} <===> {port_b} :{node_b}"
    provider = provider_setup(f"Finding link: [bold]{_name}[/]")
    prj = Project(project)  # type: ignore
    connection = Connection(
        name=_name,
        project=project,  # type: ignore
        endpoints=[
            {"name": node_a, "port": port_a},
            {"name": node_b, "port": port_b},
        ],
    )
    provider.get_connection_details(connection=connection, project=prj)


@app.command(short_help="Creates a connection")  # type: ignore
@utils.error_catcher(parameter="check_project")
def create(
    node_a: str = typer.Option(
        ..., "--node_a", "-na", help="Node name from ENDPOINT A"
    ),
    port_a: str = typer.Option(
        ..., "--port_a", "-pa", help="Port name from node on ENDPOINT A"
    ),
    node_b: str = typer.Option(
        ..., "--node_b", "-nb", help="Node name from ENDPOINT B"
    ),
    port_b: str = typer.Option(
        ..., "--port_b", "-pb", help="Port name from node on ENDPOINT B"
    ),
):
    """
    Creates a Link

    > labby --project lab01 link create --node_a router01 --port_a eth1
        --node_b router02 --port_b eth2
    """
    project = settings.SETTINGS.labby.project
    _name = f"{node_a}: {port_a} <===> {port_b} :{node_b}"
    provider = provider_setup(f"Finding link: [bold]{_name}[/]")
    prj = Project(project)  # type: ignore
    connection = Connection(
        name=_name,
        project=project,  # type: ignore
        endpoints=[
            {"name": node_a, "port": port_a},
            {"name": node_b, "port": port_b},
        ],
    )
    provider.create_connection(connection=connection, project=prj)


@app.command(short_help="Deletes a link")  # type: ignore
@utils.error_catcher(parameter="check_project")
def delete(
    node_a: str = typer.Option(
        ..., "--node_a", "-na", help="Node name from ENDPOINT A"
    ),
    port_a: str = typer.Option(
        ..., "--port_a", "-pa", help="Port name from node on ENDPOINT A"
    ),
    node_b: str = typer.Option(
        ..., "--node_b", "-nb", help="Node name from ENDPOINT B"
    ),
    port_b: str = typer.Option(
        ..., "--port_b", "-pb", help="Port name from node on ENDPOINT B"
    ),
):
    """
    Deletes a Link.

    NOTE: Order does not matter, just the pairing of node and port

    > labby --project lab01 link delete --node_a router01 --port_a eth1
        --node_b router02 --port_b eth2
    """
    project = settings.SETTINGS.labby.project
    _name = f"{node_a}: {port_a} <===> {port_b} :{node_b}"
    provider = provider_setup(f"Finding link: [bold]{_name}[/]")
    prj = Project(project)  # type: ignore
    connection = Connection(
        name=_name,
        project=project,  # type: ignore
        endpoints=[
            {"name": node_a, "port": port_a},
            {"name": node_b, "port": port_b},
        ],
    )
    provider.delete_connection(connection=connection, project=prj)
