"""Labby delete command.

Handles the deletion of labby resources.

Example:
> labby delete --help
"""
import typer

from labby.commands.common import get_labby_objs_from_link, get_labby_objs_from_project, get_labby_objs_from_node
from labby import utils


app = typer.Typer(help="Deletes a Resource on Network Provider Lab")


@app.command(short_help="Deletes a project")
def project(project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT")):
    """
    Deletes a Project.

    Example:

    > labby delete project lab01
    """
    # Get Labby objects from project definition
    _, prj = get_labby_objs_from_project(project_name=project_name)

    # Delete project
    utils.console.log(prj)
    prj.delete()


@app.command(short_help="Deletes a node")
def node(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
):
    """
    Deletes a Node.

    Example:

    > labby delete node r1 --project lab01
    """
    # Get Labby objects from project and node definition
    _, _, device = get_labby_objs_from_node(project_name=project_name, node_name=node_name)

    # Delete node
    utils.console.log(device)
    device.delete()


@app.command(short_help="Deletes a link")
def link(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_a: str = typer.Option(..., "--node-a", "-na", help="Node name from ENDPOINT A"),
    port_a: str = typer.Option(..., "--port-a", "-pa", help="Port name from node on ENDPOINT A"),
    node_b: str = typer.Option(..., "--node-b", "-nb", help="Node name from ENDPOINT B"),
    port_b: str = typer.Option(..., "--port-b", "-pb", help="Port name from node on ENDPOINT B"),
):
    """
    Deletes a Link.

    Example:

    > labby delete link --project lab01 -na r1 -pa Ethernet1 -nb r2 -pb Ethernet1
    """
    # Get Labby objects from project and link definition
    _, _, enlace = get_labby_objs_from_link(
        project_name=project_name,
        node_a=node_a,
        port_a=port_a,
        node_b=node_b,
        port_b=port_b,
    )

    # Delete link
    utils.console.log(enlace)
    enlace.delete()
