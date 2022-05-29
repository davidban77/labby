"""Labby get command.

Handles all get/retrive information actions of labby resources.

Example:
> labby get --help
"""
from pathlib import Path
from enum import Enum
from typing import List, Optional

import typer

from labby.commands.common import (
    get_labby_objs_from_link,
    get_labby_objs_from_node,
    get_labby_objs_from_node_template,
    get_labby_objs_from_project,
)
from labby import utils, config


app = typer.Typer(help="Retrieves information on resources of a Network Provider Lab")
project_app = typer.Typer(help="Retrieves Lab Projects Resources")
node_app = typer.Typer(help="Retrieves Lab Nodes Resources")
link_app = typer.Typer(help="Retrieves Lab Links Resources")

app.add_typer(project_app, name="project")
app.add_typer(node_app, name="node")
app.add_typer(link_app, name="link")


class ProjectFilter(str, Enum):
    """Project Filter enum."""

    # pylint: disable=invalid-name
    status = "status"
    auto_start = "auto_start"
    auto_open = "auto_open"
    auto_close = "auto_close"


class NodeFilter(str, Enum):
    """Node Filter enum."""

    # pylint: disable=invalid-name
    node_type = "node_type"
    category = "category"
    status = "status"


@project_app.command(name="list", short_help="Retrieves summary list of projects")
def project_list(
    pfilter: Optional[ProjectFilter] = typer.Option(
        None, "--filter", "-f", help="Attribute name to filter on. Works with `--value`"
    ),
    value: Optional[str] = typer.Option(
        None, "--value", "-v", help="Attribute value to filter on. Works with `--filter`"
    ),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to filter on."),
):
    """
    Retrieve a summary list of projects configured on server.

    Example:

    > labby get project list --filter status --value opened

    Or based on labels

    > labby get project list --label telemetry --label test
    """
    provider = config.get_provider()
    utils.console.log(provider.render_project_list(field=pfilter, value=value, labels=labels))


@project_app.command(short_help="Retrieves details of a project", name="detail")
def project_detail(
    project_name: str = typer.Argument(..., help="Project name", envvar="LABBY_PROJECT"),
):
    """
    Retrieves Project details.

    Example:

    > labby get project detail lab01
    """
    # Get Labby objects from project definition
    _, prj = get_labby_objs_from_project(project_name=project_name)

    utils.console.log()
    utils.console.log(prj.render_nodes_summary())
    utils.console.log()
    utils.console.log(prj.render_links_summary())
    prj.to_initial_state()


@node_app.command(name="list", short_help="Retrieves summary list of nodes in a project")
def node_list(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    nfilter: Optional[NodeFilter] = typer.Option(
        None, "--filter", "-f", help="Attribute name to filter on. Works with `--value`"
    ),
    value: Optional[str] = typer.Option(
        None, "--value", "-v", help="Attribute value to filter on. Works with `--filter`"
    ),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to filter on."),
):
    """
    Retrieve a summary list of nodes configured on a project.

    Example:

    > labby get node list --project lab01 --filter status --value started

    Or based on labels

    > labby get node list --project lab01 --label edge --label mgmt
    """
    # Get Labby objects from project definition
    _, prj = get_labby_objs_from_project(project_name=project_name)

    utils.console.log()
    utils.console.log(prj.render_nodes_summary(field=nfilter, value=value, labels=labels))
    prj.to_initial_state()


@node_app.command(name="template-list", short_help="Retrieves summary list of node templates in a Provider")
def node_template_list(
    nfilter: Optional[NodeFilter] = typer.Option(None, help="If used you MUST provide expected `--value`"),
    value: Optional[str] = typer.Option(None, help="Value to be used with `--filter`"),
):
    """
    Retrieve a summary list of node templates configured on a provider.

    Example:

    > labby get node template-list
    """
    provider = config.get_provider()
    utils.console.log(provider.render_templates_list(field=nfilter, value=value))


