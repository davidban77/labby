"""Labby update command.

Handles all update/modify related actions of labby resources.

Example:
> labby update --help
"""
from enum import Enum
from typing import Any, Dict, List

import typer

from labby import utils
from labby import config

app = typer.Typer(help="Updates a Network Provider Lab Resource")
project_app = typer.Typer(help="Updates a Network Provider Project")
node_app = typer.Typer(help="Updates a Network Provider Node")
link_app = typer.Typer(help="Updates a Network Provider Link")

app.add_typer(project_app, name="project")
app.add_typer(node_app, name="node")
app.add_typer(link_app, name="link")


def strtobool(value: Any) -> bool:
    """Return whether the provided string (or any value really) represents true. Otherwise false."""
    if not value:
        return False
    return str(value).lower() in ("y", "yes", "t", "true", "on", "1")


class LinkFilter(str, Enum):
    """Link Filter Enum."""

    # pylint: disable=invalid-name
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


def parse_value(value: str, bool_flag: bool, int_flag: bool, float_flag: bool) -> Any:
    """Parse a string into a Python object.

    Args:
        value (str): A string to be parsed.
        bool_flag (bool): A flag indicating whether to parse as a Boolean.
        int_flag (bool): A flag indicating whether to parse as an integer.
        float_flag (bool): A flag indicating whether to parse as a float.

    Returns:
        Any: A Python object.
    """
    if bool_flag:
        parsed_value = is_truthy(value)
    elif int_flag:
        parsed_value = int(value)
    elif float_flag:
        parsed_value = float(value)
    else:
        parsed_value = str(value)
    return parsed_value


@project_app.command(name="attr", short_help="Updates a general attribute of a project")
def project_attr(
    attr: str = typer.Argument(..., help="Attribute to set"),
    value: str = typer.Argument(..., help="Value to set"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    bool_flag: bool = typer.Option(False, "--bool", "-b", help="Value to be parsed as a boolean"),
    int_flag: bool = typer.Option(False, "--int", "-i", help="Value to be parsed as an integer"),
    float_flag: bool = typer.Option(False, "--float", "-f", help="Value to be parsed as a float"),
):
    """Update a Project's general attribute.

    Example:

    > labby update project attr --project lab01 --bool auto_close yes
    """
    parsed_value = parse_value(value, bool_flag, int_flag, float_flag)

    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update project
    prj.update(**{attr: parsed_value})
    utils.console.log(prj)


@project_app.command(name="labels", short_help="Updates the labels of a project")
def project_labels(
    labels: str = typer.Argument(..., help="Labels to set"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
):
    """Update the labels of a Project.

    Example:

    > labby update project labels --project lab01 --labels "lab1,lab2"
    """
    extracted_labels: List[str] = labels.split(",")
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update project
    prj.update(labels=extracted_labels)
    utils.console.log(prj)


@node_app.command(name="attr", short_help="Updates a general attribute of a node")
def node_attr(
    attr: str = typer.Argument(..., help="Attribute to set"),
    value: str = typer.Argument(..., help="Value to set"),
    node_name: str = typer.Option(..., "--node", "-n", help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Projectname", envvar="LABBY_PROJECT"),
    bool_flag: bool = typer.Option(False, "--bool", "-b", help="Value to be parsed as a boolean"),
    int_flag: bool = typer.Option(False, "--int", "-i", help="Value to be parsed as an integer"),
    float_flag: bool = typer.Option(False, "--float", "-f", help="Value to be parsed as a float"),
):
    """Update a Node's general attribute.

    Example:

    > labby update node attr --project lab01 --node r1 name new_r1
    """
    parsed_value = parse_value(value, bool_flag, int_flag, float_flag)

    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    device = prj.search_node(name=node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update node
    device.update(**{attr: parsed_value})
    utils.console.log(device)


@node_app.command(name="template", short_help="Updates a general attribute of a node template")
def node_template(
    attr: str = typer.Argument(..., help="Attribute to set"),
    value: str = typer.Argument(..., help="Value to set"),
    template_name: str = typer.Option(..., "--template", "-t", help="Node Template name"),
    bool_flag: bool = typer.Option(False, "--bool", "-b", help="Value to be parsed as a boolean"),
    int_flag: bool = typer.Option(False, "--int", "-i", help="Value to be parsed as an integer"),
    float_flag: bool = typer.Option(False, "--float", "-f", help="Value to be parsed as a float"),
):
    """Update a Node Template's general attribute.

    Example:

    > labby update node template -t "Arista EOS vEOS 4.25F" --int ram 2048
    """
    parsed_value = parse_value(value, bool_flag, int_flag, float_flag)

    provider = config.get_provider()
    tplt = provider.search_template(template_name)
    if not tplt:
        utils.console.log(f"Node Template [cyan i]{template_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Update node template
    tplt.update(**{attr: parsed_value})
    utils.console.log(tplt)


@link_app.command(name="filter", short_help="Updates a link filter")
def link_filter(
    attr: LinkFilter = typer.Argument(..., help="Filter to apply to the link"),
    value: str = typer.Argument(..., help="Value of Link Filter to apply to the link"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_a: str = typer.Option(..., "--node-a", "-na", help="Node name from ENDPOINT A"),
    port_a: str = typer.Option(..., "--port-a", "-pa", help="Port name from node on ENDPOINT A"),
    node_b: str = typer.Option(..., "--node-b", "-nb", help="Node name from ENDPOINT B"),
    port_b: str = typer.Option(..., "--por-b", "-pb", help="Port name from node on ENDPOINT B"),
    bool_flag: bool = typer.Option(False, "--bool", "-b", help="Value to be parsed as a boolean"),
    int_flag: bool = typer.Option(False, "--int", "-i", help="Value to be parsed as an integer"),
    float_flag: bool = typer.Option(False, "--float", "-f", help="Value to be parsed as a float"),
):
    """Update a Link Filter.

    The filter applied are dependant on the underlying Network lab provider.
    By default we are setting GNS3 filter types capabilities to be used on the link.

    Example:

    > labby update link filter -p lab01 -na r1 -pa Ethernet2 -nb r2 -pb Ethernet2 --int packet_loss 77
    """
    parsed_value = parse_value(value, bool_flag, int_flag, float_flag)

    filters: Dict[str, Any] = dict({attr: parsed_value})

    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    enlace = prj.search_link(node_a, port_a, node_b, port_b)
    if not enlace:
        utils.console.log(
            f"Link [cyan i]{node_a}: {port_a} == {node_b}: {port_b}[/] not found. Nothing to do...", style="error"
        )
        raise typer.Exit(1)

    # Update link
    enlace.apply_metric(**filters)
    utils.console.log(enlace)
