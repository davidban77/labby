"""Labby Nornir Inventory Plugin."""
from typing import Any, Dict

from ipaddress import IPv4Interface
from nornir.core.inventory import Inventory, Hosts, Host, Groups, ConnectionOptions, Defaults
from nornir.core.plugins.inventory import InventoryPlugin

from labby.models import LabbyProject


def _set_host(data: Dict[str, Any], name: str, groups, host, host_platform) -> Host:
    """Creates Nornir Hosts object from data passed.

    Args:
        data (Dict[str, Any]): Host data returned to Nornir
        name (str): Host name
        groups (_type_): Groups for hosts
        host (_type_): Host object
        host_platform (_type_): Host platform

    Returns:
        Host: Nornir Host
    """
    connection_option = {
        "scrapli": ConnectionOptions(
            port=host.get("port", 22),
            username=host.get("username", "netops"),
            password=host.get("password", "netops123"),
            platform=host_platform,
            extras=host.get("extras", {"auth_strict_key": False}),
        )
    }

    return Host(
        name=name,
        hostname=host["hostname"],
        username=host.get("username"),
        password=host.get("password"),
        platform=host_platform,
        data=data,
        groups=groups,
        connection_options=connection_option,
    )


class LabbyNornirInventory(InventoryPlugin):
    # pylint: disable=too-few-public-methods
    """Labby Nornir Inventory."""

    def __init__(self, project: LabbyProject) -> None:
        """Labby Nornir Inventory Plugin which uses a LabbyProject.

        Args:
            project (LabbyProject): Labby Project.
        """
        self.project = project

    def load(self) -> Inventory:
        """Loads inventory data.

        Returns:
            Inventory: Nornir Inventory
        """
        hosts = Hosts()
        groups = Groups()
        defaults = Defaults()

        for _, node in self.project.nodes.items():
            host: Dict[Any, Any] = {"data": {}}

            host["data"]["labby_obj"] = node

            host["data"]["labby_dict"] = node.dict()

            host["hostname"] = str(IPv4Interface(node.mgmt_addr).ip) if node.mgmt_addr else node.name

            host["name"] = node.name

            host["groups"] = []

            host_platform = node.net_os if node.net_os != "cisco_ios" else "cisco_iosxe"

            hosts[node.name] = _set_host(
                data=host["data"], name=host["name"], groups=host["groups"], host=host, host_platform=host_platform
            )

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)
