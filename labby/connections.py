import typer
import labby.utils as utils
from enum import Enum
from typing import Optional
from rich.console import Console
from labby.providers import services
from labby.models import Project, Connection


console = Console(color_system="auto")
app = typer.Typer(help="Management of Lab Links for a Project")
config = {"gns3_server_url": "http://gns3-server:80"}
provider = services.get("GNS3", **config)


class ProjectFilter(str, Enum):
    node_type = "node_type"
    category = "category"
    status = "status"
    # template = "template"


@app.command(
    name="list",
    short_help="Retrieves a summary list of links in a project",
)
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
    Retrieve a summary list of links for a given project.

    For example:

    > labby link list project01 --filter status --value started
    """
    utils.header(f"Connections list for project: [bold]{project}[/]")
    prj = Project(name=project)
    provider.get_connections_list(project=prj, field=field, value=value)


@app.command(short_help="Finds a link in a project")
def find(
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the link belongs"
    ),
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
    Find a Link in a project

    > labby link find --project project01 --node_a router01 --port_a eth1
        --node_b router02 --port_b eth2
    """
    _name = f"{node_a}: {port_a} <===> {port_b} :{node_b}"
    utils.header(f"Finding link: [bold]{_name}[/]")
    prj = Project(project)
    connection = Connection(
        name=_name,
        project=project,
        endpoints=[{"name": node_a, "port": port_a}, {"name": node_b, "port": port_b}],
    )
    provider.get_connection_details(connection=connection, project=prj)


@app.command(short_help="Creates a connection")
def create(
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the link belongs"
    ),
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

    > labby link create --project project01 --node_a router01 --port_a eth1
        --node_b router02 --port_b eth2
    """
    _name = f"{node_a}: {port_a} <===> {port_b} :{node_b}"
    utils.header(f"Finding link: [bold]{_name}[/]")
    prj = Project(project)
    connection = Connection(
        name=_name,
        project=project,
        endpoints=[{"name": node_a, "port": port_a}, {"name": node_b, "port": port_b}],
    )
    provider.create_connection(connection=connection, project=prj)


@app.command(short_help="Deletes a link")
def delete(
    project: str = typer.Option(
        ..., "--project", "-p", help="Project the link belongs"
    ),
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

    > labby link delete --project project01 --node_a router01 --port_a eth1
        --node_b router02 --port_b eth2
    """
    _name = f"{node_a}: {port_a} <===> {port_b} :{node_b}"
    utils.header(f"Finding link: [bold]{_name}[/]")
    prj = Project(project)
    connection = Connection(
        name=_name,
        project=project,
        endpoints=[{"name": node_a, "port": port_a}, {"name": node_b, "port": port_b}],
    )
    provider.delete_connection(connection=connection, project=prj)


if __name__ == "__main__":
    app()
