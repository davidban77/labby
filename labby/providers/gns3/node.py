from labby.providers.gns3.provisioner import bootstrap
import time
import re
from typing import Dict, List, Optional
from gns3fy.templates import Template, get_templates
from gns3fy.nodes import Node
from gns3fy.ports import Port
from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult, RenderGroup, render_scope
from rich.table import Table
from rich.panel import Panel
from rich import box
import typer
from labby.models import LabbyNode, LabbyProjectInfo, LabbyPort
from labby.utils import console, dissect_url
from labby import config, lock_file
from labby.providers.gns3.utils import node_net_os, node_status


def dissect_gns3_template_name(template_name: str) -> Optional[Dict[str, str]]:
    pattern = re.compile(r"(?P<vendor>\S+)\s+(?P<os>\S+)\s+(?P<model>\S+)\s+(?P<version>\S+)")
    match = pattern.search(template_name)
    if not match:
        if config.DEBUG:
            console.log(f"Node template name not matching Labby GNS3 standard: {template_name}.", style="warning")
        return None
    node_data = dict(
        net_os=f"{match.groupdict()['vendor'].lower()}_{match.groupdict()['os'].lower()}",
        model=match.groupdict()["model"].lower(),
        version=match.groupdict()["version"],
    )
    return node_data


class GNS3Port(LabbyPort):
    def __init__(self, name: str, kind: str, port: Port) -> None:
        super().__init__(name=name, kind=kind)
        self._base = port


