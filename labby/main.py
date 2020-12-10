import typer
import labby.config
import labby.projects
import labby.templates
import labby.nodes
import labby.connections
import labby.run
from labby import settings
from labby import utils

from typing import Optional
from pathlib import Path


app = typer.Typer(help=f"{utils.banner()}Awesome Network Lab Management Tool!")
state = {"verbose": False}

app.add_typer(labby.config.app, name="config")
app.add_typer(labby.projects.app, name="project")
app.add_typer(labby.templates.app, name="template")
app.add_typer(labby.nodes.app, name="node")
app.add_typer(labby.connections.app, name="link")
app.add_typer(labby.run.app, name="run")


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