@node_app.command(short_help="Retrieves details of a node", name="detail")
def node_detail(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    properties: bool = typer.Option(False, "--properties", "-o", help="Show node properties"),
):
    """
    Retrieves Node details.

    Example:

    > labby get node detail --project lab01 --node r1
    """
    # Get Labby objects from project and node definition
    _, prj, device = get_labby_objs_from_node(project_name=project_name, node_name=node_name)

    utils.console.log(device)
    utils.console.log()
    utils.console.log(device.render_ports_detail())
    utils.console.log()
    utils.console.log(device.render_links_detail())
    if properties:
        utils.console.log()
        utils.console.log(device.render_properties())
    prj.to_initial_state()


@node_app.command(short_help="Retrieves node running configuration", name="config")
def node_config(
    node_name: str = typer.Argument(..., help="Node name"),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    console: bool = typer.Option(False, "--console", "-c", help="Retrieve configuration over console"),
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="User to use for the node connection", envvar="LABBY_NODE_USER"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-w", help="Password to use for the node connection", envvar="LABBY_NODE_PASSWORD"
    ),
    save: Optional[Path] = typer.Option(None, "--save", "-s", help="Save configuration to file specified"),
):
    """Retrieve node running configuration.

    By default, the configuration is retrieved over the node mgmt_port. If you want to retrieve the configuration over
    console, you can use the `--console` option.

    Example:

    > labby get node detail r1 --project lab01 --user netops --save /tmp/config.txt
    """
    # Get Labby objects from project and node definition
    _, prj, device = get_labby_objs_from_node(project_name=project_name, node_name=node_name)
    utils.console.log(device)

    if not console:
        if device.nornir:
            utils.console.log(device.nornir.inventory.hosts[device.name].connection_options)

        config_text = device.get_config()
    else:
        config_text = device.get_config_over_console(user=user, password=password)

    if save and config_text:
        save.write_text(config_text)
        utils.console.log(f"[b]({prj.name})({device.name})[/] Saved configuration to: {save.absolute()}", style="good")


@node_app.command(short_help="Retrieves details of a node template", name="template-detail")
def node_template_detail(
    template_name: str = typer.Option(..., "--template", "-t", help="Node Template name"),
):
    """
    Retrieves Node Template details.

    Example:

    > labby get node template-detail --template "Arista EOS vEOS 4.25F"
    """
    # Get Labby objects from node's template
    _, tplt = get_labby_objs_from_node_template(template_name=template_name)

    utils.console.log(tplt)


@link_app.command(name="list", short_help="Retrieves summary list of links in a project")
def link_list(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    lfilter: Optional[str] = typer.Option(
        None, "--filter", "-f", help="Attribute name to filter on. Works with `--value`"
    ),
    value: Optional[str] = typer.Option(
        None, "--value", "-v", help="Attribute value to filter on. Works with `--filter`"
    ),
    labels: Optional[List[str]] = typer.Option(None, "--label", "-l", help="Labels to filter on."),
):
    """
    Retrieve a summary list of links configured on a project.

    Example:

    > labby get link list --project lab01

    Or based on labels

    > labby get link list --project lab01 --label inter-dc
    """
    # Get Labby objects from project definition
    _, prj = get_labby_objs_from_project(project_name=project_name)

    utils.console.log()
    utils.console.log(prj.render_links_summary(field=lfilter, value=value, labels=labels))
    prj.to_initial_state()


@link_app.command(short_help="Retrieves details of a link", name="detail")
def link_detail(
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    node_a: str = typer.Option(..., "--node-a", "-na", help="Node name from ENDPOINT A"),
    port_a: str = typer.Option(..., "--port-a", "-pa", help="Port name from node on ENDPOINT A"),
    node_b: str = typer.Option(..., "--node-b", "-nb", help="Node name from ENDPOINT B"),
    port_b: str = typer.Option(..., "--port-b", "-pb", help="Port name from node on ENDPOINT B"),
):
    """
    Retrieves details of a link.

    Example:

    > labby get link detail --project lab01 -na r1 -pa Ethernet1 -nb r2 -pb Ethernet1
    """
    # Get Labby objects from project and link definition
    _, prj, enlace = get_labby_objs_from_link(
        project_name=project_name,
        node_a=node_a,
        port_a=port_a,
        node_b=node_b,
        port_b=port_b,
    )

    utils.console.log(enlace)
    prj.to_initial_state()
