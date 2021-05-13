from __future__ import annotations
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
from scrapli.transport.telnet import TelnetTransport
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from labby.providers.gns3.node import GNS3Node


DRIVER = {
    "cisco_ios": IOSXEDriver,
    "arista_eos": EOSDriver,
    "cisco_nxos": NXOSDriver,
    "cisco_xr": IOSXRDriver,
    "juniper_junos": JunosDriver,
}

BOOTSTRAP_SETTINGS = {
    "cisco_ios": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 190,
        # "host": host,
        # "port": port,
    },
    "arista_eos": {
        "auth_bypass": False,
        "auth_username": "admin",
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 190,
        # "host": host,
        # "port": port,
    },
    "cisco_nxos": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 190,
        # "host": host,
        # "port": port,
    },
    "cisco_xr": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 190,
        # "host": host,
        # "port": port,
    },
    "juniper_junos": {
        "auth_bypass": True,
        "transport": "telnet",
        "comms_return_char": "\r\n",
        "timeout_ops": 190,
        # "host": host,
        # "port": port,
    },
}


def cisco_ios_boot(
    connector: IOSXEDriver, server_host: str, model: str, console: int, node_name: str, project_name: str
):
    if "csr" in model:
        utils.console.log(f"[b]({project_name})({node_name})[/] Using Telnet transport for model {model}")
        telnet_session = TelnetTransport(
            host=server_host,
            port=console,
            comms_return_char="\r\n",
            auth_bypass=True,
        )
        telnet_session.open()
        response = telnet_session.session.expect([b" initial configuration dialog"], timeout=190)
        if response[0] == -1:
            utils.console.log(f"[b]({project_name})({node_name})[/] Error found on config dialog")
            raise typer.Exit(1)
        telnet_session.session.write(b"no\n")
        telnet_session.session.write(b"yes\n")
        time.sleep(10)
    utils.console.log(f"[b]({project_name})({node_name})[/] Opening console connection...")
    connector.open()
    utils.console.log(f"[b]({project_name})({node_name})[/] Console connection opened", style="good")


def arista_eos_boot(connector: EOSDriver, node_name: str, project_name: str, server_host: str, console: int):
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
            utils.console.log("Not found a reloading messages")
        utils.console.log(f"[b]({project_name})({node_name})[/] Reloading device...")
        time.sleep(20)
    else:
        telnet_session.close()
    # Setting prompts for initiating the device
    connector.transport.username_prompt = "localhost login:"
    connector.transport.password_prompt = "localhost>"

    # Re-authenticating
    utils.console.log(f"[b]({project_name})({node_name})[/] Re-opening console connection...")
    connector.open()
    utils.console.log(f"[b]({project_name})({node_name})[/] Console connection opened", style="good")


def bootstrap(server_host: str, config: str, node: GNS3Node) -> bool:
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

    # Get scrapli connector object
    node_console_settings = BOOTSTRAP_SETTINGS[node.net_os]
    node_console_settings.update(host=server_host, port=node.console)
    node_console_conn = DRIVER[node.net_os](**node_console_settings)

    # Boot process per device type
    with utils.console.status(
        f"[b]({node.project.name})({node.name})[/] Running initial boot sequence", spinner="aesthetic"
    ) as status:
        if node.net_os == "arista_eos":
            arista_eos_boot(
                connector=node_console_conn,
                node_name=node.name,
                project_name=node.project.name,
                server_host=server_host,
                console=node.console,
            )
        elif node.net_os == "cisco_ios":
            cisco_ios_boot(
                connector=node_console_conn,
                server_host=server_host,
                model=node.model,
                console=node.console,
                node_name=node.name,
                project_name=node.project.name,
            )

        # Push config
        utils.console.log(f"[b]({node.project.name})({node.name})[/] Pushing bootstrap configuration...")

        # Get response and send result status flag
        status.update(status=f"[b]({node.project.name})({node.name})[/] Pushing bootstrap configuration...")
        response = node_console_conn.send_config(config=config)
        return not response.failed
