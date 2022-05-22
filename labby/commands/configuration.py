"""Labby configuration command.

Handles labby configuration.

Example:
> labby configuration --help
"""
from pathlib import Path

import typer
from rich.syntax import Syntax
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.scope import render_scope
from rich.align import Align
from rich.box import ROUNDED
from rich.text import Text

from labby import utils, config


app = typer.Typer(help="Configuration for Labby")


@app.command(short_help="Labby configuration settings")
def show(
    ctx: typer.Context,
):
    """
    Retrieves configuration parameters at a specified location.

    Example:

    > labby config show
    """
    config_file: Path = ctx.obj["config_file"]

    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")
    utils.console.print(
        Syntax(
            config_file.read_text(),
            "toml",
            line_numbers=False,
            background_color="default",
        )
    )
    typer.echo()


@app.command(short_help="Launches configuration file for edit")
def edit(
    ctx: typer.Context,
):
    """
    Launches configuration file for edit.

    Example:

    > labby -c examples/labby.toml config edit
    """
    config_file: Path = ctx.obj["config_file"]

    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")
    typer.launch(str(config_file.absolute()), locate=True)


@app.command(short_help="Show environments configured")
def environments(
    ctx: typer.Context,
):
    """
    Shows information from all environments in the configuration.

    Example:

    > labby -c labby.toml config environmentss
    """
    config_file = ctx.obj["config_file"]
    table = Table("Environment", "Description", "URL", "Online", show_header=True, header_style="blod magenta")
    config_data = config.load_toml(config_file)  # type: ignore
    layout = Layout()
    layout.split(Layout(name="main", ratio=1), Layout(size=7, name="footer"))
    layout["main"].split_row(Layout(name="environments", ratio=2), Layout(name="providers", ratio=4))
    env_layouts = []
    prov_layouts = []
    for env in config_data["environment"]:
        pan = Panel(
            f"Environment: [b cyan]{env}[/]\nActive Provider: [b cyan]{config_data['environment'][env]['provider']}",
            title="Environment",
            padding=1,
            highlight=True,
        )
        if "meta" not in config_data["environment"][env]:
            env_layouts.append(Layout(pan))
        else:
            meta_p = Panel(render_scope(config_data["environment"][env]["meta"]), title="Meta")
            env_layout = Layout()
            env_layout.split(Layout(pan), Layout(meta_p))
            env_layouts.append(env_layout)
        table = Table(
            "Provider",
            "Kind",
            "URL",
            "User",
            header_style="bold cyan",
            box=ROUNDED,
            highlight=True,
            # expand=True,
            show_lines=True,
        )
        for prov, prov_data in config_data["environment"][env]["providers"].items():
            table.add_row(prov, prov_data["kind"], prov_data["server_url"], prov_data.get("user", "N/A"))
        prov_layouts.append(Layout(Panel(Align.center(table, vertical="middle"), title="Providers")))
    layout["environments"].split(*env_layouts)
    layout["providers"].split(*prov_layouts)
    env = config.get_environment()
    layout["footer"].update(Text(f"Active Environment: {env.name.upper()}", style="bold magenta", justify="center"))
    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")
    utils.console.print(layout)
