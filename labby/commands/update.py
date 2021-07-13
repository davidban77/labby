from enum import Enum
import typer
from typing import Any, Dict, Optional
from distutils.util import strtobool
from labby.providers import get_provider
from labby import utils
from labby import config


app = typer.Typer(help="Updates a Network Provider Lab Resource")


class LinkFilter(str, Enum):  # noqa: D101
    frequency_drop = "frequency_drop"
    packet_loss = "packet_loss"
    latency = "latency"
    jitter = "jitter"
    corrupt = "corrupt"
    bpf_expression = "bpf_expression"


def is_truthy(arg: Any):
    """Convert "truthy" strings into Booleans.

    Examples:
        >>> is_truthy('yes')
        True
    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    """
    if isinstance(arg, bool):
        return arg
    return bool(strtobool(arg))


@app.command(short_help="Updates a project")
def project(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    parameter: str = typer.Option(..., help="Parameter to set"),
    string_value: Optional[str] = typer.Option(None, help="String value to be set"),
    bool_value: Optional[str] = typer.Option(None, help="Boolean value to be set"),
    int_value: Optional[int] = typer.Option(None, help="Integer value to be set"),
    float_value: Optional[float] = typer.Option(None, help="Float value to be set"),
):
    """Update a Project based on a parameter and its value.

    Example:
    > labby update project -p lab01 --parameter auto_close --bool-value yes
    """
    if string_value:
        parsed_value = string_value
    elif bool_value:
        parsed_value = is_truthy(bool_value)
    elif int_value:
        parsed_value = int(int_value)  # type: ignore
    elif float_value:
        parsed_value = float(float_value)  # type: ignore
    else:
        utils.console.log("Value needs to be passed.", style="error")
        raise typer.Exit(1)

    env = config.get_config_env()
    provider = get_provider(provider_name=env.provider.name, provider_settings=env.provider)
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update project
    project.update(**{parameter: parsed_value})
    utils.console.log(project)


@app.command(short_help="Updates a node")
def node(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
    parameter: str = typer.Option(..., help="Parameter to set"),
    string_value: Optional[str] = typer.Option(None, help="String value to be set"),
    bool_value: Optional[str] = typer.Option(None, help="Boolean value to be set"),
    int_value: Optional[int] = typer.Option(None, help="Integer value to be set"),
    float_value: Optional[float] = typer.Option(None, help="Float value to be set"),
):
    """Update a Node based on a parameter and its value.

    Example:
    > labby update node -p lab01 -n r1 --parameter name --string-value new_r1
    """
    if string_value:
        parsed_value = string_value
    elif bool_value:
        parsed_value = is_truthy(bool_value)
    elif int_value:
        parsed_value = int(int_value)  # type: ignore
    elif float_value:
        parsed_value = float(float_value)  # type: ignore
    else:
        utils.console.log("Value needs to be passed.", style="error")
        raise typer.Exit(1)

    env = config.get_config_env()
    provider = get_provider(provider_name=env.provider.name, provider_settings=env.provider)
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    node = project.search_node(name=node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update node
    node.update(**{parameter: parsed_value})
    utils.console.log(node)


@app.command(short_help="Updates a node template")
def node_template(
    template_name: str = typer.Option(..., "--template", "-t", help="Node Template name"),
    parameter: str = typer.Option(..., help="Parameter to set"),
    string_value: Optional[str] = typer.Option(None, help="String value to be set"),
    bool_value: Optional[str] = typer.Option(None, help="Boolean value to be set"),
    int_value: Optional[int] = typer.Option(None, help="Integer value to be set"),
    float_value: Optional[float] = typer.Option(None, help="Float value to be set"),
):
    """Update a Node Template based on a parameter and its value.

    Example:
    > labby update template -t "Arista EOS vEOS 4.25F" --parameter ram --int-value 2048
    """
    if string_value:
        parsed_value = string_value
    elif bool_value:
        parsed_value = is_truthy(bool_value)
    elif int_value:
        parsed_value = int(int_value)  # type: ignore
    elif float_value:
        parsed_value = float(float_value)  # type: ignore
    else:
        utils.console.log("Value needs to be passed.", style="error")
        raise typer.Exit(1)

    env = config.get_config_env()
    provider = get_provider(provider_name=env.provider.name, provider_settings=env.provider)
    template = provider.search_template(template_name)
    if not template:
        utils.console.log(f"Node Template [cyan i]{template_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update node template
    template.update(**{parameter: parsed_value})
    utils.console.log(template)


@app.command(short_help="Updates a link filter")
def link_filter(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_a: str = typer.Option(..., "--node-a", "-na", help="Node name from ENDPOINT A"),
    port_a: str = typer.Option(..., "--port-a", "-pa", help="Port name from node on ENDPOINT A"),
    node_b: str = typer.Option(..., "--node-b", "-nb", help="Node name from ENDPOINT B"),
    port_b: str = typer.Option(..., "--por-b", "-pb", help="Port name from node on ENDPOINT B"),
    filter_type: LinkFilter = typer.Option(..., help="Filter to apply to the link"),
    filter_value: str = typer.Option(..., help="Value of Link Filter to apply to the link"),
):
    """Update a Link based on a parameter and its value.

    Example:
    > labby update link -p lab01 -na r1 -pa Ethernet2 -nb r2 -pb Ethernet2 --filter-type packet_loss --filter-value 77
    """
    filters: Dict[str, Any]
    if filter_type != "bpf_expression":
        filters = dict({filter_type: int(filter_value)})
    else:
        filters = dict({filter_type: filter_value})

    env = config.get_config_env()
    provider = get_provider(provider_name=env.provider.name, provider_settings=env.provider)
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    link = project.search_link(node_a, port_a, node_b, port_b)
    if not link:
        utils.console.log(
            f"Link [cyan i]{node_a}: {port_a} == {node_b}: {port_b}[/] not found. Nothing to do...", style="error"
        )
        raise typer.Exit(1)

    # Update link
    link.apply_metric(**filters)
    utils.console.log(link)
