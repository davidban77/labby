"""Templates for GNS3."""
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value
import time
import re
from typing import Dict, List, Optional

from gns3fy.templates import Template
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from rich import box

from labby.utils import console
from labby import config
from labby.providers.gns3.utils import bool_status, node_net_os
from labby.models import LabbyNodeTemplate


def dissect_gns3_template_name(template_name: str) -> Optional[Dict[str, str]]:
    """From template_name it returns data of the nodes in a dictionary."""
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


class GNS3NodeTemplate(LabbyNodeTemplate):
    # pylint: disable=too-many-instance-attributes
    """
    GNS3 Node template.

    Attributes:
        compute_id (Optional[str]): GN3S ID of the server running the node.
        builtin (bool): If the node is a GNS3 type of node (default=False).
        category (Optional[str]): Catergory of the template.
    """

    compute_id: Optional[str] = "local"
    builtin: bool = False
    category: Optional[str] = None
    _base: Template

    def __init__(self, name: str, template: Template, labels: List[str] = [], **data) -> None:
        """
        Initializes GNS3NodeTemplate.

        Attributes:
            name (str): Name for node template.
            template: A GNS3 template.
            labels (List[str]):labels for node template.
            data: Data for the template.
        """
        super().__init__(name=name, labels=labels, _base=template, **data)  # type: ignore
        self._update_labby_node_attrs()

    def _update_labby_node_attrs(self):
        self.id = self._base.template_id  # pylint: disable=invalid-name
        self.kind = self._base.template_type
        self.category = self._base.category
        self.builtin = self._base.builtin
        self.compute_id = self._base.compute_id
        template_data = dissect_gns3_template_name(self._base.name)
        if template_data:
            self.net_os = template_data["net_os"]
            self.model = template_data["model"]
            self.version = template_data["version"]

    def get(self) -> None:
        """Method for collecting the template data."""
        console.log(f"[b]({self.name})[/] Collecting template data")
        self._base.get()
        self._update_labby_node_attrs()

    def update(self, **kwargs) -> None:
        """Method to update current template."""
        console.log(f"[b]({self.name})[/] Updating template: {kwargs}", highlight=True)
        if "labels" in kwargs:
            self.labels = kwargs["labels"]  # pylint: disable=attribute-defined-outside-init
        else:
            self._base.update(**kwargs)
        time.sleep(2)

        self.get()
        console.log(f"[b]({self.name})[/] Template updated")

    def delete(self) -> bool:
        """Method to delete current template."""
        console.log(f"[b]({self.name})[/] Deleting template")
        tplt_deleted = self._base.delete()
        time.sleep(2)

        if tplt_deleted:
            self.id = None
            console.log(f"[b]({self.name})[/] Template deleted")
            return True

        console.log(f"[b]({self.name})[/] Template could not be deleted", style="warning")
        return False

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # pylint: disable=unused-argument
        # pylint: disable=redefined-outer-name
        """Renders a table of all the attributes in current project."""
        yield f"[b]Node Template:[/b] {self.name}"
        table = Table("Attributes", "Value", box=box.HEAVY_EDGE, highlight=True)
        for key, value in self.dict().items():
            if key.startswith("_"):
                continue
            if isinstance(value, bool):
                table.add_row(f"[b]{key.capitalize()}[/]", bool_status(value))
            elif key == "net_os":
                table.add_row("[b]NET OS[/b]", node_net_os(self.net_os))
            else:
                table.add_row(f"[b]{key.capitalize()}[/]", str(value))
        for key, value in sorted(self._base.dict().items()):
            if key.startswith("_") or key in self.dict().keys():
                continue
            if isinstance(value, bool):
                table.add_row(f"[b]{key.capitalize()}[/]", bool_status(value))
            elif isinstance(value, str) and not value:
                table.add_row(f"[b]{key.capitalize()}[/]", "None")
            else:
                table.add_row(f"[b]{key.capitalize()}[/]", str(value))
        yield table
