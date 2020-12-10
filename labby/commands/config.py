import typer

from pathlib import Path
from labby import utils
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from labby.settings import (
    get_config_base_path,
    get_config_current_path,
    create_config_data,
)


app = typer.Typer(help="Configuration for Labby")


@app.command(short_help="Labby configuration settings")
@utils.error_catcher
def show(
    ctx: typer.Context,
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
):
    """
    Retrieves configuration parameters at a specified location

    Example:

    > labby config show --global
    """
    if cli_local:
        config_file = get_config_current_path()
    elif cli_global:
        config_file = get_config_base_path()
    elif ctx.obj is not None:
        if not ctx.obj.is_file():
            utils.console.print("[red]Configuration specified is not a file[/]")
            raise typer.Exit(code=1)
        config_file = ctx.obj
    else:
        utils.console.print("[red]Configuration not set[/]")
        raise typer.Exit(code=1)

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
):
    """
    Launches configuration file for edit

    Example:

    > labby config edit -c examples/labby.toml
    """
    if cli_local:
        config_file = get_config_current_path()
    elif cli_global:
        config_file = get_config_base_path()
    elif ctx.obj is None:
        utils.console.print("[red]No configuration location specified[/]")
        raise typer.Exit(code=1)
    else:
        if not ctx.obj.is_file():
            utils.console.print("[red]Path specified is not a file[/]")
            raise typer.Exit(code=1)
        config_file = ctx.obj

    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")

    # Touch config file it it doesn't exist
    if not config_file.exists():
        if cli_global:
            config_file.parent.mkdir()
        config_file.touch()

    typer.launch(str(config_file.absolute()), locate=True)


@app.command(short_help="Creates basic configuration file")
@utils.error_catcher
def create(
    ctx: typer.Context,
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
):
    """
    Creates basic configuration file for labby. It will guide you through some options
    you can set

    Example:

    > labby config create --local
    """
    if cli_local:
        config_file = get_config_current_path()
    elif cli_global:
        config_file = get_config_base_path()
    elif ctx.obj is None:
        utils.console.print("[red]No configuration location specified[/]")
        raise typer.Exit(code=1)
    else:
        config_file = ctx.obj

    # Touch config file it it doesn't exist
    if not config_file.exists():
        if cli_global:
            config_file.parent.mkdir()
        config_file.touch()

    utils.header(f"Config file at: [bold]{config_file.absolute()}[/]")

    environment = Prompt.ask(
        "[cyan]Environment name for your network lab providers", default="default"
    )
    environment_description = Prompt.ask("[cyan]Environment description")

    provider = Prompt.ask(
        "[cyan]Network Lab Provider",
        choices=["gns3", "vrnetlab", "eve_ng"],
        default="gns3",
    )

    provider_url = Prompt.ask("[cyan]Network Lab Provider server URL")

    data = dict(
        environment=environment,
        environment_description=environment_description,
        provider=provider,
        provider_url=provider_url,
    )

    project_yes = Confirm.ask(
        "[cyan]Would you like to set a project in the configuration file?"
    )

    if project_yes is True:
        project_name = Prompt.ask("[cyan]Project name", default="labby_project")

        project_description = Prompt.ask("[cyan]Project description")

        project_version = Prompt.ask(
            "[cyan]Project initial version", default="0.0.1"
        )

        prj_authors = Prompt.ask(
            "[cyan]Project authors, for multiple authors separate them with `,`",
            default="Foo Bar <foo.bar@example.com>,Bar Foo <bar.foo@example.com>",
        )

        project_authors = prj_authors.split(",")

        project_path = Path(Prompt.ask("[cyan]Directory path for project data"))

        project_hosts_file = project_path / "inventory/hosts.yml"
        project_groups_file = project_path / "inventory/groups.yml"

        data.update(
            dict(
                project_name=project_name,
                project_description=project_description,
                project_version=project_version,
                project_authors=project_authors,
                project_hosts_file=project_hosts_file,
                project_groups_file=project_groups_file,
            )
        )

    rendered_data = create_config_data(data)
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
