# import typer
import re
import time
from typing import Any, List, Optional, Dict
from rich import box
from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.table import Table

# from rich.progress import track
from pydantic import Field
from gns3fy.projects import Project

# from gns3fy.templates import get_templates
from labby.models import LabbyProject
from labby.providers.gns3.node import GNS3Node
from labby.providers.gns3.link import GNS3Link
from labby.providers.gns3.utils import bool_status, link_status, node_status, node_net_os, template_type, project_status
from labby.utils import console
from labby import lock_file
from nornir import InitNornir


def get_link_name(node_a, port_a, node_b, port_b) -> str:
    return f"{node_a}: {port_a} == {node_b}: {port_b}"


class GNS3Project(LabbyProject):
    nodes: Dict[str, GNS3Node] = Field(default_factory=dict)  # type: ignore
    links: Dict[str, GNS3Link] = Field(default_factory=dict)  # type: ignore
    _base: Project
    _initial_state: Optional[str]

    def __init__(self, name: str, project: Project, labels: List[str] = [], **data) -> None:
        project.get()
        initial_state = project.status
        super().__init__(name=name, labels=labels, _base=project, _initial_state=initial_state, **data)
        if self._initial_state == "closed":
            self.start()
        else:
            self.get(nodes_refresh=True, links_refresh=True)

        self.init_nornir()

    def init_nornir(self) -> None:
        self.nornir = InitNornir(
            runner={
                "plugin": "threaded",
                "options": {
                    "num_workers": 100,
                },
            },
            inventory={"plugin": "LabbyNornirInventory", "options": {"project": self}},
        )

    def _update_labby_project_attrs(self, nodes_refresh: bool = False, links_refresh: bool = False):
        self.status = self._base.status
        self.id = self._base.project_id
        if nodes_refresh:
            self.nodes = {}
            for _node in self._base.nodes.values():
                if not _node.template:
                    _node.get()
                    if not _node.template:
                        raise ValueError(f"Node template could not be resolved: {_node}")
                kwargs: Dict[str, Any] = {}
                node_lock_file_data = lock_file.get_node_data(_node.name, self.name)
                if node_lock_file_data:
                    kwargs.update(**node_lock_file_data)
                self.nodes.update(
                    {
                        _node.name: GNS3Node(
                            name=_node.name, template=_node.template, project_name=self.name, node=_node, **kwargs
                        )
                    }
                )
        if links_refresh:
            self.links = {}
            for _link in self._base.links.values():
                if not _link.name:
                    _link.get()
                    if not _link.name:
                        raise ValueError(f"Link name could not be resolved {_link}")
                kwargs = {}
                link_lock_file_data = lock_file.get_link_data(_link.name, self.name)
                if link_lock_file_data:
                    kwargs.update(**link_lock_file_data)
                self.links.update({_link.name: GNS3Link(name=_link.name, project_name=self.name, link=_link, **kwargs)})

    def to_initial_state(self):
        if self._initial_state == "closed":
            self.stop(stop_nodes=False)

    def get_web_url(self) -> str:
        pattern = re.compile(r"/v\d")
        server_url = pattern.sub("", self._base._connector.base_url)
        return f"{server_url}/static/web-ui/server/1/project/{self.id}"

    def get(self, nodes_refresh: bool = False, links_refresh: bool = False) -> None:
        console.log(f"[b]({self.name})[/] Collecting project data")
        self._base.get()
        self._update_labby_project_attrs(nodes_refresh, links_refresh)
        self.init_nornir()

    def start(self, start_nodes: Optional[str] = None, nodes_delay: int = 5) -> bool:
        console.log(f"[b]({self.name})[/] Starting project")
        self._base.open()
        # Delay to give project to finish initilization
        time.sleep(2)

        # Start nodes
        if start_nodes is not None:
            self.start_nodes(start_nodes=start_nodes, nodes_delay=nodes_delay)

        # Refresh and validate
        self.get(nodes_refresh=True, links_refresh=True)
        # self._base.get()
        # self._update_labby_project_attrs()
        if self.status != "opened":
            console.log(f"[b]({self.name})[/] Project could not be started", style="warning")
            return False

        console.log(f"[b]({self.name})[/] Project started", style="good")
        return True

    def stop(self, stop_nodes: bool = True) -> bool:
        console.log(f"[b]({self.name})[/] Stopping project")

        # Stop nodes
        if stop_nodes:
            self.stop_nodes()
        self._base.close()
        time.sleep(2)

        # Refresh and validate
        self.get()
        # self._update_labby_project_attrs()
        if self.status != "closed":
            console.log(f"[b]({self.name})[/] Project could not be stopped", style="warning")
            return False

        console.log(f"[b]({self.name})[/] Project stopped", style="good")
        return True

    def update(self, **kwargs) -> None:
        if self.status == "closed":
            self.start()

        console.log(f"[b]({self.name})[/] Updating project: {kwargs}", highlight=True)
        if "labels" in kwargs:
            self.labels = kwargs["labels"]
        else:
            self._base.update(**kwargs)
        time.sleep(2)

        # Refresh
        self.get(nodes_refresh=True, links_refresh=True)
        console.log(f"[b]({self.name})[/] Project updated", style="good")
        # self._update_labby_project_attrs(refresh=True)

    def delete(self) -> bool:
        console.log(f"[b]({self.name})[/] Deleting project")
        project_deleted = self._base.delete()
        time.sleep(2)
        if project_deleted:
            self.id = None
            self.status = "deleted"
            self.nodes = {}
            self.links = {}
            console.log(f"[b]({self.name})[/] Project deleted", style="good")
            lock_file.delete_project_data(self.name)
            return True
        else:
            console.log(f"[b]({self.name})[/] Project could not be deleted", style="warning")
            return False

    def start_nodes(self, start_nodes: str, nodes_delay: int = 5) -> None:
        if start_nodes == "all":
            console.log(f"[b]({self.name})[/] Starting all nodes in project {self.name}...")
            self._base.nodes_action(action="start", poll_wait_time=nodes_delay)
            # Delay to give some time for device bootup
            time.sleep(5)
        elif start_nodes == "one_by_one":
            # for node in track(self._base.nodes.values(), description=f"[b]({self.name})[/] Starting nodes..."):
            #     if node.status == "started":
            #         console.log(f"[b]({self.name})[/] Node [cyan i]{node.name}[/] already started...")
            #     else:
            #         console.log(f"[b]({self.name})[/] Starting node: [cyan i]{node.name}[/]")
            #         node.start()
            #         time.sleep(nodes_delay)
            with console.status(f"[b]({self.name})[/] Starting nodes...", spinner="aesthetic") as status:
                for node in self.nodes.values():
                    if node.status == "started":
                        console.log(f"[b]({self.name})({node.name})[/] Node already started...")
                    else:
                        # console.log(f"[b]({self.name})({node.name})[/] Starting node: [cyan i]{node.name}[/]")
                        status.update(status=f"[b]({self.name})({node.name})[/] Starting node: [cyan i]{node.name}[/]")
                        node.start()
                        status.update(
                            status=f"[b]({self.name})({node.name})[/] Waiting for node warmup: [cyan i]{node.name}[/]"
                        )
                        time.sleep(nodes_delay)
        console.log(f"[b]({self.name})[/] Project nodes have been started", style="good")

    def stop_nodes(self) -> None:
        console.log(f"[b]({self.name})[/] Stopping nodes")
        self._base.nodes_action(action="stop")
        time.sleep(2)
        console.log(f"[b]({self.name})[/] Project nodes have been stopped", style="good")

    def create_node(
        self,
        name: str,
        template: str,
        labels: List[str] = [],
        mgmt_addr: Optional[str] = None,
        mgmt_port: Optional[str] = None,
        **kwargs,
    ) -> GNS3Node:
        if self.status == "closed":
            self.start()

        _node = self.search_node(name)
        if _node:
            console.log(f"Node [cyan i]{name}[/] already created. Nothing to do...", style="warning")
            return _node

        else:
            console.log(f"[b]({self.name})({name})[/] Creating node with template [cyan i]{template}[/]")
            gns3_node = self._base.create_node(name=name, template=template, **kwargs)
            node = GNS3Node(
                name=gns3_node.name,
                template=template,
                project_name=self.name,
                node=gns3_node,
                labels=labels,
                mgmt_addr=mgmt_addr,
                mgmt_port=mgmt_port,
                **kwargs,
            )
            time.sleep(2)
            # console.log(node)
            console.log(f"[b]({self.name})({node.name})[/] Node created", style="good")
            lock_file.apply_node_data(node, self)
            self.init_nornir()
            node.nornir = self.nornir.inventory.hosts[gns3_node.name]  # type: ignore
            return node

    # def delete_node(self, name: str) -> bool:
    #     if self.status == "closed":
    #         self.start()

    #     console.log(f"[b]({self.name})({name})[/] Deleting node")
    #     node_deleted = self._base.delete_node(name=name)
    #     time.sleep(2)
    #     self.get(nodes_refresh=True, links_refresh=True)

    #     if not node_deleted:
    #         console.log(f"[b]({self.name})[/] Node {name} was not deleted", style="warning")
    #         return False

    #     console.log(f"[b]({self.name})({name})[/] Node deleted")
    #     return True

    def search_node(self, name: str) -> Optional[GNS3Node]:
        if self.status == "closed":
            self.start()

        # Refresh attributes
        self.get()

        node = self.nodes.get(name)

        if node is not None:
            # Refresh lock data
            node_lock_file_data = lock_file.get_node_data(name, self.name)
            if node_lock_file_data is not None:
                node.labels = node_lock_file_data.get("labels", [])
                node.mgmt_addr = node_lock_file_data.get("mgmt_addr")
                node.mgmt_port = node_lock_file_data.get("mgmt_port")

            # Refresh nornir object on host
            if node.nornir is None:
                # print(type(self.nornir.inventory.hosts[name]))
                # print(self.nornir.inventory.hosts[name])
                # node.nornir = self.nornir.filter(host=name)
                node.nornir = self.nornir.filter(filter_func=lambda h: h.name == name)  # type: ignore
                # print(node.nornir.inventory.hosts[name].values())
                # node.nornir = self.nornir.inventory.hosts[name]

        return node

    # def update_node(self, name: str, **kwargs) -> None:
    #     node = self.search_node(name)
    #     if node is None:
    #         console.log(f"[b]({self.name})({name})[/] Node not found", style="warning")
    #         raise typer.Exit(1)

    #     with console.status(f"[b]({self.name})({node.name})[/] Updating node: {kwargs}", spinner="aesthetic") as _:
    #         node.update(**kwargs)
    #     lock_file.apply_node_data(node, self)

    # def update_node(self, name: str, **kwargs) -> None:
    #     node = self.search_node(name)
    #     if node is None:
    #         console.log(f"[b]({self.name})({name})[/] Node not found", style="warning")
    #         raise typer.Exit(1)

    #     with console.status(f"[b]({self.name})({node.name})[/] Updating node: {kwargs}", spinner="aesthetic") as _:
    #         node.update(**kwargs)
    #     lock_file.apply_node_data(node, self)

    # def bootstrap_node(self, name: str, config: str, boot_delay: int = 5) -> bool:
    #     console.log(f"[b]({self.name})({name})[/] Bootstraping node")
    #     node = self.search_node(name)
    #     console.log(node)
    #     if node.status != "started":
    #         node.start()
    #         time.sleep(boot_delay)
    #     if not node:
    #         console.log(f"[b]({self.name})[/]Node [cyan i]{name}[/] not found. Nothing to do...", style="error")
    #         raise typer.Exit(1)
    #     server_host = dissect_url(self._base._connector.base_url)[1]
    #     if not server_host:
    #         console.log(f"[b]({self.name})({node.name})[/] GNS3 server host could not be parsed", style="error")
    #         raise typer.Exit(1)

    #     console.log(f"[b]({self.name})({name})[/] Running bootstrap config")
    #     if bootstrap(server_host=server_host, node=node, config=config):
    #         console.log(f"[b]({self.name})({node.name})[/] Bootstrapped node", style="good")
    #         return True
    #     else:
    #         console.log(f"[b]({self.name})({node.name})[/] Node could not be configured", style="error")
    #         return False

    def create_link(
        self,
        node_a: str,
        port_a: str,
        node_b: str,
        port_b: str,
        filters: Optional[Dict[str, Any]] = None,
        labels: List[str] = [],
        **kwargs,
    ) -> GNS3Link:
        if self.status == "closed":
            self.start()

        _link = self.search_link(node_a, port_a, node_b, port_b)
        if _link:
            console.log(f"Link [cyan i]{_link.name}[/] already created. Nothing to do...", style="warning")
            return _link
        else:
            console.log(f"[b]({self.name})[/] Creating link on: [cyan i]{node_a}: {port_a} <==> {port_b}: {node_b}[/]")
            gns3_link = self._base.create_link(node_a, port_a, node_b, port_b, **kwargs)
            _link = GNS3Link(
                name=gns3_link.name if gns3_link.name else get_link_name(node_a, port_a, node_b, port_b),
                project_name=self.name,
                link=gns3_link,
                labels=labels,
                **kwargs,
            )
            time.sleep(2)
            if filters:
                _link.apply_metric(**filters)
            # console.log(_link)
            console.log(f"[b]({self.name})({_link.name})[/] Link created", style="good")
            lock_file.apply_link_data(_link, self)
            return _link

    # def delete_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> bool:
    #     if self.status == "closed":
    #         self.start()

    #     console.log(f"[b]({self.name})({node_a}: {port_a} <==> {port_b}: {node_b})[/] Deleting link")
    #     link_deleted = self._base.delete_link(node_a, port_a, node_b, port_b)
    #     time.sleep(2)
    #     self.get(nodes_refresh=True, links_refresh=True)

    #     if not link_deleted:
    #         console.log(
    #             f"[b]({self.name})[/] Link {node_a}: {port_a} <==> {port_b}: {node_b} was not deleted",
    #             style="warning",
    #         )
    #         return False

    #     console.log(f"[b]({self.name})[/] Link [cyan i]{node_a}: {port_a} <==> {port_b}: {node_b}[/] deleted")
    #     return True

    def search_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> Optional[GNS3Link]:
        # Refresh attributes
        self.get()

        _gns3_link = self._base.search_link(node_a, port_a, node_b, port_b)

        if _gns3_link is None:
            return None

        link = self.links.get(f"{_gns3_link.name}")

        if link is not None:
            link_lock_file_data = lock_file.get_link_data(link.name, self.name)
            if link_lock_file_data is not None:
                link.labels = link_lock_file_data.get("labels", [])

        return link

    def render_nodes_summary(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        table = Table(
            "Name",
            "Status",
            "Kind",
            "Category",
            "NET OS",
            "Model",
            "Version",
            "Builtin",
            # "Template",
            "Console Port",
            "Labels",
            "Mgmt Address",
            "# Ports",
            title="Nodes Information",
            title_justify="center",
            show_lines=True,
            highlight=True,
        )
        if field:
            nodes = [x for x in self.nodes.values() if getattr(x, field) == value]
        else:
            nodes = list(self.nodes.values())
        for node in nodes:
            node_ports = "None" if node.interfaces is None else str(len(node.interfaces))
            table.add_row(
                f"[b]{node.name}[/]",
                node_status(node.status),
                template_type(node.kind),
                node.category if node.template else "None",
                node_net_os(node.net_os),
                node.model if node.model else "None",
                node.version if node.version else "None",
                bool_status(node.builtin),
                # node.template if node.template else "None",
                str(node.console),
                str(node.labels) if node.labels is not None else "None",
                node.mgmt_addr,
                node_ports,
            )
        return table

    def render_links_summary(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        table = Table(
            "Node A",
            "Port A",
            "Node B",
            "Port B",
            "Status",
            "Capturing",
            "Filters",
            "Labels",
            "Kind",
            title="Links Information",
            show_lines=True,
            title_justify="center",
            highlight=True,
        )
        if field:
            links = [x for x in self.links.values() if getattr(x, field) == value]
        else:
            links = list(self.links.values())
        for link in links:
            if link.endpoint is None:
                raise ValueError(f"Link {link} does not have endpoint defined")
            table.add_row(
                f"[b]{link.endpoint.node_a}[/]",
                f"{link.endpoint.port_a}",
                f"[b]{link.endpoint.node_b}[/]",
                f"{link.endpoint.port_b}",
                link_status(link.status),
                bool_status(link._base.capturing) if link._base.capturing is not None else "None",
                str(link.filters) if link.filters is not None else "None",
                str(link.labels) if link.labels is not None else "None",
                link.kind,
            )
        return table

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]Project:[/b] {self.name}"
        table = Table(
            "Status",
            "#Nodes",
            "#Links",
            "Labels",
            "Auto Start",
            "Auto Close",
            "Auto Open",
            "ID",
            box=box.HEAVY_EDGE,
            highlight=True,
        )
        table.add_row(
            project_status(self.status),
            str(len(self.nodes)),
            str(len(self.links)),
            str(self.labels),
            bool_status(self._base.auto_start),
            bool_status(self._base.auto_close),
            bool_status(self._base.auto_open),
            self.id,
        )
        yield table