"""Labby delete command.

Handles the deletion of labby resources.

Example:
> labby delete --help
"""
import typer

from labby import utils, config


app = typer.Typer(help="Deletes a Resource on Network Provider Lab")


@app.command(short_help="Deletes a project")
def project(project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT")):
    """
    Deletes a Project.

    Example:

    > labby delete project lab01
    """
    provider = config.get_provider()
    prj = provider.search_project(project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

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
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    device = prj.search_node(name=node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

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
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    enlace = prj.search_link(node_a, port_a, node_b, port_b)
    if not enlace:
        utils.console.log(
            f"Link [cyan i]{node_a}: {port_a} == {node_b}: {port_b}[/] not found. Nothing to do...", style="error"
        )
        raise typer.Exit(1)

    # Delete link
    utils.console.log(enlace)
    enlace.delete()
