"""GNS3 Project module."""
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value
import re
import time
from typing import Any, List, Optional, Dict

from rich import box
from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.table import Table
from pydantic import Field
from nornir import InitNornir
from gns3fy.projects import Project

from labby.models import LabbyProject
from labby.providers.gns3.node import GNS3Node
from labby.providers.gns3.link import GNS3Link
from labby.providers.gns3.utils import bool_status, link_status, node_status, node_net_os, template_type, project_status
from labby.utils import console
from labby import lock_file


def get_link_name(node_a: str, port_a: str, node_b: str, port_b: str) -> str:
    """Return the name of a link.

    Args:
        node_a (str): Side A node name.
        port_a (str): Side A port name.
        node_b (str): Side B node name.
        port_b (str): Side B port name.

    Returns:
        str: Link name.
    """
    return f"{node_a}: {port_a} == {node_b}: {port_b}"


class GNS3Project(LabbyProject):
    """GNS3 Project class."""

    nodes: Dict[str, GNS3Node] = Field(default_factory=dict)  # type: ignore
    links: Dict[str, GNS3Link] = Field(default_factory=dict)  # type: ignore
    _base: Project
    _initial_state: Optional[str]

    def __init__(self, name: str, project: Project, labels: List[str] = [], **data) -> None:
        """Initialize a GNS3 Project instance.

        Args:
            name (str): Project name.
            project (Project): GNS3 Project instance.
            labels (List[str], optional): List of labels.
            data (Dict[str, Any]): Project data.
        """
        project.get()
        initial_state = project.status
        super().__init__(name=name, labels=labels, _base=project, _initial_state=initial_state, **data)  # type: ignore
        if self._initial_state == "closed":
            self.start()
        else:
            self.get(nodes_refresh=True, links_refresh=True)

        self.init_nornir()

    def init_nornir(self) -> None:
        """Initialize Norir instance."""
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
        """Update labby project attributes.

        Args:
            nodes_refresh (bool, optional): Refresh nodes attributes.
            links_refresh (bool, optional): Refresh links attributes.

        Raises:
            ValueError: If a node template could not be resolved
            ValueError: If a link name could not be resolved
        """
        self.status = self._base.status
        self.id = self._base.project_id  # pylint: disable=invalid-name
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
        """Set project status to initial state."""
        if self._initial_state == "closed":
            self.stop(stop_nodes=False)

    def get_web_url(self) -> str:
        """Return the project web url.

        Returns:
            str: Project web url.
        """ """
        """
        pattern = re.compile(r"/v\d")
        server_url = pattern.sub("", self._base._connector.base_url)
        return f"{server_url}/static/web-ui/server/1/project/{self.id}"

    def get(self, nodes_refresh: bool = False, links_refresh: bool = False) -> None:
        """Get project attributes.

        Args:
            nodes_refresh (bool, optional): Refresh nodes attributes.
            links_refresh (bool, optional): Refresh links attributes.
        """
        console.log(f"[b]({self.name})[/] Collecting project data")
        self._base.get()
        self._update_labby_project_attrs(nodes_refresh, links_refresh)
        self.init_nornir()

    def start(self, start_nodes: Optional[str] = None, nodes_delay: int = 5) -> bool:
        """Start project.

        Args:
            start_nodes (Optional[str], optional): Start nodes.
            nodes_delay (int, optional): Nodes delay between starts.

        Returns:
            bool: True if project started.
        """
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
        """Stop project.

        Args:
            stop_nodes (bool, optional): Stop nodes before.

        Returns:
            bool: True if project stopped.
        """
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
        """Update project attributes.

        Args:
            **kwargs: Attributes to update.
        """
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
        """Delete project.

        Returns:
            bool: True if project deleted.
        """
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

        console.log(f"[b]({self.name})[/] Project could not be deleted", style="warning")
        return False

    def start_nodes(self, start_nodes: str, nodes_delay: int = 5) -> None:
        """Start nodes.

        Args:
            start_nodes (str): Start nodes method. Options are: "all", "one_by_one".
            nodes_delay (int, optional): Nodes delay between starts.
        """
        if start_nodes == "all":
            console.log(f"[b]({self.name})[/] Starting all nodes in project {self.name}...")
            self._base.nodes_action(action="start", poll_wait_time=nodes_delay)
            # Delay to give some time for device bootup
            time.sleep(5)
        elif start_nodes == "one_by_one":
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
        """Stop nodes."""
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
        config_managed: bool = True,
        **kwargs,
    ) -> GNS3Node:
        """Create node.

        Args:
            name (str): Node name.
            template (str): Node template.
            labels (List[str], optional): Node labels.
            mgmt_addr (Optional[str], optional): Node management address.
            mgmt_port (Optional[str], optional): Node management port.

        Returns:
            GNS3Node: Node instance.
        """
        if self.status == "closed":
            self.start()

        _node = self.search_node(name)
        if _node:
            console.log(f"Node [cyan i]{name}[/] already created. Nothing to do...", style="warning")
            return _node

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
            config_managed=config_managed,
            **kwargs,
        )

        # Assign nornir object
        node.nornir = self.nornir.filter(filter_func=lambda h: h.name == name)  # type: ignore

        # Save node in project
        self.nodes[name] = node
        time.sleep(2)
        console.log(f"[b]({self.name})({node.name})[/] Node created", style="good")

        # Apply node to lock file
        lock_file.apply_node_data(node, self)

        # Refresh Nornir object
        self.init_nornir()
        return node

    def search_node(self, name: str) -> Optional[GNS3Node]:
        """Search node in project.

        Args:
            name (str): Node name.

        Returns:
            Optional[GNS3Node]: Node instance.
        """
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
                node.nornir = self.nornir.filter(filter_func=lambda h: h.name == name)  # type: ignore

        return node

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
        """Create link.

        Args:
            node_a (str): Side A Node name.
            port_a (str): Side A Port name.
            node_b (str): Side B Node name.
            port_b (str): Side B Port name.
            filters (Optional[Dict[str, Any]], optional): Filters to use.
            labels (List[str], optional): Link labels.

        Returns:
            GNS3Link: Link instance.
        """
        if self.status == "closed":
            self.start()

        _link = self.search_link(node_a, port_a, node_b, port_b)

        if _link:
            console.log(f"Link [cyan i]{_link.name}[/] already created. Nothing to do...", style="warning")
            return _link

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

        console.log(f"[b]({self.name})({_link.name})[/] Link created", style="good")
        lock_file.apply_link_data(_link, self)
        return _link

    def search_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> Optional[GNS3Link]:
        """Search link in project.

        Args:
            node_a (str): Side A Node name.
            port_a (str): Side A Port name.
            node_b (str): Side B Node name.
            port_b (str): Side B Port name.

        Returns:
            Optional[GNS3Link]: Link instance.
        """
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

    def render_nodes_summary(
        self, field: Optional[str] = None, value: Optional[str] = None, labels: Optional[List[str]] = []
    ) -> ConsoleRenderable:
        """Render a Project's nodes attributes summary.

        Args:
            field (Optional[str], optional): Field to filter on.
            value (Optional[str], optional): Value to filter on.

        Returns:
            ConsoleRenderable: Renderable table of the nodes attributes.
        """
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
            "Config Managed",
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

            # Skip node if labels are not present
            if labels:
                if not any(x in node.labels for x in labels):
                    continue

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
                bool_status(node.config_managed),
                node_ports,
            )
        return table

    def render_links_summary(
        self, field: Optional[str] = None, value: Optional[str] = None, labels: Optional[List[str]] = []
    ) -> ConsoleRenderable:
        """Render a Project's links attributes summary.

        Args:
            field (Optional[str], optional): Field to filter on.
            value (Optional[str], optional): Value to filter on.

        Raises:
            ValueError: If a link does not have an endpoint defined.

        Returns:
            ConsoleRenderable: Renderable table of the links attributes.
        """
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

            # Skip node if labels are not present
            if labels:
                if not any(x in link.labels for x in labels):
                    continue

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
        # pylint: disable=unused-argument
        # pylint: disable=redefined-outer-name
        """Rich repr for a project.

        Args:
            console (Console): Console instance.
            options (ConsoleOptions): Console options.

        Returns:
            RenderResult: Console render result.

        Yields:
            Iterator[RenderResult]: Console render result.
        """
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
