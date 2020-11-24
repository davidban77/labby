import time
import gns3fy
from labby.utils import console
import labby.models as models
from typing import List, Tuple, Dict
from requests.exceptions import HTTPError
from rich.progress import track


def set_node_attributes(node: models.Node):
    if node._provider is None:
        raise ValueError("GNS3 Provider not initialized")
    node.project_id = node._provider.project_id
    node.id = node._provider.node_id
    node.console = node._provider.console
    node.status = node._provider.status
    node.template = node._provider.template
    node.type = node._provider.node_type
    node.category = node._provider.connector.get_template(
        template_id=node._provider.template_id
    )
    node.interfaces = node._provider.ports
    node.properties = node._provider.properties


def set_connection_attributes(connection: models.Connection):
    if connection._provider is None:
        raise ValueError("GNS3 Provider not initialized")
    connection.project_id = connection._provider.project_id
    connection.id = connection._provider.link_id
    connection.type = connection._provider.link_type
    # connection.endpoints = connection._provider.nodes


def get_nodes(project: models.Project) -> List[models.Node]:
    if project._provider is None:
        raise ValueError("GNS3 Provider not initialized")
    nodes = []
    for gns3_node in project._provider.nodes:
        node = models.Node(
            name=gns3_node.name, project=project.name, _provider=gns3_node
        )
        nodes.append(set_node_attributes(node))
    return nodes


def get_connections(project: models.Project) -> List[models.Connection]:
    if project._provider is None:
        raise ValueError("GNS3 Provider not initialized")
    conns = []
    for index, gns3_link in enumerate(project._provider.links):
        conn = models.Connection(
            name=str(index), project=project.name, _provider=gns3_link
        )
        conns.append(set_connection_attributes(conn))
    return conns


def set_project_attributes(project: models.Project):
    if project._provider is None:
        raise ValueError("GNS3 Provider not initialized")
    project.status = project._provider.status
    project.id = project._provider.project_id
    project.nodes = get_nodes(project) if project._provider.nodes else None
    project.connections = get_connections(project) if project._provider.links else None


class GNS3ProjectBuilder:
    def __init__(self, server):
        self.server = server

    def prep_status(self, project: models.Project) -> str:
        if project.status is None:
            raise ValueError("GNS3 Project not initialized")
        initial_status = project.status
        if initial_status == "closed":
            console.log(f"Opening project [cyan]{project.name}[/]...")
            self.start(project, start_nodes="none")
        return initial_status

    def post_status(self, project: models.Project, initial_status: str):
        if initial_status == "closed":
            console.log(f"Closing project [cyan]{project.name}[/]...")
            self.stop(project, stop_nodes=False)

    def update(self, project: models.Project):
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")
        try:
            project._provider.get()
            project.is_created = True
            set_project_attributes(project)
        except HTTPError as err:
            if "Project ID None doesn't exist" not in str(err):
                raise err
            project.is_created = False

    def set_provider(self, project: models.Project):
        project._provider = gns3fy.Project(name=project.name, connector=self.server)

    def retrieve(self, project: models.Project) -> bool:
        self.set_provider(project)
        self.update(project)
        if not project.is_created:
            return False
        return True

    def create(self, project: models.Project) -> bool:
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Create and update
        project._provider.create()
        self.update(project)
        if not project.is_created:
            return False
        return True

    def delete(self, project: models.Project) -> bool:
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Stop and delete
        project._provider.stop_nodes()
        project._provider.delete()
        project.is_created = False

        # Verify object deleation
        # self.update(project)
        # if project.is_created:
        #     return False

        # Init some attributes
        project._provider = None
        project.id = None
        project.status = None
        project.nodes = None
        project.connections = None
        return True

    def start(
        self, project: models.Project, start_nodes: str, nodes_delay: int = 5
    ) -> bool:
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        project._provider.open()
        if start_nodes == "all":
            console.log(f"Starting all nodes in project {project.name}...")
            project._provider.start_nodes(nodes_delay)
        elif start_nodes == "one_by_one":
            for node in track(project._provider.nodes, description="Starting nodes..."):
                if node.status == "started":
                    console.log(f"Node [cyan]{node.name}[/] already started...")
                else:
                    console.log(f"Starting node: [cyan]{node.name}[/]")
                    node.start()
                    time.sleep(nodes_delay)

        # Refresh and validate
        self.update(project)
        if project.status != "opened":
            return False
        return True

    def stop(self, project: models.Project, stop_nodes: bool) -> bool:
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        if stop_nodes:
            console.log("Stopping nodes...")
            project._provider.stop_nodes()
        project._provider.close()

        # Refresh and validate
        self.update(project)
        if project.status != "closed":
            return False
        return True

    def get_template(self, name: str) -> Tuple[Dict[str, str], bool]:
        template = self.server.get_template(name=name)
        if template is None:
            templ_exists = False
        else:
            templ_exists = True
        return template, templ_exists


