import typer

import labby.commands.build
import labby.commands.configuration
import labby.commands.run
import labby.commands.get
import labby.commands.start
import labby.commands.restart
import labby.commands.stop
import labby.commands.create
import labby.commands.delete
import labby.commands.update
import labby.commands.connect

from labby import config
from labby import utils
from labby.providers import register_service

from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from rich.traceback import install as traceback_install
from nornir.core.plugins.inventory import InventoryPluginRegister
from labby.nornir.plugins.inventory.labby import LabbyNornirInventory

traceback_install()


InventoryPluginRegister.register("LabbyNornirInventory", LabbyNornirInventory)


app = typer.Typer(help=f"{utils.banner()} Awesome Network Lab Management Tool!")
state = {"verbose": False}

# app.add_typer(labby.commands.projects.app, name="project")
app.add_typer(labby.commands.run.app, name="run")
app.add_typer(labby.commands.get.app, name="get")
app.add_typer(labby.commands.start.app, name="start")
app.add_typer(labby.commands.restart.app, name="restart")
app.add_typer(labby.commands.stop.app, name="stop")
app.add_typer(labby.commands.create.app, name="create")
app.add_typer(labby.commands.delete.app, name="delete")
app.add_typer(labby.commands.update.app, name="update")
app.add_typer(labby.commands.configuration.app, name="config")
app.add_typer(labby.commands.build.app, name="build")
app.add_typer(labby.commands.connect.app, name="connect")


def version_callback(value: bool):
    from labby import __version__

    if value:
        utils.console.print(f"Labby version [cyan bold]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = False,
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
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
):
    if not config_file:
        config_file = config.get_config_current_path()
        if not config_file.is_file():
            config_file = config.get_config_base_path()
            if not config_file.is_file():
                utils.console.print("[red]Configuration specified is not a file[/]")
                raise typer.Exit(code=1)
    ctx.obj = dict(config_file=config_file)
    config.load_config(config_file=config_file, environment_name=environment, provider_name=provider, debug=verbose)

    if config.SETTINGS is None:
        utils.console.print("No configuration settings found", style="error")
        raise typer.Exit(1)

    # Register each provider environment
    try:
        register_service(config.SETTINGS.environment.provider.name, config.SETTINGS.environment.provider.kind)
    except AttributeError:
        utils.console.print(
            "An attribute was not found in configuration. Most likely is a configuration file issue", style="error"
        )
        raise typer.Exit(1)
    # Load env vars after processed in config to be used by typer commands
    load_dotenv()