class GNS3Node(LabbyNode):
    builtin: bool = False
    _base: Node
    _template: Optional[Template]

    def __init__(
        self,
        name: str,
        template: str,
        project_name: str,
        node: Node,
        labels: List[str] = [],
        mgmt_addr: Optional[str] = None,
        mgmt_port: Optional[str] = None,
        **data,
    ) -> None:
        _project = LabbyProjectInfo(name=project_name, id=node.project_id)
        super().__init__(
            name=name,
            labels=labels,
            template=template,
            project=_project,
            _base=node,
            mgmt_addr=mgmt_addr,
            mgmt_port=mgmt_port,
            **data,
        )
        # self.name = name
        # self._base: Node = node
        self._template = self._get_gns3_template()
        self._update_labby_node_attrs()

    def _update_labby_node_attrs(self):
        self.id = self._base.node_id
        self.console = self._base.console
        self.status = self._base.status
        self.kind = self._base.node_type
        _interfaces = {}
        for p in self._base.ports:
            if p.name and p.link_type:
                _interfaces.update({p.name: GNS3Port(name=p.name, kind=p.link_type, port=p)})
            else:
                raise ValueError(f"Port name or link type info not available: {p} -> {self.name}")
        self.interfaces = _interfaces
        self.properties = self._base.properties

        # Validate mgmt_port
        if self.mgmt_port is not None and self.mgmt_port not in self.interfaces:
            console.log(f"Mgmt Port {self.mgmt_port} is not part of the node interfaces", style="error")
            raise typer.Exit(1)

        # Update attributes from template
        self.category = self._template.category
        self.builtin = self._template.builtin

        if self.template:
            node_data = dissect_gns3_template_name(self.template)
            if node_data:
                self.net_os = node_data["net_os"]
                self.model = node_data["model"]
                self.version = node_data["version"]

    def _get_gns3_template(self) -> Template:
        if not self.template:
            raise ValueError(f"Node Template must be specified {self.name}")

        _templates = get_templates(self._base._connector)
        try:
            tplt = next(_t for _t in _templates if _t.name == self.template)
        except StopIteration:
            raise ValueError(f"Node template not found: {self.template}")

        return tplt

    def get(self) -> None:
        console.log(f"[b]({self.project.name})({self.name})[/] Collecting node data")
        self._base.get()
        self._update_labby_node_attrs()

    def start(self) -> bool:
        console.log(f"[b]({self.project.name})({self.name})[/] Starting node")
        self._base.start()
        time.sleep(2)

        self.get()

        if self.status != "started":
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be started", style="warning")
            return False

        console.log(f"[b]({self.project.name})({self.name})[/] Node started", style="good")
        return True

    def stop(self) -> bool:
        console.log(f"[b]({self.project.name})({self.name})[/] Stopping node")
        self._base.stop()
        time.sleep(2)

        self.get()

        if self.status != "stopped":
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be stopped", style="warning")
            return False

        console.log(f"[b]({self.project.name})({self.name})[/] Node stopped", style="good")
        return True

    def restart(self) -> bool:
        console.log(f"[b]({self.project.name})({self.name})[/] Retarting node")
        self._base.reload()
        time.sleep(2)

        self.get()

        if self.status != "started":
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be restarted", style="warning")
            return False

        console.log(f"[b]({self.project.name})({self.name})[/] Node restarted", style="good")
        return True

    def update(self, **kwargs) -> None:
        if self.status != "started":
            self.start()

        console.log(f"[b]({self.project.name})({self.name})[/] Updating node: {kwargs}", highlight=True)
        if "labels" in kwargs:
            self.labels = kwargs["labels"]
        elif "mgmt_addr" in kwargs:
            self.mgmt_addr = kwargs["mgmt_addr"]
        elif "mgmt_port" in kwargs:
            self.mgmt_port = kwargs["mgmt_port"]
            if self.mgmt_port not in self.interfaces:
                console.log(f"Mgmt Port {self.mgmt_port} is not part of the node interfaces", style="error")
                raise typer.Exit(1)
        else:
            self._base.update(**kwargs)
        time.sleep(2)

        self.get()
        console.log(f"[b]({self.project.name})({self.name})[/] Node updated", style="good")
        lock_file.apply_node_data(self)

    def delete(self) -> bool:
        console.log(f"[b]({self.project.name})({self.name})[/] Deleting node")
        node_deleted = self._base.delete()
        time.sleep(2)
        if node_deleted:
            self.id = None
            self.status = "deleted"
            console.log(f"[b]({self.project.name})({self.name})[/] Node deleted", style="good")
            lock_file.delete_node_data(self.name, self.project.name)
            return True
        else:
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be deleted", style="warning")
            return False

    def bootstrap(self, config: str, boot_delay: int) -> bool:
        with console.status(
            f"[b]({self.project.name})({self.name})[/] Bootstraping node", spinner="aesthetic"
        ) as status:
            console.log(f"[b]({self.project.name})({self.name})[/] Bootstraping node")
            console.log(self)
            if self.status != "started":
                status.update(status=f"[b]({self.project.name})({self.name})[/] Starting node")
                self.start()
                status.update(status=f"[b]({self.project.name})({self.name})[/] Waiting for node to warmup")
                time.sleep(boot_delay)
            else:
                status.update(status=f"[b]({self.project.name})({self.name})[/] Restarting node")
                self.restart()
                status.update(status=f"[b]({self.project.name})({self.name})[/] Waiting for node to warmup")
                time.sleep(boot_delay)

        server_host = dissect_url(self._base._connector.base_url)[1]
        if not server_host:
            console.log(f"[b]({self.project.name})({self.name})[/] GNS3 server host could not be parsed", style="error")
            raise typer.Exit(1)

        console.log(f"[b]({self.project.name})({self.name})[/] Running bootstrap configuration process")
        if bootstrap(server_host=server_host, node=self, config=config):
            console.log(f"[b]({self.project.name})({self.name})[/] Bootstrapped node", style="good")
            return True
        else:
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be configured", style="error")
            return False

    def render_ports_detail(self) -> ConsoleRenderable:
        # The following helps highlight used ports
        list_ports = []
        flag = False
        for port in self._base.ports:
            for _, link in self._base.links.items():
                for gns3_port in link.nodes:
                    if gns3_port.name == port.name and gns3_port.node_name == self.name:
                        flag = True
            if flag:
                flag = False
                list_ports.append(f"[yellow i]{port.name}[/]")
            else:
                flag = False
                list_ports.append(port.name)
        ports = ", ".join([p for p in list_ports])
        return Panel(ports, expand=False, title="[b]Ports[/]", box=box.HEAVY_EDGE)

    def render_links_detail(self) -> ConsoleRenderable:
        paneles = []
        for index, link in enumerate(self._base.links.values()):
            paneles.append(
                Panel(
                    f"[yellow bold]{link.name}",
                    title=f"Link: {index}",
                )
            )
        return Panel(RenderGroup(*paneles), expand=False, title="[b]Links[/]", box=box.HEAVY_EDGE)

    def render_properties(self) -> ConsoleRenderable:
        return render_scope(self.properties if self.properties else {}, title="[b]Properties[/]")

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]Node:[/b] {self.name}"
        table = Table("Attributes", "Value", box=box.HEAVY_EDGE, highlight=True)
        table.add_row("[b]ID[/b]", self.id)
        table.add_row("[b]Template[/b]", self.template)
        table.add_row("[b]Kind[/b]", self.kind)
        table.add_row("[b]Project[/b]", self.project.name)
        table.add_row("[b]Status[/b]", node_status(self.status))
        table.add_row("[b]Console[/b]", str(self.console))
        table.add_row("[b]Category[/b]", self.category)
        table.add_row("[b]NET OS[/b]", node_net_os(self.net_os))
        table.add_row("[b]Model[/b]", self.model)
        table.add_row("[b]Version[/b]", self.version)
        table.add_row("[b]#Ports[/b]", str(len(self.interfaces)))
        table.add_row("[b]Labels[/b]", str(self.labels))
        table.add_row("[b]Mgmt Address[/b]", self.mgmt_addr)
        table.add_row("[b]Mgmt Port[/b]", self.mgmt_port)
        yield table
