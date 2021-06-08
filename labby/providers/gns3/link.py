from labby.providers.gns3.utils import bool_status, link_status
from labby import lock_file
import time
from typing import List, Optional
from rich import box
from rich.table import Table
from rich.console import Console, RenderResult, ConsoleOptions
from gns3fy.links import Link
from labby.models import LabbyLink, LabbyLinkEndpoint, LabbyProjectInfo
from labby.utils import console


class GNS3LinkEndpoint(LabbyLinkEndpoint):
    pass


class GNS3Link(LabbyLink):
    endpoint: Optional[GNS3LinkEndpoint]
    _base: Link

    def __init__(self, name: str, project_name: str, link: Link, labels: List[str] = [], **data) -> None:
        _project = LabbyProjectInfo(name=project_name, id=link.project_id)
        super().__init__(name=name, labels=labels, project=_project, _base=link, **data)
        self._update_labby_link_attrs()

    def _update_labby_link_attrs(self):
        self.id = self._base.link_id
        self.kind = self._base.link_type
        if self._base.suspend:
            self.status = "suspended"
        else:
            self.status = "present"
        self.filters = self._base.filters
        self.endpoint = GNS3LinkEndpoint(
            node_a=self._base.nodes[0].node_name,
            port_a=self._base.nodes[0].name,
            node_b=self._base.nodes[-1].node_name,
            port_b=self._base.nodes[-1].name,
        )

    def get(self) -> None:
        console.log(f"[b]({self.project.name})({self.name})[/] Collecting link data")
        self._base.get()
        self._update_labby_link_attrs()

    def update(self, **kwargs) -> None:
        console.log(f"[b]({self.project.name})({self.name})[/] Updating link: {kwargs}", highlight=True)
        if "labels" in kwargs:
            self.labels = kwargs["labels"]
        else:
            self._base.update(**kwargs)
        time.sleep(2)

        self.get()
        console.log(f"[b]({self.project.name})({self.name})[/] Link updated", style="good")
        lock_file.apply_link_data(self)

    def apply_metric(self, **kwargs) -> bool:
        console.log(f"[b]({self.project.name})({self.name})[/] Applying filter: {kwargs}", highlight=True)
        filter_applied = self._base.apply_filters(**kwargs)
        time.sleep(2)
        self.get()
        if filter_applied:
            console.log(f"[b]({self.project.name})({self.name})[/] Filter applied", style="good")
            return True
        else:
            console.log(f"[b]({self.project.name})({self.name})[/] Filter could not be applied", style="warning")
            return False

    def delete(self) -> bool:
        console.log(f"[b]({self.project.name})({self.name})[/] Deleting link")
        link_deleted = self._base.delete()
        time.sleep(2)
        if link_deleted:
            self.id = None
            self.status = "deleted"
            console.log(f"[b]({self.project.name})({self.name})[/] Link deleted", style="good")
            lock_file.delete_link_data(self.name, self.project.name)
            return True
        else:
            console.log(f"[b]({self.project.name})({self.name})[/] Link could not be deleted", style="warning")
            return False

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]Link:[/b] {self.name}"
        table = Table(
            "Node A",
            "Port A",
            "Node B",
            "Port B",
            "Status",
            "Capturing",
            "Filter",
            "Labels",
            "Kind",
            "ID",
            box=box.HEAVY_EDGE,
            highlight=True,
        )
        if self.endpoint is None:
            raise ValueError(f"Link {self} does not have endpoint defined")
        table.add_row(
            self.endpoint.node_a,
            self.endpoint.port_a,
            self.endpoint.node_b,
            self.endpoint.port_b,
            link_status(self.status),
            bool_status(self._base.capturing),
            str(self.filters),
            str(self.labels),
            self.kind,
            self.id,
        )
        yield table
