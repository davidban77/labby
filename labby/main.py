import typer
import labby.commands.config
import labby.commands.projects
import labby.commands.templates
import labby.commands.nodes
import labby.commands.connections
import labby.commands.run
from labby import settings
from labby import utils

from typing import Optional
from pathlib import Path


app = typer.Typer(help=f"{utils.banner()}Awesome Network Lab Management Tool!")
state = {"verbose": False}

app.add_typer(labby.commands.config.app, name="config")
app.add_typer(labby.commands.projects.app, name="project")
app.add_typer(labby.commands.templates.app, name="template")
app.add_typer(labby.commands.nodes.app, name="node")
app.add_typer(labby.commands.connections.app, name="link")
app.add_typer(labby.commands.run.app, name="run")


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = False,
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to find labby.toml file",
        envvar="LABBY_CONFIG",
    ),
    environment: Optional[str] = typer.Option(
        None,
        "--environment",
        "-e",
        help="Environment of network lab provider",
        envvar="LABBY_ENVIRONMENT",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Network Lab provider to use",
        envvar="LABBY_PROVIDER",
    ),
    project: Optional[str] = typer.Option(
        None, "--project", help="Network Project to use", envvar="LABBY_PROJECT"
    ),
):
    ctx.obj = config
    if ctx.invoked_subcommand != "config":
        settings.load(
            config_file=config,
            environment=environment,
            provider=provider,
            project=project,
        )
    if verbose:
        typer.echo("Will write verbose output")
        state["verbose"] = True
