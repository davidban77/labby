"""GNS3 Node Console provisioner module based on Scrapli and Telnet transport."""
from __future__ import annotations
from scrapli.exceptions import ScrapliTimeout
import typer
import time
from labby import utils
from scrapli.driver.core import (
    IOSXEDriver,
    EOSDriver,
    IOSXRDriver,
    NXOSDriver,
    JunosDriver,
)
from scrapli.response import Response as ScrapliResponse
from scrapli.transport.telnet import TelnetTransport
from typing import Any, Dict, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from labby.providers.gns3.node import GNS3Node


RUN_ACTIONS = Literal["command", "bootstrap", "config"]


DRIVER = {
    "cisco_ios": IOSXEDriver,
    "arista_eos": EOSDriver,
    "cisco_nxos": NXOSDriver,
    "cisco_xr": IOSXRDriver,
    "juniper_junos": JunosDriver,
}

BOOTSTRAP_SETTINGS = {
    "cisco_ios": {
        "auth_bypass": False,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 2,
    },
    "arista_eos": {
        "auth_bypass": False,
        "auth_username": "admin",
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 2,
    },
    "cisco_nxos": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 2,
    },
    "cisco_xr": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 2,
    },
    "juniper_junos": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 2,
    },
}


def cisco_ios_boot(server_host: str, model: str, console: int, node_name: str, project_name: str):
    """Bootstrap actions for Cisco IOS devices.

    Args:
        server_host (str): GNS3 server address.
        model (str): GNS3 Node model.
        console (int): GNS3 telnet port number for node's console.
        node_name (str): GNS3 node name.
        project_name (str): GNS3 Project name.

    Raises:
        typer.Exit: When an error has been found on config dialog
    """
    utils.console.log(f"[b]({project_name})({node_name})[/] Using Telnet transport for model {model}")
    telnet_session = TelnetTransport(
        host=server_host,
        port=console,
        comms_return_char="\r\n",
        auth_bypass=True,
    )
    telnet_session.open()
    if "csr" in model:
        response = telnet_session.session.expect([b" initial configuration dialog"], timeout=190)
        if response[0] == -1:
            utils.console.log(f"[b]({project_name})({node_name})[/] Error found on config dialog")
            raise typer.Exit(1)
        telnet_session.session.write(b"no\n")
        telnet_session.session.write(b"yes\n")
        time.sleep(10)
    else:
        response = telnet_session.session.expect([b"Press RETURN to get started"], timeout=190)
        telnet_session.session.write(b"\r\n")
        utils.console.log(f"[b]({project_name})({node_name})[/] Sent enter command...")
    telnet_session.close()


def arista_eos_boot(node_name: str, project_name: str, server_host: str, console: int):
    """Bootstrap actions for Arista EOS devices.

    Args:
        node_name (str): GNS3 node name.
        project_name (str): GNS3 Project name.
        server_host (str): GNS3 server address.
        console (int): GNS3 telnet port number for node's console.
    """
    # Independent telnet session to disable ZTP
    telnet_session = TelnetTransport(
        host=server_host, port=console, auth_username="admin", timeout_transport=120, timeout_ops=120
    )
    telnet_session.username_prompt = "localhost login:"
    telnet_session.password_prompt = "localhost>"
    telnet_session.open()
    response = telnet_session.session.expect([b"ZeroTouch"], timeout=30)
    # Verify if match on ZTP
    if response[1]:
        utils.console.log(f"[b]({project_name})({node_name})[/] Disabling ZTP")
        telnet_session.session.write(b"zerotouch disable\r\n")
        response = telnet_session.session.expect(
            [b"Welcome to Arista Networks", b"Loading linux", b"Starting ProcMgr"], timeout=30
        )
        if response[1] is None:
            utils.console.log("Not found a reloading message")
        utils.console.log(f"[b]({project_name})({node_name})[/] Reloading device...")
        time.sleep(20)
    telnet_session.close()


def set_node_console_settings(node: GNS3Node, server_host: str) -> Dict[str, Any]:
    """Set node console transport settings to connect against GNS3 server.

    Args:
        node (GNS3Node): GNS3 node.
        server_host (str): GNS3 server address.

    Raises:
        typer.Exit: When node.console, node.net_os or node.model are not set.

    Returns:
        Dict[str, Any]: Node console transport settings.
    """
    if node.console is None or node.model is None or node.net_os is None:
        node.get()
        if node.console is None:
            utils.console.log(f"[b]({node.project.name})({node.name})[/] Node console needs to be set", style="error")
            raise typer.Exit(1)
        if node.model is None:
            utils.console.log(f"[b]({node.project.name})({node.name})[/] Node model needs to be set", style="error")
            raise typer.Exit(1)
        if node.net_os is None:
            utils.console.log(f"[b]({node.project.name})({node.name})[/] Node net_os needs to be set", style="error")
            raise typer.Exit(1)

    # Update console settings with server host and port
    node_console_settings = BOOTSTRAP_SETTINGS[node.net_os]
    node_console_settings.update(host=server_host, port=node.console)
    return node_console_settings


