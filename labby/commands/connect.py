"""Labby connect command.

Handles methods and command to connect to labby resources.

Example:
> labby connect --help
"""
import os
from netaddr.ip import IPNetwork
import typer
from labby import utils, config


app = typer.Typer(help="Connects to a Network Resource")


@app.command(short_help="Connects to a node via SSH or Telnet/Console.")
def node(
    node_name: str = typer.Argument(..., help="Node name."),
    project_name: str = typer.Option(..., "--project", "-p", help="Project name", envvar="LABBY_PROJECT"),
    user: str = typer.Option(None, "--user", "-u", help="Node user", envvar="LABBY_NODE_USER"),
    console: bool = typer.Option(False, "--console", "-c", help="Apply configuration over console"),
):
    """
    Connects to a Node bia SSH (default and if applicable) or Telnet console.

    For console connection to work, you must have a Telnet client installed.

    Example:

    > labby connect node r1 -p lab01 --user netops --password netops123
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    project = provider.search_project(project_name=project_name)
    if not project:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    # Get node to connect
    node = project.search_node(node_name)
    if not node:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    if node.mgmt_addr is None and console is False:
        utils.console.log(
            f"Node [cyan i]{node_name}[/] mgmt_addr parameter must be set. Run update command", style="error"
        )
        raise typer.Exit(code=1)

    if not user and not console:
        utils.console.log("Parameter '--user' must be set", style="error")
        raise typer.Exit(code=1)

    # Connect to node
    if console:
        server_host = utils.dissect_url(node._base._connector.base_url)[1]  # type: ignore
        os.system(f"telnet {server_host} {node.console}")
    else:
        os.system(f"ssh {user}@{IPNetwork(node.mgmt_addr).ip}")
