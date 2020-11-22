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
from rich.console import Console


console = Console()


class GNS3Provider(ProvidersBase):
    def __init__(self, url, user, cred, verify):
        self.server = gns3fy.Gns3Connector(url=url, user=user, cred=cred, verify=verify)
        # Test connectivity
        # self.version = self.server.get_version()
        self.project_builder = GNS3ProjectBuilder(server=self.server)
        self.node_builder = GNS3NodeBuilder(server=self.server)
        self.connection_builder = GNS3ConnectionBuilder(server=self.server)
        self.reporter = Reports(server=self.server)
        self.provisioner = Provision(self.server)

    def get_project_details(self, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Project Summary Table
        console.print(
            self.reporter.table_project_summary(project=project), justify="center"
        )

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Nodes Summary Table
        console.print()
        console.print(
            self.reporter.table_nodes_summary(project=project), justify="center"
        )

        # Links Summary table
        console.print()
        console.print(
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
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Nodes Summary Table
        console.print()
        console.print(
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
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Links Summary Table
        console.print()
        console.print(
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
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.connection_builder.retrieve(connection, project):
            console.print(
                f"No connection: [cyan]{connection.name}[/] found. Nothing to do..."
            )
            return

        # Link information
        console.print(
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
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.print()
        console.print(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.print()
        console.print(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Nodes Properties
        console.print()
        console.print(
            self.reporter.table_node_properties_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def get_template_details(self, name: str):
        # Retrieve template
        template, templ_exists = self.project_builder.get_template(name)
        if not templ_exists:
            console.print(f"No template named [cyan]{name}[/] found. Nothing to do...")
            return

        # Template Table
        console.print("[italic]Template parameters[/]", justify="center")
        console.print(
            self.reporter.table_template_detail(template=template), justify="center"
        )

    def create_project(self, project: models.Project):
        # TODO: Wrapper could be set to check project existence
        # Retrieve project
        if self.project_builder.retrieve(project):
            console.print(
                f"Project {project.name} is already created. Nothing to do..."
            )
            return

        # Create project
        if self.project_builder.create(project=project):
            console.print(f"[green]Created[/] project: [cyan]{project.name}[/]")
        else:
            console.print("[red]Project could not be created[/]")

        # Project Summary Table
        console.print()
        console.print(
            self.reporter.table_project_summary(project=project), justify="center"
        )

    def delete_project(self, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Delete project
        if self.project_builder.delete(project=project):
            console.print(f"[red]Deleted[/] project: [cyan]{project.name}[/]")
        else:
            console.print("[red]Project could not be deleted[/]")

    def start_project(
        self, project: models.Project, start_nodes: str = "none", nodes_delay: int = 5
    ):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Start project
        if self.project_builder.start(
            project=project, start_nodes=start_nodes, nodes_delay=nodes_delay
        ):
            console.print(f"[green]Started[/] project: [cyan]{project.name}[/]")
        else:
            console.print("[red]Project could not be started[/]")

        # Project Summary Table
        console.print()
        console.print(
            self.reporter.table_project_summary(project=project), justify="center"
        )

    def stop_project(self, project: models.Project, stop_nodes: bool = True):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Stop project
        if self.project_builder.stop(project=project, stop_nodes=stop_nodes):
            console.print(f"[red]Stopped[/] project: [cyan]{project.name}[/]")
        else:
            console.print("[red]Project could not be started[/]")

        # TODO: Currently there is a bug that cannot display stats if project is closed
        # # Project Summary Table
        # console.print()
        # console.print(
        #     self.reporter.table_project_summary(project=project), justify="center"
        # )

    def create_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if self.node_builder.retrieve(node, project):
            console.print(f"Node [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Create node
        if self.node_builder.create(node=node):
            console.print(f"[green]Created[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be created[/]")

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.print()
        console.print(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def delete_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Delete node
        if self.node_builder.delete(node=node):
            console.print(f"[red]Deleted[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be deleted[/]")

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def start_node(self, node: models.Node, project: models.Project):
        # TODO: Wrapper for actions on nodes!
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Start node
        if self.node_builder.start(node=node):
            console.print(f"[green]Started[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be started[/]")

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.print()
        console.print(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.print()
        console.print(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def stop_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Stop node
        if self.node_builder.stop(node=node):
            console.print(f"[red]Stopped[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be stopped[/]")

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.print()
        console.print(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.print()
        console.print(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def reload_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Reload node
        if self.node_builder.reload(node=node):
            console.print(f"[yellow]Reloaded[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be reloaded[/]")

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.print()
        console.print(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.print()
        console.print(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def suspend_node(self, node: models.Node, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Suspend node
        if self.node_builder.suspend(node=node):
            console.print(f"[yellow]Suspended[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be suspended[/]")

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Nodes Ports
        console.print()
        console.print(
            self.reporter.table_node_ports_detail(node),
            justify="center",
        )

        # Nodes Links
        console.print()
        console.print(
            self.reporter.table_node_links_detail(node),
            justify="center",
        )

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def create_connection(self, connection: models.Connection, project: models.Project):
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve connection
        if self.connection_builder.retrieve(connection, project):
            console.print(
                f"Connection [cyan]{connection.name}[/] found. Nothing to do..."
            )
            return

        # Create connection
        if self.connection_builder.create(connection=connection, project=project):
            console.print(f"[green]Created[/] connection: [cyan]{connection.name}[/]")
        else:
            console.print("[red]Connection could not be created[/]")

        # Link information
        console.print(
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
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Prep project for nodes and links and get initial status
        initial_status = self.project_builder.prep_status(project)

        # Retrieve connection
        if not self.connection_builder.retrieve(connection, project):
            console.print(
                f"No connection [cyan]{connection.name}[/] found. Nothing to do..."
            )
            return

        # Create connection
        if self.connection_builder.delete(connection=connection):
            console.print(f"[red]Deleted[/] connection: [cyan]{connection.name}[/]")
        else:
            console.print("[red]Connection could not be deleted[/]")

        # Set project back to its original state
        self.project_builder.post_status(project, initial_status)

    def bootstrap_node(
        self, node: models.Node, project: models.Project, config: Path, device_type: str
    ):
        # TODO: Wrapper for actions on nodes!
        # Retrieve project
        if not self.project_builder.retrieve(project):
            console.print(
                f"No project named [cyan]{project.name}[/] found. Nothing to do..."
            )
            return

        # Project must be opened
        if project.status != "opened":
            console.print(f"Project [cyan]{project.name}[/] must been opened.")
            return

        # Retrieve node
        if not self.node_builder.retrieve(node, project):
            console.print(f"No node named [cyan]{node.name}[/] found. Nothing to do...")
            return

        # Nodes information
        console.print(
            self.reporter.table_node_detail(node),
            justify="center",
        )

        # Bottstrapping node
        console.print(
            f"\nRunning bootstrap for [cyan]{node.name}[/] on [cyan]{project.name}[/]\n"
        )
        if self.provisioner.bootstrap(
            node=node, project=project, config=config, device_type=device_type
        ):
            console.print(f"[green]Bootstrapped[/] node: [cyan]{node.name}[/]")
        else:
            console.print("[red]Node could not be configured[/]")


class GNS3ProviderBuilder:
    def __init__(self):
        self._instance = None

    def __call__(
        self,
        gns3_server_url,
        gns3_user=None,
        gns3_password=None,
        gns3_verify=False,
        **_ignored,
    ):
        if not self._instance:
            self._instance = GNS3Provider(
                url=gns3_server_url,
                user=gns3_user,
                cred=gns3_password,
                verify=gns3_verify,
            )
        return self._instance

    def authorize(self, key, secret):
        return "GNS3_CONSUMER_KEY", "GNS3_CONSUMER_SECRET"