def run_bootstrap(
    node_console_settings: Dict[str, Any], server_host: str, config: str, node: GNS3Node
) -> ScrapliResponse:
    """Execute Bootrap configuration steps for a specific GNS3Node.

    Args:
        server_host (str): GNS3 server address.
        config (str): Node configuration to send.
        node (GNS3Node): GNS3 node.

    Raises:
        typer.Exit: When node.net_os is not supported

    Returns:
        bool: True if executed succesfully, else False
    """
    # Boot process per device type
    with utils.console.status(
        f"[b]({node.project.name})({node.name})[/] Running initial boot sequence", spinner="aesthetic"
    ) as status:

        if node.net_os == "arista_eos":
            arista_eos_boot(
                node_name=node.name,
                project_name=node.project.name,
                server_host=server_host,
                console=node.console,  # type: ignore
            )

            node_console_settings.update(timeout_ops=120, timeout_transport=120)
            connector = EOSDriver(**node_console_settings)

            # Setting prompts for initiating the device
            connector.transport.username_prompt = "localhost login:"
            connector.transport.password_prompt = "localhost>"

            # Re-authenticating
            try:
                utils.console.log(f"[b]({node.project.name})({node.name})[/] Authenticating to console...")
                connector.open()
            except ScrapliTimeout:
                try:
                    utils.console.log(f"[b]({node.project.name})({node.name})[/] Attempting to connect to terminal...")
                    connector.transport.auth_bypass = True
                    connector.open()
                except ScrapliTimeout as err:
                    utils.console.log(
                        f"[b]({node.project.name})({node.name})[/] Console connection timed out: {err}", style="error"
                    )
                    raise typer.Exit(1)

        elif node.net_os == "cisco_ios":
            cisco_ios_boot(
                server_host=server_host,
                model=node.model,  # type: ignore
                console=node.console,  # type: ignore
                node_name=node.name,
                project_name=node.project.name,
            )

            node_console_settings.update(timeout_ops=60, timeout_transport=60)
            connector = IOSXEDriver(**node_console_settings)

            # Re-authenticating
            try:
                utils.console.log(f"[b]({node.project.name})({node.name})[/] Authenticating to console...")
                connector.open()
            except ScrapliTimeout:
                try:
                    utils.console.log(f"[b]({node.project.name})({node.name})[/] Attempting to connect to terminal...")
                    connector.transport.auth_bypass = True
                    connector.open()
                except ScrapliTimeout as err:
                    utils.console.log(
                        f"[b]({node.project.name})({node.name})[/] Console connection timed out: {err}", style="error"
                    )
                    raise typer.Exit(1)

        else:
            utils.console.log(
                f"[b]({node.project.name})({node.name})[/] Node OS not supported {node.net_os}", style="error"
            )
            raise typer.Exit(1)

        # Get response and send result status flag
        status.update(status=f"[b]({node.project.name})({node.name})[/] Pushing bootstrap configuration...")
        response = connector.send_config(config=config)
        return response


def run_action(
    action: RUN_ACTIONS,
    server_host: str,
    data: str,
    node: GNS3Node,
    user: Optional[str] = None,
    password: Optional[str] = None,
) -> ScrapliResponse:
    """Execute a command on the device via console transport.

    Args:
        server_host (str): GNS3 server address.
        command (str): Node command to send.
        node (GNS3Node): GNS3 node.

    Raises:
        typer.Exit: When node.net_os is not supported

    Returns:
        str: Result of command executed.
    """
    # Get scrapli connector object
    node_console_settings = set_node_console_settings(node=node, server_host=server_host)
    node_console_settings.update(host=server_host, port=node.console)

    if action == "bootstrap":
        return run_bootstrap(
            node_console_settings=node_console_settings, server_host=server_host, config=data, node=node
        )

    if user:
        node_console_settings["auth_username"] = user
    if password:
        node_console_settings["auth_password"] = password
        node_console_settings["auth_bypass"] = False

    # Connection to device
    with utils.console.status(
        f"[b]({node.project.name})({node.name})[/] Sending command over console", spinner="aesthetic"
    ) as status:

        if node.net_os == "arista_eos":
            connector = EOSDriver(**node_console_settings)
            try:
                status.update(status=f"[b]({node.project.name})({node.name})[/] Attempting authentication...")
                connector.transport.username_prompt = "login:"
                if password:
                    connector.transport.password_prompt = "Password:"
                else:
                    connector.transport.password_prompt = ">"
                connector.open()
            except ScrapliTimeout:
                try:
                    status.update(
                        status=f"[b]({node.project.name})({node.name})[/] Attempting to connect to terminal..."
                    )
                    connector.transport.auth_bypass = True
                    connector.open()
                except ScrapliTimeout as err:
                    utils.console.log(
                        f"[b]({node.project.name})({node.name})[/] Console connection timed out: {err}", style="error"
                    )
                    raise typer.Exit(1)

        elif node.net_os == "cisco_ios":
            connector = IOSXEDriver(**node_console_settings)
            try:
                status.update(status=f"[b]({node.project.name})({node.name})[/] Attempting authentication...")
                connector.open()
            except ScrapliTimeout:
                try:
                    status.update(
                        status=f"[b]({node.project.name})({node.name})[/] Attempting to connect to terminal..."
                    )
                    connector.transport.auth_bypass = True
                    connector.open()
                except ScrapliTimeout as err:
                    utils.console.log(
                        f"[b]({node.project.name})({node.name})[/] Console connection timed out: {err}", style="error"
                    )
                    raise typer.Exit(1)

        else:
            utils.console.log(
                f"[b]({node.project.name})({node.name})[/] Node OS not supported {node.net_os}", style="error"
            )
            raise typer.Exit(1)

        # Push config
        utils.console.log(f"[b]({node.project.name})({node.name})[/] Sending {action}...")

        # Get response and send result status flag
        status.update(status=f"[b]({node.project.name})({node.name})[/] Sending {action}...")
        if action == "command":
            response = connector.send_command(command=data, timeout_ops=60)
        else:
            response = connector.send_config(config=data, timeout_ops=60)

        connector.close()
        return response
