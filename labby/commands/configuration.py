"""Labby configuration command.

Handles labby configuration.

Example:
> labby configuration --help
"""
import typer

from pathlib import Path
from labby import utils, config
from rich.syntax import Syntax
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import render_scope
from rich.align import Align
from rich.box import ROUNDED
from rich.text import Text


app = typer.Typer(help="Configuration for Labby")


@app.command(short_help="Labby configuration settings")
@utils.error_catcher
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
@utils.error_catcher
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
@utils.error_catcher
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
        p = Panel(
            f"Environment: [b cyan]{env}[/]\nActive Provider: [b cyan]{config_data['environment'][env]['provider']}",
            title="Environment",
            padding=1,
            highlight=True,
        )
        if "meta" not in config_data["environment"][env]:
            env_layouts.append(Layout(p))
        else:
            meta_p = Panel(render_scope(config_data["environment"][env]["meta"]), title="Meta")
            env_layout = Layout()
            env_layout.split(Layout(p), Layout(meta_p))
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
    layout["footer"].update(
        Text(f"Active Environment: {env.name.upper()}", style="bold magenta", justify="center")
    )
    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")
    utils.console.print(layout)


# @app.command(short_help="Creates basic configuration file")
# @utils.error_catcher
# def create(
#     ctx: typer.Context,
#     cli_global: bool = typer.Option(
#         False,
#         "--global",
#         help=f"General config stored at {get_config_base_path()}",
#     ),
#     cli_local: bool = typer.Option(
#         False,
#         "--local",
#         help=f"Local config stored at {get_config_current_path()}",
#     ),
# ):
#     """
#     Creates basic configuration file for labby. It will guide you through some options
#     you can set

#     Example:

#     > labby config create --local
#     """
#     if cli_local:
#         config_file = get_config_current_path()
#     elif cli_global:
#         config_file = get_config_base_path()
#     elif ctx.obj is None:
#         utils.console.print("[red]No configuration location specified[/]")
#         raise typer.Exit(code=1)
#     else:
#         config_file = ctx.obj

#     # Touch config file it it doesn't exist
#     if not config_file.exists():
#         if cli_global:
#             config_file.parent.mkdir()
#         config_file.touch()

#     utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")

#     environment = Prompt.ask(
#         "[cyan]Environment name for your network lab providers", default="default"
#     )
#     environment_description = Prompt.ask("[cyan]Environment description")

#     provider = Prompt.ask(
#         "[cyan]Network Lab Provider",
#         choices=["gns3", "vrnetlab", "eve_ng"],
#         default="gns3",
#     )

#     provider_url = Prompt.ask("[cyan]Network Lab Provider server URL")

#     data = dict(
#         environment=environment,
#         environment_description=environment_description,
#         provider=provider,
#         provider_url=provider_url,
#     )

#     project_yes = Confirm.ask(
#         "[cyan]Would you like to set a project in the configuration file?"
#     )

#     if project_yes is True:
#         project_name = Prompt.ask("[cyan]Project name", default="labby_project")

#         project_description = Prompt.ask("[cyan]Project description")

#         project_version = Prompt.ask(
#             "[cyan]Project initial version", default="0.0.1"
#         )

#         prj_authors = Prompt.ask(
#             "[cyan]Project authors, for multiple authors separate them with `,`",
#             default="Foo Bar <foo.bar@example.com>,Bar Foo <bar.foo@example.com>",
#         )

#         project_authors = prj_authors.split(",")

#         project_path = Path(Prompt.ask("[cyan]Directory path for project data"))

#         project_hosts_file = project_path / "inventory/hosts.yml"
#         project_groups_file = project_path / "inventory/groups.yml"

#         data.update(
#             dict(
#                 project_name=project_name,
#                 project_description=project_description,
#                 project_version=project_version,
#                 project_authors=project_authors,
#                 project_hosts_file=project_hosts_file,
#                 project_groups_file=project_groups_file,
#             )
#         )

#     rendered_data = create_config_data(data)
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