class GNS3NodeBuilder:
    def __init__(self, server):
        self.server = server

    def update(self, node: models.Node):
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")
        try:
            node._provider.get()
            node.is_created = True
            set_node_attributes(node)
        except Exception:
            # TODO: To be fixed once the issue is solved on gns3fy
            node.is_created = False

    def set_provider(self, node: models.Node, project: models.Project):
        node._provider = gns3fy.Node(
            name=node.name, project_id=project.id, connector=self.server
        )

    def retrieve(self, node: models.Node, project: models.Project) -> bool:
        self.set_provider(node, project)
        self.update(node)
        if not node.is_created:
            return False
        return True

    def create(self, node: models.Node) -> bool:
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")
        if node._provider.template is None:
            node._provider.template = node.template
            if node._provider.template is None:
                raise ValueError("Node cannot be created -> 'template' is needed")

        # Create and update
        node._provider.create()
        self.update(node)
        if not node.is_created:
            return False
        return True

    def delete(self, node: models.Node) -> bool:
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Stop and delete
        node._provider.stop()
        node._provider.delete()

        # Verify object deleation
        self.update(node)
        if node.is_created:
            return False

        # Init some attributes
        node._provider = None
        node.id = None
        node.status = None
        node.template = None
        node.console = None
        node.category = None
        node.interfaces = None
        node.properties = None
        return True

    def start(self, node: models.Node) -> bool:
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Refresh and validate
        node._provider.start()
        self.update(node)
        if node.status != "started":
            return False
        return True

    def stop(self, node: models.Node) -> bool:
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Refresh and validate
        node._provider.stop()
        self.update(node)
        if node.status != "stopped":
            return False
        return True

    def reload(self, node: models.Node) -> bool:
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Refresh and validate
        node._provider.reload()
        self.update(node)
        if node.status != "started":
            return False
        return True

    def suspend(self, node: models.Node) -> bool:
        if node._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Refresh and validate
        node._provider.suspend()
        self.update(node)
        if node.status != "suspended":
            return False
        return True


class GNS3ConnectionBuilder:
    def __init__(self, server):
        self.server = server

    def _get_link(
        self,
        project: gns3fy.Project,
        node_a: str,
        port_a: str,
        node_b: str,
        port_b: str,
    ) -> Tuple[gns3fy.Link, bool]:
        _node_a = project.get_node(name=node_a)  # type: ignore
        if not _node_a:
            raise ValueError(f"node_a: {node_a} not found")
        try:
            _port_a = [_p for _p in _node_a.ports if _p["name"] == port_a][0]
        except IndexError:
            raise ValueError(f"port_a: {port_a} not found")

        _node_b = project.get_node(name=node_b)  # type: ignore
        if not _node_b:
            raise ValueError(f"node_b: {node_b} not found")
        try:
            _port_b = [_p for _p in _node_b.ports if _p["name"] == port_b][0]
        except IndexError:
            raise ValueError(f"port_b: {port_b} not found")

        _matches = []
        for _l in project.links:  # type: ignore
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

        return link, link_exists  # type: ignore

    def update(self, connection: models.Connection):
        if connection._provider is None:
            raise ValueError("GNS3 Provider not initialized")
        try:
            connection._provider.get()
            connection.is_created = True
            set_connection_attributes(connection)
        except Exception:
            # TODO: To be fixed once the issue is solved on gns3fy
            connection.is_created = False

    def set_provider(self, connection: models.Connection, project: models.Project):
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")
        if connection.endpoints is None:
            raise ValueError("Need to have 'endpoints' defined to create connection")
        _provider, link_exists = self._get_link(
            project=project._provider,
            node_a=connection.endpoints[0]["name"],
            port_a=connection.endpoints[0]["port"],
            node_b=connection.endpoints[1]["name"],
            port_b=connection.endpoints[1]["port"],
        )
        if not link_exists:
            connection.is_created = False
        else:
            connection.is_created = True
            connection._provider = _provider

    def retrieve(self, connection: models.Connection, project: models.Project) -> bool:
        self.set_provider(connection, project)
        if not connection.is_created:
            return False
        self.update(connection)
        return True

    def create(self, connection: models.Connection, project: models.Project) -> bool:
        # if connection._provider is None or project._provider is None:
        #     raise ValueError("GNS3 Provider not initialized")
        if project._provider is None:
            raise ValueError("GNS3 Provider not initialized")
        if connection.endpoints is None:
            raise ValueError("Connection cannot be created -> 'endpoints' is needed")
        if len(connection.endpoints) != 2:
            raise ValueError(
                "Connection cannot be created -> 'endpoints' must have 2 endpoints"
            )
        # Create connection
        project._provider.create_link(
            node_a=connection.endpoints[0]["name"],
            port_a=connection.endpoints[0]["port"],
            node_b=connection.endpoints[1]["name"],
            port_b=connection.endpoints[1]["port"],
        )
        # Set provider and update attributes in connection
        return self.retrieve(connection, project)

    def delete(self, connection: models.Connection) -> bool:
        if connection._provider is None:
            raise ValueError("GNS3 Provider not initialized")

        # Verify object deleation
        connection._provider.delete()
        self.update(connection)
        if connection.is_created:
            return False

        # Init some attributes
        connection._provider = None
        connection.id = None
        connection.type = None
        connection.endpoints = None
        return True
