import re
import time
import gns3fy
from labby.utils import console
import labby.models as models
from pathlib import Path
from typing import Tuple, Optional
from scrapli.driver import NetworkDriver
from scrapli.driver.core import (
    IOSXEDriver,
    EOSDriver,
    IOSXRDriver,
    NXOSDriver,
    JunosDriver,
)
from scrapli.transport.telnet import TelnetTransport


def dissect_url(target: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Takes URL and returns protocol, destination and resource.

    Example:
    >>> dissect_url("https://api.test.com/v2/resourceX")
    ("https", "api.test.com", "v2/resourceX")
    """
    match = re.search(
        r"((?P<protocol>\w+?)://)?(?P<destination>(\w+(-\w+)?\.?)+[a-z|0-9]+):?"
        r"(?P<port>\d+)?(/(?P<resource>[a-z]+\S+))?",
        target,
    )
    if match is None:
        raise ValueError(f"Could not dissect URL: {target}")
    return (
        match.groupdict().get("protocol"),
        match.groupdict().get("destination"),
        match.groupdict().get("resource"),
    )


def bootstrap_settings(device_type: str, host: str, port: int) -> NetworkDriver:
    settings = {
        "cisco_iosxe": {  # NOTE: Works on IOSv
            "auth_bypass": True,
            "transport": "telnet",
            "comms_return_char": "\r\n",
            "timeout_ops": 190,
            "host": host,
            "port": port,
        },
        "arista_eos": {
            "auth_bypass": False,
            "auth_username": "admin",
            "transport": "telnet",
            "comms_return_char": "\r\n",
            "timeout_ops": 190,
            "host": host,
            "port": port,
        },
        "cisco_nxos": {
            "auth_bypass": True,
            "transport": "telnet",
            "comms_return_char": "\r\n",
            "timeout_ops": 190,
            "host": host,
            "port": port,
        },
        "cisco_iosxr": {
            "auth_bypass": True,
            "transport": "telnet",
            "comms_return_char": "\r\n",
            "timeout_ops": 190,
            "host": host,
            "port": port,
        },
        "juniper_junos": {
            "auth_bypass": True,
            "transport": "telnet",
            "comms_return_char": "\r\n",
            "timeout_ops": 190,
            "host": host,
            "port": port,
        },
    }
    driver = {
        "cisco_iosxe": IOSXEDriver,
        "arista_eos": EOSDriver,
        "cisco_nxos": NXOSDriver,
        "cisco_iosxr": IOSXRDriver,
        "juniper_junos": JunosDriver,
    }
    return driver[device_type](**settings[device_type])


class Provision:
    def __init__(self, server: gns3fy.Gns3Connector) -> None:
        self.server = server

    def cisco_iosxe_boot(
        self, connector: IOSXEDriver, node: models.Node, server_host: str
    ):
        if node._provider is None or node.console is None:
            raise ValueError("GNS3 Node must be initialized")
        image = node._provider.properties.get("hda_disk_image")
        if "csr1000v" in image:
            telnet_session = TelnetTransport(
                host=server_host,
                port=node.console,
                comms_return_char="\r\n",
                auth_bypass=True,
            )
            telnet_session.open()
            response = telnet_session.session.expect(
                [b" initial configuration dialog"], timeout=190
            )
            if response[0] == -1:
                raise ValueError("Error found on config dialog")
            telnet_session.session.write(b"no\n")
            telnet_session.session.write(b"yes\n")
            time.sleep(10)
        console.log("Opening console connection...")
        connector.open()

    def arista_eos_boot(
        self, connector: EOSDriver, node: models.Node, server_host: str
    ):
        # Setting prompts for initiating the device
        connector.transport.username_prompt = "localhost login:"
        connector.transport.password_prompt = "localhost>"
        console.log("Opening console connection...")
        connector.open()

        # Disable ZTP
        console.log("Disabling ZTP")
        response = connector.send_command("zerotouch disable")
        if response.failed:
            raise ValueError("Error disabling ZTP")
        console.log("Reloading device...")
        time.sleep(20)

        # Re-authenticating
        console.log("Re-opening console connection...")
        connector.open()

    def bootstrap(
        self, node: models.Node, project: models.Project, config: Path, device_type: str
    ) -> bool:
        if node.console is None:
            raise ValueError("Node needs console port")
        server_host = dissect_url(self.server.base_url)[1]
        if server_host is None:
            raise ValueError("Could not get GNS3 server from url")

        # Get scrapli connector object
        node_console_conn = bootstrap_settings(
            device_type=device_type, host=server_host, port=node.console
        )

        # Boot process per device type
        getattr(self, f"{device_type}_boot")(
            connector=node_console_conn, node=node, server_host=server_host
        )

        # Push config
        console.log("Pushing bootstrap configuration...")

        # Get response and send result status flag
        response = node_console_conn.send_config(config=config.read_text())
        return not response.failed
