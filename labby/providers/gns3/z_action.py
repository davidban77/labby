import gns3fy
from typing import Dict, Tuple
from rich.console import Console
from requests.exceptions import HTTPError


GNS3_SERVER = "http://gns3-server:80"

gns3_server = gns3fy.Gns3Connector(url=GNS3_SERVER)
console = Console()


class Action:
    def is_project_created(self, project: gns3fy.Project) -> bool:
        try:
            project.get()
            prj_exists = True
        except HTTPError as err:
            if "Project ID None doesn't exist" not in str(err):
                raise err
            prj_exists = False
        return prj_exists

    def is_node_created(self, node: gns3fy.Node) -> bool:
        try:
            node.get()
            node_exists = True
        except Exception:
            # TODO: To be fixed once the issue is solved on gns3fy
            node_exists = False
        return node_exists

    def get_project(self, name: str) -> Tuple[gns3fy.Project, bool]:
        project = gns3fy.Project(name=name, connector=gns3_server)
        prj_exists = self.is_project_created(project)
        return project, prj_exists

    def get_node(
        self, name: str, project: gns3fy.Project
    ) -> Tuple[gns3fy.Project, bool]:
        node = gns3fy.Node(
            name=name, project_id=project.project_id, connector=gns3_server
        )
        node_exists = self.is_node_created(node)
        return node, node_exists

    def get_link(
        self,
        project: gns3fy.Project,
        node_a: str,
        port_a: str,
        node_b: str,
        port_b: str,
    ) -> Tuple[gns3fy.Link, bool]:
        _node_a = project.get_node(name=node_a)
        if not _node_a:
            raise ValueError(f"node_a: {node_a} not found")
        try:
            _port_a = [_p for _p in _node_a.ports if _p["name"] == port_a][0]
        except IndexError:
            raise ValueError(f"port_a: {port_a} not found")

        _node_b = project.get_node(name=node_b)
        if not _node_b:
            raise ValueError(f"node_b: {node_b} not found")
        try:
            _port_b = [_p for _p in _node_b.ports if _p["name"] == port_b][0]
        except IndexError:
            raise ValueError(f"port_b: {port_b} not found")

        _matches = []
        for _l in project.links:
            if not _l.nodes:
                continue
            if (
                _l.nodes[0]["node_id"] == _node_a.node_id
                and _l.nodes[0]["adapter_number"] == _port_a["adapter_number"]
                and _l.nodes[0]["port_number"] == _port_a["port_number"]
                and _l.nodes[1]["node_id"] == _node_b.node_id
                and _l.nodes[1]["adapter_number"] == _port_b["adapter_number"]
                and _l.nodes[1]["port_number"] == _port_b["port_number"]
            ):
                _matches.append(_l)
            elif (
                _l.nodes[1]["node_id"] == _node_a.node_id
                and _l.nodes[1]["adapter_number"] == _port_a["adapter_number"]
                and _l.nodes[1]["port_number"] == _port_a["port_number"]
                and _l.nodes[0]["node_id"] == _node_b.node_id
                and _l.nodes[0]["adapter_number"] == _port_b["adapter_number"]
                and _l.nodes[0]["port_number"] == _port_b["port_number"]
            ):
                _matches.append(_l)
        try:
            link = _matches[0]
            link_exists = True
        except IndexError:
            link = None
            link_exists = False

        return link, link_exists

    def get_template(self, name: str) -> Tuple[Dict[str, str], bool]:
        template = gns3_server.get_template(name=name)
        if template is None:
            templ_exists = False
        else:
            templ_exists = True
        return template, templ_exists

    def create_project(self, project: gns3fy.Project):
        project.create()

    def create_node(self, node: gns3fy.Node, template: str):
        node.template = template
        node.create()

    def create_link(
        self,
        project: gns3fy.Project,
        node_a: str,
        port_a: str,
        node_b: str,
        port_b: str,
    ):
        project.create_link(node_a=node_a, port_a=port_a, node_b=node_b, port_b=port_b)

    def open_project(self, project: gns3fy.Project):
        project.open()

    def close_project(self, project: gns3fy.Project):
        project.stop_nodes(poll_wait_time=0)
        project.close()

    def delete_project(self, project: gns3fy.Project):
        project.stop_nodes(poll_wait_time=0)
        project.delete()

    def delete_link(self, link: gns3fy.Link):
        link.delete()

    def delete_node(self, node: gns3fy.Node):
        node.stop()
        node.delete()

    def start_node(self, node: gns3fy.Node):
        node.start()

    def stop_node(self, node: gns3fy.Node):
        node.stop()

    def suspend_node(self, node: gns3fy.Node):
        node.suspend()

    def reload_node(self, node: gns3fy.Node):
        node.reload()

    def prep_status_project(self, project: gns3fy.Project) -> str:
        initial_status = project.status
        if initial_status == "closed":
            console.print(f"Opening project [cyan]{project.name}[/]...")
            project.open()
            project.get()
        return initial_status

    def post_status_project(self, project: gns3fy.Project, initial_status: str):
        if initial_status == "closed":
            console.print(f"Closing project [cyan]{project.name}[/]...")
            project.close()
