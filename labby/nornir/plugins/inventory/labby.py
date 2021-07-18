from ipaddress import IPv4Interface
from typing import Any, Dict
from labby.models import LabbyProject
from nornir.core.inventory import Inventory, Hosts, Host, Groups, ConnectionOptions, Defaults
from nornir.core.plugins.inventory import InventoryPlugin


def _set_host(data: Dict[str, Any], name: str, groups, host, host_platform) -> Host:
    # connection_option: Dict[str, Any] = {"scrapli": {"extras": {"auth_strict_key": False}}}
    # for key, value in data.get("connection_options", {}).items():
    #     connection_option[key] = ConnectionOptions(
    #         # hostname=value.get("hostname"),
    #         hostname=host["hostname"],
    #         # port=value.get("port"),
    #         port=value.get("port", 22),
    #         # username=value.get("username"),
    #         username=host.get("username", "netops"),
    #         # password=value.get("password"),
    #         password=host.get("password", "netops123"),
    #         platform=host_platform,
    #         extras=value.get("extras", {"auth_strict_key": False}),
    #     )
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
    def __init__(self, project: LabbyProject) -> None:
        self.project = project
        # self.project.get()
        # if not self.project.nodes:
        #     raise ValueError(f"No Node in Project: {self.project.name}")

    def load(self) -> Inventory:
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
            # print(hosts[node.name].keys(), type(hosts[node.name]))

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)
