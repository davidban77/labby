import typer
from labby.providers import get_provider
from labby import utils
from labby import config


app = typer.Typer(help="Deletes a Resource on Network Provider Lab")


@app.command(short_help="Deletes a project")
def project(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
):
    """
    Deletes a Project.

    Example:

    > labby delete project --project lab01
    """
    provider = get_provider(
        provider_name=config.SETTINGS.environment.provider.name, provider_settings=config.SETTINGS.environment.provider
    )
    project = provider.search_project(project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log(project)
    project.delete()


@app.command(short_help="Deletes a node")
def node(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
):
    """
    Deletes a Node.

    Example:

    > labby delete node --project lab01 --node r1
    """
    provider = get_provider(
        provider_name=config.SETTINGS.environment.provider.name, provider_settings=config.SETTINGS.environment.provider
    )
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    node = project.search_node(name=node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log(node)
    node.delete()


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
    provider = get_provider(
        provider_name=config.SETTINGS.environment.provider.name, provider_settings=config.SETTINGS.environment.provider
    )
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    link = project.search_link(node_a, port_a, node_b, port_b)
    if not link:
        utils.console.log(
            f"Link [cyan i]{node_a}: {port_a} == {node_b}: {port_b}[/] not found. Nothing to do...", style="error"
        )
        raise typer.Exit(1)
    utils.console.log(link)
    link.delete()
