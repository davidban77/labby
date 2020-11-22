import typer
import labby.utils as utils
from enum import Enum
from typing import Optional
from rich.console import Console
# from rich.panel import Panel
from labby.providers import services
# from labby.models import Project


console = Console(color_system="auto")
app = typer.Typer(help="Management Device Templates")
config = {"gns3_server_url": "http://gns3-server:80"}
provider = services.get("GNS3", **config)


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
    utils.header("Templates list")
    console.print(
        provider.reporter.table_templates_list(field=filter, value=value),
        justify="center",
    )


@app.command(short_help="Retrieves details of a template")
def detail(name: str):
    """
    Retrieves Template details
    """
    utils.header(f"Template: {name}")
    provider.get_template_details(name)


if __name__ == "__main__":
    app()
