"""The main module for labby. All of the labby commands are loaded in this module."""
from typing import Any, Dict, Optional
from pathlib import Path

import typer
import toml
from dotenv import load_dotenv
# from rich.traceback import install as traceback_install
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from nornir.core.plugins.inventory import InventoryPluginRegister

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
from labby.nornir.plugins.inventory.labby import LabbyNornirInventory
from labby import __version__

# traceback_install(show_locals=True)


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
    """Prints the current version of labby."""
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
    # pylint: disable=unused-argument
    """Main function that loads labby configuration file."""
    if ctx.invoked_subcommand == "init":
        return
    if not config_file:
        config_file = config.get_config_current_path()
        if not config_file.is_file():
            config_file = config.get_config_base_path()
            if not config_file.is_file():
                utils.console.print("[red]Configuration specified is not a file[/]")
                raise typer.Exit(code=1)
    ctx.obj = dict(config_file=config_file)

    # Load .env variables
    load_dotenv()
    config.load_config(config_file=config_file, environment_name=environment, provider_name=provider, debug=verbose)

    if config.SETTINGS is None:
        utils.console.print("No configuration settings found", style="error")
        raise typer.Exit(1)

    # Register each provider environment
    try:
        register_service(config.SETTINGS.environment.provider.name, config.SETTINGS.environment.provider.kind)
    except AttributeError as err:
        utils.console.print(
            "An attribute was not found in configuration. Most likely is a configuration file issue", style="error"
        )
        raise typer.Exit(1) from err


@app.command(short_help="Initialises Labby Configuration file.")
def init(
    cli_global: bool = typer.Option(
        False,
        "--global",
        help=(
            f"If set, the general config will be stored at {config.get_config_base_path()}. By default, it will be "
            "generated on the current directory."
        ),
    )
):
    """Create basic configuration file for labby. It will guide you through some options you can set.

    Example:

    > labby init --global
    """
    if cli_global:
        config_file = config.get_config_base_path()
    else:
        config_file = config.get_config_current_path()

    # Touch config file it it doesn't exist
    if not config_file.exists():
        if cli_global:
            config_file.parent.mkdir()
        config_file.touch()

    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")

    environment = Prompt.ask("[cyan]Environment name for your network lab providers", default="default")
    environment_description = Prompt.ask("[cyan]Environment description")

    provider_name = Prompt.ask("[cyan]Network Lab Provider name", default="default-provider")

    provider_type = Prompt.ask(
        "[cyan]Network Lab Provider Type",
        choices=["gns3", "vrnetlab", "eve_ng"],
        default="gns3",
    )

    provider_url = Prompt.ask("[cyan]Network Lab Provider server URL")

    # Environment data
    config_data: Dict[str, Any] = dict(main={}, environment={})

    config_data["main"]["environment"] = environment
    config_data["environment"][environment] = dict(
        description=environment_description,
        provider=provider_name,
        providers={provider_name: dict(server_url=provider_url, kind=provider_type)},
    )

    rendered_data = toml.dumps(config_data)
    utils.console.print(
        Syntax(
            rendered_data,
            "toml",
            line_numbers=True,
            background_color="default",
        )
    )
    save_file = Confirm.ask("[cyan]Do you want to save file?")
    if save_file:
        config_file.write_text(rendered_data)
        utils.console.print("Config data saved")
    else:
        utils.console.print("Nothing to do.")

    # project_yes = Confirm.ask("[cyan]Would you like to set a project in the configuration file?")

    # if project_yes is True:
    #     project_name = Prompt.ask("[cyan]Project name", default="labby_project")

    #     project_description = Prompt.ask("[cyan]Project description")

    #     project_version = Prompt.ask("[cyan]Project initial version", default="0.0.1")

    #     prj_contribs = Prompt.ask(
    #         "[cyan]Project contributors, for multiple entries separate them with `,`",
    #         default="Netpanda <netpanda@example.com>,Bethepacket <bethepacket@example.com>",
    #     )

    #     project_contribs = prj_contribs.split(",")

    #     project_path = Path(Prompt.ask("[cyan]Directory path for project data"))

    #     project_hosts_file = project_path / "inventory/hosts.yml"
    #     project_groups_file = project_path / "inventory/groups.yml"

    #     project_data = dict(
    #         project_name=project_name,
    #         project_description=project_description,
    #         project_version=project_version,
    #         project_contribs=project_contribs,
    #         project_hosts_file=project_hosts_file,
    #         project_groups_file=project_groups_file,
    #     )

    #     rendered_data = config.create_config_data(project_data)
    #     utils.console.print(
    #         Syntax(
    #             rendered_data,
    #             "toml",
    #             line_numbers=True,
    #             background_color="default",
    #         )
    #     )
    #     save_file = Confirm.ask("[cyan]Do you want to save file?")
    #     if save_file:
    #         config_file.write_text(rendered_data)
    #         utils.console.print("Config data saved")
    #     else:
    #         utils.console.print("Nothing to do.")
