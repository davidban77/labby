import gns3fy
import labby.models as models
from typing import Dict, Optional
from rich import box
from rich.console import ConsoleRenderable, RenderGroup, render_scope
from rich.panel import Panel
from rich.table import Table


def bool_status(bool_value: bool) -> str:
    return "[cyan]Yes[/cyan]" if bool_value is True else "[orange1]No[/orange1]"


def string_status(str_value: str) -> str:
    return "None" if str_value == "" else str_value


def node_status(status: str) -> str:
    STATUS_CODES = {
        "started": "[green]started[/]",
        "stopped": "[red]stopped[/]",
        "suspended": "[yellow]suspended[/]",
    }
    return STATUS_CODES[status]


def project_status(status: str) -> str:
    STATUS_CODES = {
        "opened": "[green]started[/]",
        "closed": "[red]stopped[/]",
    }
    return STATUS_CODES[status]


def template_type(t_type: str) -> str:
    TEMPLATE_TYPE = {
        "qemu": "[rosy_brown]qemu[/]",
        "docker": "[bright_blue]docker[/]",
    }
    return TEMPLATE_TYPE.get(t_type, f"[white]{t_type}[/]")


class Reports:
    def __init__(self, server: gns3fy.Gns3Connector):
        self.server = server

    def table_projects_list(
        self, field: Optional[str] = None, value: Optional[str] = None
    ) -> Table:
        table = Table(title="GNS3 Projects")
        table.add_column("Project Name")
        table.add_column("Status")
        table.add_column("Auto Start")
        table.add_column("Auto Close")
        table.add_column("Auto Open")
        table.add_column("Supplier")
        if field:
            projects = [x for x in self.server.get_projects() if x[field] == value]
        else:
            projects = self.server.get_projects()
        for prj in projects:
            table.add_row(
                prj["name"],
                project_status(prj["status"]),
                bool_status(prj["auto_start"]),
                bool_status(prj["auto_close"]),
                bool_status(prj["auto_open"]),
                prj["supplier"],
            )
        return table

    def table_project_summary(self, project: models.Project) -> Table:
        if project._provider is None:
            raise ValueError("GNS3 Project must be initialized")
        table = Table(
            "Status",
            "Nodes",
            "Links",
            "ID",
            title="Project Information",
            box=box.HEAVY_EDGE,
            title_justify="center",
        )
        table.add_row(
            project_status(project._provider.status),
            str(len(project._provider.nodes)),
            str(len(project._provider.links)),
            project._provider.project_id,
        )
        return table

    def table_nodes_summary(
        self,
        project: models.Project,
        field: Optional[str] = None,
        value: Optional[str] = None,
    ) -> Table:
        if project._provider is None:
            raise ValueError("GNS3 Project must be initialized")
        table = Table(
            "Name",
            "Type",
            "Category",
            "Builtin",
            "Template",
            "Status",
            "Console Port",
            "# Ports",
            title="Nodes Information",
            title_justify="center",
            show_lines=True,
        )
        templates = {k["template_id"]: k for k in self.server.get_templates()}
        if field:
            nodes = [x for x in project._provider.nodes if getattr(x, field) == value]
        else:
            nodes = project._provider.nodes
        for node in nodes:
            node_ports = "N/A" if node.ports is None else str(len(node.ports))
            table.add_row(
                node.name,
                template_type(node.node_type),
                templates[node.template_id]["category"],
                bool_status(templates[node.template_id]["builtin"]),
                templates[node.template_id]["name"],
                node_status(node.status),
                str(node.console),
                node_ports,
            )
        return table

    def table_links_summary(
        self,
        project: models.Project,
        field: Optional[str] = None,
        value: Optional[str] = None,
    ) -> Table:
        if project._provider is None:
            raise ValueError("GNS3 Project must be initialized")
        table = Table(
            "Type",
            "Suspended",
            "Node A",
            "Port A",
            "Node B",
            "Port B",
            "Capturing",
            title="Links Information",
            show_lines=True,
            title_justify="center",
        )
        if field:
            links = [x for x in project._provider.links if getattr(x, field) == value]
        else:
            links = project._provider.links
        for link in links:
            node_a = project._provider.get_node(node_id=link.nodes[0]["node_id"])
            node_b = project._provider.get_node(node_id=link.nodes[1]["node_id"])
            table.add_row(
                link.link_type,
                bool_status(link.suspend),
                f"{node_a.name}",
                f"{link.nodes[0]['label']['text']}",
                f"{node_b.name}",
                f"{link.nodes[1]['label']['text']}",
                bool_status(link.capturing),
            )
        return table

    def table_templates_list(
        self, field: Optional[str] = None, value: Optional[str] = None
    ) -> Table:
        table = Table(title="GNS3 Templates")
        table.add_column("Device Template")
        table.add_column("Category")
        table.add_column("Type")
        table.add_column("Builtin")
        table.add_column("Mgmt Port")
        table.add_column("Image")
        if field:
            templates = [x for x in self.server.get_templates() if x[field] == value]
        else:
            templates = self.server.get_templates()
        for template in templates:
            table.add_row(
                template["name"],
                template["category"],
                template["template_type"],
                bool_status(template["builtin"]),
                string_status(template.get("first_port_name", "N/A")),
                string_status(template.get("hda_disk_image", "N/A")),
            )
        return table

    def table_template_detail(self, template: Dict[str, str]) -> ConsoleRenderable:
        # table = []
        # for k, v in template.items():
        #     # Breaking down usage field, because sometimes is too long
        #     if k == "usage":
        #         v = "\n".join(v.split(". "))
        #     header = " ".join(k.split("_")).title()
        #     table.append(Panel(f"[b]{header}[/b]\n[yellow]{v}[/]", expand=True))
        # return Columns(table)
        return render_scope(template, title="Parameters")

    def table_node_detail(self, node: models.Node) -> Table:
        if node._provider is None:
            raise ValueError("GNS3 Project and Node must be initialized")
        table = Table(
            "Name",
            "Project ID",
            "Compute ID",
            "Node Type",
            "Status",
            "Locked",
            "Console",
            # "Ports",
            "Template",
            # "Properties"
            title="Node Information",
            show_lines=True,
            title_justify="center",
        )
        templates = {k["template_id"]: k for k in self.server.get_templates()}
        table.add_row(
            node.name,
            node.project_id,
            node._provider.compute_id,
            template_type(node._provider.node_type),
            node_status(node._provider.status),
            bool_status(node._provider.locked),
            str(node.console) if node.console is not None else "N/A",
            templates[node._provider.template_id]["name"],
        )
        return table

    def table_node_properties_detail(self, node: models.Node) -> ConsoleRenderable:
        # table = []
        # for k, v in node.properties.items():
        #     # Breaking down usage field, because sometimes is too long
        #     if k == "interfaces" or k == "ports_mapping":
        #         continue
        #     if k == "usage":
        #         v = "\n".join(v.split(". "))
        #     header = " ".join(k.split("_")).title()
        #     table.append(Panel(f"[b]{header}[/b]\n[yellow]{v}[/]", expand=True))
        # return Columns(table)
        return render_scope(
            node.properties if node.properties else {}, title="Properties"
        )

    def table_node_ports_detail(self, node: models.Node):
        if node._provider is None:
            raise ValueError("GNS3 Project and Node must be initialized")
        ports = ", ".join([p["name"] for p in node._provider.ports])
        return Panel(ports, expand=False, title="Ports")

    def table_node_links_detail(self, node: models.Node):
        if node._provider is None:
            raise ValueError("GNS3 Project and Node must be initialized")
        paneles = []
        for index, link in enumerate(node._provider.links):
            endpoint_a = self.server.get_node(
                node_id=link.nodes[0]["node_id"], project_id=node._provider.project_id
            )["name"]
            port_a = link.nodes[0]["label"]["text"]
            endpoint_b = self.server.get_node(
                node_id=link.nodes[1]["node_id"], project_id=node._provider.project_id
            )["name"]
            port_b = link.nodes[1]["label"]["text"]
            paneles.append(
                Panel(
                    f"[yellow]{endpoint_a}: {port_a} [b]<===>[/b] "
                    f"{endpoint_b}: {port_b}",
                    title=f"Link: {index}",
                )
            )
        return Panel(RenderGroup(*paneles), expand=False, title="Links")
