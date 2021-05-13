import typer
from labby.providers import get_provider
from labby import utils
from labby import config


app = typer.Typer(help="Runs Stop/Halt actions on Network Provider Lab Resources")


@app.command(short_help="Stops a project")
def project(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    stop_nodes: bool = typer.Option(
        True, help="Strategy to use to start nodes in project"
    ),
):
    """
    Stops a Project and optionally stops the nodes preemptively.

    Example:

    > labby stop project --project lab01
    """
    provider = get_provider(
        provider_name=config.SETTINGS.environment.provider.name, provider_settings=config.SETTINGS.environment.provider
    )
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    project.stop(stop_nodes=stop_nodes)


@app.command(short_help="Stops a node")
def node(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
):
    """
    Stops a Node.

    Example:

    > labby stop node --project lab01 --node r1
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
    node.stop()
    utils.console.log(node)
