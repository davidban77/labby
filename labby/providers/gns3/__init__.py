from pathlib import Path
import gns3fy
import labby.models as models

from typing import Optional
from labby.providers.gns3.provision import Provision
from labby.providers.gns3.reporter import Reports
from labby.providers.gns3.builders import (
    GNS3ConnectionBuilder,
    GNS3NodeBuilder,
    GNS3ProjectBuilder,
)
from labby.providers.base import ProvidersBase
from labby.utils import console


class GNS3Provider(ProvidersBase):
    def __init__(self, url, user, cred, verify):
        if url is None:
            raise ValueError("No GNS3 server url specified")

        self.url = url
        self.server = gns3fy.Gns3Connector(url=url, user=user, cred=cred, verify=verify)

        self.project_builder = GNS3ProjectBuilder(server=self.server)
        self.node_builder = GNS3NodeBuilder(server=self.server)
        self.connection_builder = GNS3ConnectionBuilder(server=self.server)
        self.reporter = Reports(server=self.server)
        self.provisioner = Provision(self.server)

    def get_project_web_url(self, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return
        return f"{self.url}/static/web-ui/server/1/project/{project.id}"

    def get_version(self):
        return self.server.get_version()["version"]

    def get_project_details(self, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Project Summary Table
        console.log(
            self.reporter.table_project_summary(project=project), justify="center"
        )

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Nodes Summary Table
        console.log()
        console.log(
            self.reporter.table_nodes_summary(project=project), justify="center"
        )

        # Links Summary table
        console.log()
        console.log(
            self.reporter.table_links_summary(project=project), justify="center"
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def get_nodes_list(
        self,
        project: models.Project,
        field: Optional[str] = None,
        value: Optional[str] = None,
    ):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Nodes Summary Table
        console.log()
        console.log(
            self.reporter.table_nodes_summary(
                project=project, field=field, value=value
            ),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def get_connections_list(
        self,
        project: models.Project,
        field: Optional[str] = None,
        value: Optional[str] = None,
    ):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Links Summary Table
        console.log()
        console.log(
            self.reporter.table_links_summary(
                project=project, field=field, value=value
            ),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def get_connection_details(
        self,
        connection: models.Connection,
        project: models.Project,
    ):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.connection_builder.retrieve(connection, project):
            console.log(
                f"No connection: [cyan]{connection.name}[/] found. Nothing to do..."
            )
            return

        # Link information
        console.log(
            self.reporter.table_links_summary(
                project=project, field="link_id", value=connection.id
            ),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def get_node_details(
        self,
        node: models.Node,
        project: models.Project,
    ):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.log()
        console.log(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.log()
        console.log(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Nodes Properties
        console.log()
        console.log(
            self.reporter.table_node_properties_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def get_template_details(self, name: str):
        # Retrieve template
        template, templ_exists = self.project_builder.get_template(name)
        if not templ_exists:
            console.log(f"No template named [cyan]{name}[/] found. Nothing to do...")
            return

        # Template Table
        console.log("[italic]Template parameters[/]", justify="center")
        console.log(
            self.reporter.table_template_detail(template=template), justify="center"
        )

    def create_project(self, project: models.Project):
        # TODO: Wrapper could be set to check project existence
        # Retrieve project
        if self.project_builder.retrieve(project):
            console.log(
                f"Project {project.name} is already created. Nothing to do..."
            )
            return

        # Create project
        if self.project_builder.create(project=project):
            console.log(f"[green]Created[/] project: [cyan]{project.name}[/]")
        else:
            console.log("[red]Project could not be created[/]")

        # Project Summary Table
        console.log()
        console.log(
            self.reporter.table_project_summary(project=project), justify="center"
        )

    def delete_project(self, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Delete project
        if self.project_builder.delete(project=project):
            console.log(f"[red]Deleted[/] project: [cyan]{project.name}[/]")
        else:
            console.log("[red]Project could not be deleted[/]")

    def start_project(
        self, project: models.Project, start_nodes: str = "none", nodes_delay: int = 5
    ):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Start project
        if self.project_builder.start(
            project=project, start_nodes=start_nodes, nodes_delay=nodes_delay
        ):
            console.log(f"[green]Started[/] project: [cyan]{project.name}[/]")
        else:
            console.log("[red]Project could not be started[/]")

        # Project Summary Table
        console.log()
        console.log(
            self.reporter.table_project_summary(project=project), justify="center"
        )

    def stop_project(self, project: models.Project, stop_nodes: bool = True):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Stop project
        if self.project_builder.stop(project=project, stop_nodes=stop_nodes):
            console.log(f"[red]Stopped[/] project: [cyan]{project.name}[/]")
        else:
            console.log("[red]Project could not be started[/]")

        # TODO: Currently there is a bug that cannot display stats if project is closed
        # # Project Summary Table
        # console.log()
        # console.log(
        #     self.reporter.table_project_summary(project=project), justify="center"
        # )

    def create_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if self.node_builder.retrieve(node, project):
            console.log(f"Node [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Create node
        if self.node_builder.create(node=node):
            console.log(f"[green]Created[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be created[/]")

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.log()
        console.log(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def delete_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Delete node
        if self.node_builder.delete(node=node):
            console.log(f"[red]Deleted[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be deleted[/]")

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def start_node(self, node: models.Node, project: models.Project):
        # TODO: Wrapper for actions on nodes!
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Start node
        if self.node_builder.start(node=node):
            console.log(f"[green]Started[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be started[/]")

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.log()
        console.log(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.log()
        console.log(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def stop_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Stop node
        if self.node_builder.stop(node=node):
            console.log(f"[red]Stopped[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be stopped[/]")

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.log()
        console.log(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.log()
        console.log(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def reload_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Reload node
        if self.node_builder.reload(node=node):
            console.log(f"[yellow]Reloaded[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be reloaded[/]")

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.log()
        console.log(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.log()
        console.log(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def suspend_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Suspend node
        if self.node_builder.suspend(node=node):
            console.log(f"[yellow]Suspended[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be suspended[/]")

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.log()
        console.log(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.log()
        console.log(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def create_connection(self, connection: models.Connection, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve connection
        if self.connection_builder.retrieve(connection, project):
            console.log(
                f"Connection [cyan]{connection.name}[/] found. Nothing to do..."
            )
            return

        # Create connection
        if self.connection_builder.create(connection=connection, project=project):
            console.log(f"[green]Created[/] connection: [cyan]{connection.name}[/]")
        else:
            console.log("[red]Connection could not be created[/]")

        # Link information
        console.log(
            self.reporter.table_links_summary(
                project=project, field="link_id", value=connection.id
            ),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def delete_connection(self, connection: models.Connection, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve connection
        if not self.connection_builder.retrieve(connection, project):
            console.log(
                f"No connection [cyan]{connection.name}[/] found. Nothing to do..."
            )
            return

        # Create connection
        if self.connection_builder.delete(connection=connection):
            console.log(f"[red]Deleted[/] connection: [cyan]{connection.name}[/]")
        else:
            console.log("[red]Connection could not be deleted[/]")

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def bootstrap_node(
        self, node: models.Node, project: models.Project, config: Path, device_type: str
    ):
        # TODO: Wrapper for actions on nodes!
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.log(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Project must be opened
        if project.status != "opened":
            console.log(f"Project [cyan]{project.name}[/] must been opened.")
            return

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.log(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Nodes information
        console.log(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Bottstrapping node
        console.log(
            f"\nRunning bootstrap for [cyan]{node.name}[/] on [cyan]{project.name}[/]\n"
        )
        if self.provisioner.bootstrap(
            node=node, project=project, config=config, device_type=device_type
        ):
            console.log(f"[green]Bootstrapped[/] node: [cyan]{node.name}[/]")
        else:
            console.log("[red]Node could not be configured[/]")


class GNS3ProviderBuilder:
    def __init__(self):
        self._instance = None

    def __call__(
        self,
        server_url,
        user=None,
        password=None,
        verify_cert=False,
        **_ignored,
    ):
        if not self._instance:
            self._instance = GNS3Provider(
                url=server_url,
                user=user,
                cred=password,
                verify=verify_cert,
            )
        return self._instance

    def authorize(self, key, secret):
        return "GNS3_CONSUMER_KEY", "GNS3_CONSUMER_SECRET"
