import typer

from typing import Optional
from pathlib import Path
from labby import utils
from labby.settings import (
    delete_config_data,
    update_config_data,
    get_config_base_path,
    get_config_current_path,
    load_toml,
    save_toml,
)


app = typer.Typer(help="Configuration for Labby")


@app.command(name="list", short_help="Labby configuration settings")
def cli_list(
    cli_global: bool = typer.Option(
        False,
        "--global",
        help=f"General config stored at {get_config_base_path()}",
    ),
    cli_local: bool = typer.Option(
        False,
        "--local",
        help=f"Local config stored at {get_config_current_path()}",
    ),
    config: Optional[Path] = typer.Option(
        Path.cwd() / "labby.toml",
        "--config",
        "-c",
        help="Path to find labby.toml file",
    ),
):
    """
    Retrieves configuration parameters at a specified location

    Example:

    > labby config list --global
    """
    try:
        if cli_local:
            config_file = get_config_current_path()
        elif cli_global:
            config_file = get_config_base_path()
        elif config is not None:
            if not config.is_file():
                raise typer.Abort("config is not a file")
            config_file = config
        else:
            raise typer.Abort("config not set")

        utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")
        cfg = load_toml(config_file)
        for k, v in utils.flatten(cfg).items():
            utils.console.print(f"[bold cyan]{k}[/] = {v}")
    except Exception:
        utils.console.print_exception()


@app.command(name="set", short_help="Sets a Labby configuration parameter")
def cli_set(
    parameter: str = typer.Argument(
        ..., help="Parameter to set. A nested parameter can be set with `.` (dots)"
    ),
    value: str = typer.Argument(..., help="Value to be set"),
    cli_global: bool = typer.Option(
        False,
        "--global",
        help=f"General config stored at {get_config_base_path()}",
    ),
    cli_local: bool = typer.Option(
        False,
        "--local",
        help=f"Local config stored at {get_config_current_path()}",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to find labby.toml file",
    ),
):
    """
    Sets a Labby configuration parameter

    Example:

    > labby config set --local labby.environment home_lab
    """
    try:
        if cli_local:
            config_file = get_config_current_path()
        elif cli_global:
            config_file = get_config_base_path()
        elif config is None:
            raise typer.Abort("No config location specified")
        else:
            if not config.is_file():
                raise typer.Abort("Path specified is not a file")
            config_file = config

        utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")

        # Touch config file it it doesn't exist
        if not config_file.exists():
            if cli_global:
                config_file.parent.mkdir()
            config_file.touch()

        # Update config with parameters
        new_config = update_config_data(config_file, parameter, value)

        # Save config TOML
        save_toml(config_file, new_config)
        utils.console.print("Config data saved")
    except Exception:
        utils.console.print_exception(extra_lines=3)


@app.command(name="unset", short_help="Unsets a Labby configuration parameter")
def cli_unset(
    parameter: str = typer.Argument(
        ..., help="Parameter to unset. A nested parameter can be set with `.` (dots)"
    ),
    cli_global: bool = typer.Option(
        False,
        "--global",
        help=f"General config stored at {get_config_base_path()}",
    ),
    cli_local: bool = typer.Option(
        False,
        "--local",
        help=f"Local config stored at {get_config_current_path()}",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to find labby.toml file",
    ),
):
    """
    Unsets a Labby configuration parameter

    Example:

    > labby config unset -c example/labby.toml environment.aws.eve_ng.verify_cert
    """
    try:
        if cli_local:
            config_file = get_config_current_path()
        elif cli_global:
            config_file = get_config_base_path()
        elif config is None:
            raise typer.Abort("No config location specified")
        else:
            if not config.is_file():
                raise typer.Abort("Path specified is not a file")
            config_file = config

        if not config_file.exists():
            raise typer.Abort("config file does not exists")

        utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")

        # Update config with parameters
        new_config = delete_config_data(config_file, parameter)

        # Save config TOML
        save_toml(config_file, new_config)
        utils.console.print("Config data saved")
    except Exception:
        utils.console.print_exception(extra_lines=3)
