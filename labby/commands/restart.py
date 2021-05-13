import typer
from labby.providers import get_provider
from labby import utils
from labby import config


app = typer.Typer(help="Runs Restart actions on Network Provider Lab Resources")


@app.command(short_help="Restarts a node")
def node(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
):
    """
    Restarts a Node.

    Example:

    > labby start node --project lab01 --node r1
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
    node.restart()
    utils.console.log(node)
