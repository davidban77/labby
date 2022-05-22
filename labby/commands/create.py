"""Labby create command.

Handles all creation of labby resources.

Example:
> labby create --help
"""
from enum import Enum
from typing import Any, Dict, List, Optional

import typer

from labby import utils, config


app = typer.Typer(help="Creates a Resource on Network Provider Lab")


class LinkFilter(str, Enum):
    """Link Filter Enum."""

    # pylint: disable=invalid-name
    frequency_drop = "frequency_drop"
    packet_loss = "packet_loss"
    latency = "latency"
    jitter = "jitter"
    corrupt = "corrupt"
    bpf_expression = "bpf_expression"


@app.command(short_help="Creates a project")
def project(
    project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT"),
    label: Optional[List[str]] = typer.Option(None, help="Add labels to created project"),
):
    """
    Creates a Project and optionally lets you associate it with labels.

    Example:

    > labby create project lab01 --label mpls --label v0.1.0
    """
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] already created. Nothing to do...", style="error")
        raise typer.Exit(1)
    labels = [] if not label else label

    # Create project
    prj = provider.create_project(project_name=project_name, labels=labels)
    utils.console.log(prj)


@app.command(short_help="Creates a node")
def node(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    template_name: str = typer.Option(..., "--template", "-t", help="Node template"),
    mgmt_port: Optional[str] = typer.Option(None, help="Management Interface used on the device"),
    mgmt_addr: Optional[str] = typer.Option(None, help="IP Prefix to configure on mgmt_port. i.e. 192.168.77.77/24"),
    label: Optional[List[str]] = typer.Option(None, help="Add labels to created node"),
):
    """
    Creates a Node and optionally lets you associate it with labels, management port and address.

    Example:

    > labby create node r1 --project lab01 --template "Arista EOS vEOS 4.25.0FX" --label mpls_pe

    To verify available node templates you can run:

    > labby get node template-list
    """
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    labels = [] if not label else label

    # Create node
    device = prj.create_node(
        name=node_name, template=template_name, labels=labels, mgmt_port=mgmt_port, mgmt_addr=mgmt_addr
    )
    utils.console.log(device)


@app.command(short_help="Creates a link")
def link(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_a: str = typer.Option(..., "--node-a", "-na", help="Node name from ENDPOINT A"),
    port_a: str = typer.Option(..., "--port-a", "-pa", help="Port name from node on ENDPOINT A"),
    node_b: str = typer.Option(..., "--node-b", "-nb", help="Node name from ENDPOINT B"),
    port_b: str = typer.Option(..., "--port-b", "-pb", help="Port name from node on ENDPOINT B"),
    filter_type: Optional[LinkFilter] = typer.Option(None, help="Filter to apply to the link"),
    filter_value: Optional[str] = typer.Option(None, help="Value of Link Filter to apply to the link"),
    label: Optional[List[str]] = typer.Option(None, help="Add labels to created link"),
):
    """
    Creates a Link and optionally lets you associate it with labels.

    Example:

    > labby create link --project lab01 -na r1 -pa Ethernet1 -nb r2 -pb Ethernet1 --label backbone
    """
    filters: Optional[Dict[str, Any]] = None
    if filter_type and filter_value:
        if filter_type != "bpf_expression":
            filters = dict({filter_type: int(filter_value)})
        else:
            filters = dict({filter_type: filter_value})
    provider = config.get_provider()
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    labels = [] if not label else label

    # Create link
    enlace = prj.create_link(node_a, port_a, node_b, port_b, filters=filters, labels=labels)
    utils.console.log(enlace)
