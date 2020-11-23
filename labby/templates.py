import typer
from enum import Enum
from typing import Optional
from labby import utils
from labby.providers import provider_setup


app = typer.Typer(help="Management Device Templates")


class TemplateFilter(str, Enum):
    category = "category"
    template_type = "template_type"


@app.command(name="list", short_help="Retrieve a summary list of node templates")
def cli_list(
    filter: Optional[TemplateFilter] = typer.Option(
        None, help="If used you MUST provide expected `--value`"
    ),
    value: Optional[str] = typer.Option(
        None,
        help="Value to be used with `--filter`",
    ),
):
    """
    Retrieve a summary list of node templates configured on server

    For example:

    > labby template list --filter template_type --value docker
    """
    try:
        provider = provider_setup("Templates list")
        utils.console.print(
            provider.reporter.table_templates_list(field=filter, value=value),
            justify="center",
        )
    except Exception:
        utils.console.print_exception()


@app.command(short_help="Retrieves details of a template")
def detail(name: str):
    """
    Retrieves Template details
    """
    try:
        provider = provider_setup(f"Template: {name}")
        provider.get_template_details(name)
    except Exception:
        utils.console.print_exception()
