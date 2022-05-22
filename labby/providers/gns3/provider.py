"""GNS3 main provider module."""
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value
import time
from typing import List, Optional

import typer
from rich.table import Table
from rich.console import ConsoleRenderable
from gns3fy.server import Server

from labby.providers.gns3.template import GNS3NodeTemplate
from labby.models import LabbyProvider
from labby.utils import console
from labby import lock_file
from labby.providers.gns3.project import GNS3Project
from labby.providers.gns3.utils import bool_status, project_status, string_status, template_type


class GNS3Provider(LabbyProvider):
    """GNS3 provider class."""

    def __init__(
        self,
        name: str,
        server_url: str,
        kind: str = "gns3",
        user: Optional[str] = None,
        password: Optional[str] = None,
        verify_cert: bool = False,
    ):
        """GNS3 provider class.

        Args:
            name (str): Name of the GNS3 provider
            server_url (str): GNS3 server URL
            kind (str, optional): Type of GNS3 server (default: gns3)
            user (Optional[str], optional): User to login to GNS3 server
            password (Optional[str], optional): Password to login to GNS3 server
            verify_cert (bool, optional): Verify the server's SSL certificate (default: False)
        """
        super().__init__(name=name, kind=kind)
        self._base: Server = Server(url=server_url, user=user, cred=password, verify=verify_cert)

    def search_project(self, project_name: str) -> Optional[GNS3Project]:
        """Search a project in the GNS3 server.

        Args:
            project_name (str): Name of the project to search

        Returns:
            Optional[GNS3Project]: Project object or None
        """
        r_gns3_project = self._base.search_project(project_name)
        if not r_gns3_project:
            return None

        # Retrive info from lock file
        project_lock_file_data = lock_file.get_project_data(project_name)
        if project_lock_file_data is None:
            _project = GNS3Project(project_name, r_gns3_project)
            lock_file.apply_project_data(_project)
        else:
            labels = project_lock_file_data["labels"]
            _project = GNS3Project(project_name, r_gns3_project, labels=labels)
        console.log(_project)

        return _project

    def create_project(self, project_name: str, labels: List[str] = [], **kwargs) -> GNS3Project:
        """Create a project in the GNS3 server.

        Args:
            project_name (str): Name of the project to create
            labels (List[str], optional): List of labels to apply to the project

        Returns:
            GNS3Project: Project object
        """
        _project = self.search_project(project_name)

        if _project:
            console.log(f"Project [cyan i]{project_name}[/] already created. Nothing to do...", style="warning")
            return _project

        console.log(f"[b]({project_name})[/] Creating project")
        gns3_project = self._base.create_project(project_name)
        project = GNS3Project(project_name, gns3_project, labels, **kwargs)
        time.sleep(2)
        # console.log(project)
        console.log(f"[b]({project_name})[/] Project created", style="good")
        lock_file.apply_project_data(project)
        return project

    def search_template(self, template_name: str) -> Optional[GNS3NodeTemplate]:
        """Search a template in the GNS3 server.

        Args:
            template_name (str): Name of the template to search

        Returns:
            Optional[GNS3NodeTemplate]: Template object or None
        """
        gns3_template = self._base.search_template(template_name)
        if not gns3_template:
            return None

        template = GNS3NodeTemplate(name=template_name, template=gns3_template)
        return template

    def create_template(self, template_name: str, labels: List[str] = [], **data) -> GNS3NodeTemplate:
        """Create a template in the GNS3 server.

        Args:
            template_name (str): Name of the template to create
            labels (List[str], optional): List of labels to apply to the template

        Raises:
            typer.Exit: Attribute template_type must be set

        Returns:
            GNS3NodeTemplate: Template object
        """
        template = self.search_template(template_name)

        if template:
            console.log(f"Node Template [cyan i]{template.name}[/] already created. Nothing to do...", style="warning")
            return template

        console.log(f"[b]({template_name})[/] Creating node template")
        if not data.get("template_type"):
            console.log("Attribute `template_type` must be set", style="error")
            raise typer.Exit(1)
        gns3_template = self._base.create_template(name=template_name, template_type=data["template_type"], **data)
        template = GNS3NodeTemplate(name=template_name, template=gns3_template, labels=labels, **data)
        time.sleep(2)
        console.log(template)
        console.log(f"[b]({template.name})[/] Template created", style="good")
        return template

    def render_templates_list(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        """Render templates list.

        Args:
            field (Optional[str], optional): Field to filter on
            value (Optional[str], optional): Value to filter on

        Returns:
            ConsoleRenderable: Table
        """ """
        """
        table = Table(title="GNS3 Templates", highlight=True)
        table.add_column("Device Template")
        table.add_column("Category")
        table.add_column("Type")
        table.add_column("Builtin")
        table.add_column("First/Mgmt Port")
        table.add_column("Image")
        self._base.get_templates()
        if field:
            templates = [x for x in self._base.templates.values() if getattr(x, field) == value]
        else:
            templates = self._base.templates.values()
        for template in templates:
            table.add_row(
                template.name,
                template.category,
                template_type(template.template_type),
                bool_status(template.builtin),
                string_status(getattr(template, "first_port_name", "N/A")),
                string_status(getattr(template, "hda_disk_image", "N/A")),
            )
        return table

    def render_project_list(
        self, field: Optional[str] = None, value: Optional[str] = None, labels: Optional[List[str]] = []
    ) -> ConsoleRenderable:
        """Render project list.

        Args:
            field (Optional[str], optional): Field to filter on
            value (Optional[str], optional): Value to filter on
            labels (Optional[List[str]], optional): List of labels to filter on

        Returns:
            ConsoleRenderable: Table
        """
        table = Table(title="GNS3 Projects", highlight=True)
        table.add_column("Project Name")
        table.add_column("Status")
        table.add_column("Auto Start")
        table.add_column("Auto Close")
        table.add_column("Auto Open")
        table.add_column("Labels")
        self._base.get_projects()
        if field:
            projects = [x for x in self._base.projects.values() if getattr(x, field) == value]
        else:
            projects = list(self._base.projects.values())
        for prj in projects:
            if prj is None:
                continue

            # Get labels from lock file
            project_lock_file_data = lock_file.get_project_data(prj.name)  # type: ignore
            project_labels = project_lock_file_data["labels"] if project_lock_file_data else []

            # Skip project if labels are not present
            if labels:
                if not any(x in project_labels for x in labels):
                    continue

            table.add_row(
                prj.name,
                project_status(prj.status),
                bool_status(prj.auto_start),
                bool_status(prj.auto_close),
                bool_status(prj.auto_open),
                str(project_labels),
            )
        return table
