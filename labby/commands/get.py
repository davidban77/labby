"""Labby get command.

Handles all get/retrive information actions of labby resources.

Example:
> labby get --help
"""
from pathlib import Path
from enum import Enum
from typing import List, Optional

import typer

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
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log()
    utils.console.log(project.render_nodes_summary())
    utils.console.log()
    utils.console.log(project.render_links_summary())
    project.to_initial_state()


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
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log()
    utils.console.log(project.render_nodes_summary(field=nfilter, value=value, labels=labels))
    project.to_initial_state()


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
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    node = project.search_node(name=node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log(node)
    utils.console.log()
    utils.console.log(node.render_ports_detail())
    utils.console.log()
    utils.console.log(node.render_links_detail())
    if properties:
        utils.console.log()
        utils.console.log(node.render_properties())
    project.to_initial_state()


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
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    node = project.search_node(name=node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log(node)

    if not console:
        if node.nornir:
            utils.console.log(node.nornir.inventory.hosts[node.name].connection_options)

        config_text = node.get_config()
    else:
        config_text = node.get_config_over_console(user=user, password=password)

    if save and config_text:
        save.write_text(config_text)
        utils.console.log(
            f"[b]({project.name})({node.name})[/] Saved configuration to: {save.absolute()}", style="good"
        )


@node_app.command(short_help="Retrieves details of a node template", name="template-detail")
def node_template_detail(
    template_name: str = typer.Option(..., "--template", "-t", help="Node Template name"),
):
    """
    Retrieves Node Template details.

    Example:

    > labby get node template-detail --template "Arista EOS vEOS 4.25F"
    """
    provider = config.get_provider()
    template = provider.search_template(template_name=template_name)
    if not template:
        utils.console.log(f"Node Template [cyan i]{template_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log(template)


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
    provider = config.get_provider()
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)
    utils.console.log()
    utils.console.log(project.render_links_summary(field=lfilter, value=value, labels=labels))
    project.to_initial_state()


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
    provider = config.get_provider()
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
    utils.console.log(link)
    project.to_initial_state()
