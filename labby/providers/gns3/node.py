"""GNS3 Node module."""
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value
import time
import re
from typing import Dict, List, Optional

import typer
from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult, Group
from rich.scope import render_scope
from rich.table import Table
from rich.panel import Panel
from rich import box
from nornir.core.task import Task, AggregatedResult, Result
from nornir_scrapli.tasks import send_config
from gns3fy.templates import Template, get_templates
from gns3fy.nodes import Node
from gns3fy.ports import Port

import labby.providers.gns3.console_provisioner as node_console
from labby import config, lock_file
from labby.providers.gns3.utils import node_net_os, node_status
from labby.utils import console, dissect_url
from labby.nornir_tasks import backup_task, SHOW_RUN_COMMANDS
from labby.models import LabbyNode, LabbyProjectInfo, LabbyPort


def config_task(task: Task, config: str):
    # pylint: disable=redefined-outer-name
    """Taks for configuring a node.

    Args:
        task (Task): Nornir task object
        config (str): Node configuration
    """
    task.run(task=send_config, config=config)


def dissect_gns3_template_name(template_name: str) -> Optional[Dict[str, str]]:
    """Parse the template name to get the net_os, model and version.

    Args:
        template_name (str): Node template name

    Returns:
        Optional[Dict[str, str]]: Returns net_os, model and version if found
    """
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


class GNS3Port(LabbyPort):
    # pylint: disable=too-few-public-methods
    """GNS3 Labby port object."""

    def __init__(self, name: str, kind: str, port: Port) -> None:
        """GNS3 Labby port object.

        Args:
            name (str): Name of the port
            kind (str): Type of the port
            port (Port): GNS3 port object
        """
        super().__init__(name=name, kind=kind)
        self._base = port


class GNS3Node(LabbyNode):
    # pylint: disable=too-many-instance-attributes
    """GNS3 Labby node object."""

    builtin: bool = False
    _base: Node
    _template: Optional[Template]

    def __init__(
        self,
        name: str,
        template: str,
        project_name: str,
        node: Node,
        labels: List[str] = [],
        mgmt_addr: Optional[str] = None,
        mgmt_port: Optional[str] = None,
        config_managed: bool = True,
        **data,
    ) -> None:
        """GNS3 Labby node object.

        Args:
            name (str): GNS3 node name
            template (str): GNS3 node template name
            project_name (str): GNS3 project name
            node (Node): GNS3 node object
            labels (List[str], optional): Labels for the node. Defaults to [].
            mgmt_addr (Optional[str], optional): Management address. Defaults to None.
            mgmt_port (Optional[str], optional): Management port. Defaults to None.
            config_managed (bool, optional): Whether the node is managed by the labby. Defaults to False.
        """
        _project = LabbyProjectInfo(name=project_name, id=node.project_id)
        super().__init__(
            name=name,
            labels=labels,
            template=template,
            project=_project,
            _base=node,  # type: ignore
            mgmt_addr=mgmt_addr,
            mgmt_port=mgmt_port,
            config_managed=config_managed,
            **data,
        )
        self._template = self._get_gns3_template()
        self._update_labby_node_attrs()

    def _update_labby_node_attrs(self):
        """Updates the Labby node attributes.

        Raises:
            ValueError: If the port name or link type info is not available.
            typer.Exit: If the mgmt_port is not part of the node interfaces
        """
        self.id = self._base.node_id  # pylint: disable=invalid-name
        self.console = self._base.console
        self.status = self._base.status
        self.kind = self._base.node_type
        _interfaces = {}
        for puerto in self._base.ports:
            if puerto.name and puerto.link_type:
                _interfaces.update({puerto.name: GNS3Port(name=puerto.name, kind=puerto.link_type, port=puerto)})
            else:
                raise ValueError(f"Port name or link type info not available: {puerto} -> {self.name}")
        self.interfaces = _interfaces
        self.properties = self._base.properties

        # Validate mgmt_port
        if self.mgmt_port is not None and self.mgmt_port not in self.interfaces:
            console.log(f"Mgmt Port {self.mgmt_port} is not part of the node interfaces", style="error")
            raise typer.Exit(1)

        # Update attributes from template
        if self._template is not None:
            self.category = self._template.category
            self.builtin = self._template.builtin

        if self.template:
            node_data = dissect_gns3_template_name(self.template)
            if node_data:
                self.net_os = node_data["net_os"]
                self.model = node_data["model"]
                self.version = node_data["version"]

    def _get_gns3_template(self) -> Template:
        """Get the GNS3 template object.

        Raises:
            ValueError: If the template name is not available.
            ValueError: If the template is not found.

        Returns:
            Template: GNS3 template object
        """
        if not self.template:
            raise ValueError(f"Node Template must be specified {self.name}")

        _templates = get_templates(self._base._connector)
        try:
            tplt = next(_t for _t in _templates if _t.name == self.template)
        except StopIteration as err:
            raise ValueError(f"Node template not found: {self.template}") from err

        return tplt

    def get(self) -> None:
        """Get the node attributes."""
        console.log(f"[b]({self.project.name})({self.name})[/] Collecting node data")
        self._base.get()
        self._update_labby_node_attrs()

    def start(self) -> bool:
        """Starts the node.

        Returns:
            bool: True if the node is started, False otherwise.
        """
        console.log(f"[b]({self.project.name})({self.name})[/] Starting node")
        self._base.start()
        time.sleep(2)

        self.get()

        if self.status != "started":
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be started", style="warning")
            return False

        console.log(f"[b]({self.project.name})({self.name})[/] Node started", style="good")
        return True

    def stop(self) -> bool:
        """Stops the node.

        Returns:
            bool: True if the node is stopped, False otherwise.
        """
        console.log(f"[b]({self.project.name})({self.name})[/] Stopping node")
        self._base.stop()
        time.sleep(2)

        self.get()

        if self.status != "stopped":
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be stopped", style="warning")
            return False

        console.log(f"[b]({self.project.name})({self.name})[/] Node stopped", style="good")
        return True

    def restart(self) -> bool:
        """Restarts the node.

        Returns:
            bool: True if the node is restarted, False otherwise.
        """
        console.log(f"[b]({self.project.name})({self.name})[/] Retarting node")
        self._base.reload()
        time.sleep(2)

        self.get()

        if self.status != "started":
            console.log(f"[b]({self.project.name})({self.name})[/] Node could not be restarted", style="warning")
            return False

        console.log(f"[b]({self.project.name})({self.name})[/] Node restarted", style="good")
        return True

    def update(self, **kwargs) -> None:
        """Updates the node attributes.

        Raises:
            typer.Exit: If the mgmt_port is not part of the node interfaces
        """
        if self.status != "started":
            self.start()

        console.log(f"[b]({self.project.name})({self.name})[/] Updating node: {kwargs}", highlight=True)
        if "labels" in kwargs:
            self.labels = kwargs["labels"]
        elif "config_managed" in kwargs:
            self.config_managed = kwargs["config_managed"]
        elif "mgmt_addr" in kwargs:
            self.mgmt_addr = kwargs["mgmt_addr"]
        elif "mgmt_port" in kwargs:
            self.mgmt_port = kwargs["mgmt_port"]
            if self.mgmt_port not in self.interfaces:
                console.log(f"Mgmt Port {self.mgmt_port} is not part of the node interfaces", style="error")
                raise typer.Exit(1)
        else:
            self._base.update(**kwargs)
        time.sleep(2)

        self.get()
        console.log(f"[b]({self.project.name})({self.name})[/] Node updated", style="good")
        lock_file.apply_node_data(self)

    def delete(self) -> bool:
        """Deletes the node.

        Returns:
            bool: True if the node is deleted, False otherwise.
        """
        console.log(f"[b]({self.project.name})({self.name})[/] Deleting node")
        node_deleted = self._base.delete()
        time.sleep(2)

        if node_deleted:
            self.id = None
            self.status = "deleted"
            console.log(f"[b]({self.project.name})({self.name})[/] Node deleted", style="good")
            lock_file.delete_node_data(self.name, self.project.name)
            return True

        console.log(f"[b]({self.project.name})({self.name})[/] Node could not be deleted", style="warning")
        return False

    def bootstrap(self, config: str, boot_delay: int = 5, delay_multiplier: int = 1) -> bool:
        # pylint: disable=redefined-outer-name
        """Bootstraps the node.

        Args:
            config (str): The bootstrap configuration file.
            boot_delay (int, optional): The boot delay in seconds. Defaults to 5.
            delay_multiplier (int, optional): The delay multiplier. Defaults to 1.

        Raises:
            typer.Exit: If the GNS3 server host could not be parsed

        Returns:
            bool: True if the node is bootstrapped, False otherwise.
        """
        with console.status(
            f"[b]({self.project.name})({self.name})[/] Bootstraping node", spinner="aesthetic"
        ) as status:
            console.log(f"[b]({self.project.name})({self.name})[/] Bootstraping node")
            console.log(self)
            if self.status != "started":
                status.update(status=f"[b]({self.project.name})({self.name})[/] Starting node")
                self.start()
                status.update(status=f"[b]({self.project.name})({self.name})[/] Waiting for node to warmup")
                time.sleep(boot_delay)
            else:
                status.update(status=f"[b]({self.project.name})({self.name})[/] Restarting node")
                self.restart()
                status.update(status=f"[b]({self.project.name})({self.name})[/] Waiting for node to warmup")
                time.sleep(boot_delay)

        server_host = dissect_url(self._base._connector.base_url)[1]
        if not server_host:
            console.log(f"[b]({self.project.name})({self.name})[/] GNS3 server host could not be parsed", style="error")
            raise typer.Exit(1)

        console.log(f"[b]({self.project.name})({self.name})[/] Running bootstrap configuration process")
        response = node_console.run_action(
            action="bootstrap", server_host=server_host, data=config, node=self, delay_multiplier=delay_multiplier
        )

        if not response.failed:
            console.log(f"[b]({self.project.name})({self.name})[/] Bootstrapped node", style="good")
            console.rule(title=f"Start of bootstrap capture for: [b cyan]{self.name}")
            console.print(response.result, highlight=True)
            console.rule(title=f"End of bootstrap capture for: [b cyan]{self.name}")
            return True

        console.print(response.result, highlight=True)
        console.log(f"[b]({self.project.name})({self.name})[/] Node could not be configured", style="error")
        return False

    def apply_config(self, config: str, user: Optional[str] = None, password: Optional[str] = None) -> bool:
        # pylint: disable=redefined-outer-name
        """Applies the configuration file to the node.

        Args:
            config (str): The configuration file.
            user (Optional[str], optional): The user to login to the node. Defaults to None.
            password (Optional[str], optional): The password to login to the node. Defaults to None.

        Raises:
            ValueError: If the nornir object is not properly initialized.

        Returns:
            bool: True if the configuration is applied, False otherwise.
        """
        if self.nornir is None:
            raise ValueError(f"Check nornir object is not initialized fot the node: {self.name}")

        if self.status != "started":
            self.start()
            time.sleep(30)

        console.log(f"[b]({self.project.name})({self.name})[/] Applying configuration")
        result: AggregatedResult = self.nornir.run(task=config_task, config=config, name="apply config")
        console.rule(title=f"Start of configuration applied for: [b cyan]{self.name}")
        console.print(result[self.name][-1], highlight=True)
        console.rule(title=f"End of configuration applied for: [b cyan]{self.name}")
        try:
            result.raise_on_error()
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    def apply_config_over_console(
        self,
        config: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        delay_multiplier: int = 1,
    ) -> bool:
        # pylint: disable=redefined-outer-name
        """Applies the configuration file to the node over the console.

        Args:
            config (str): The configuration file.
            user (Optional[str], optional): The user to login to the node. Defaults to None.
            password (Optional[str], optional): The password to login to the node. Defaults to None.
            delay_multiplier (int, optional): The delay multiplier. Defaults to 1.

        Raises:
            typer.Exit: If the GNS3 server host could not be parsed

        Returns:
            bool: True if the configuration is applied, False otherwise.
        """
        if self.status != "started":
            self.start()
            time.sleep(30)

        server_host = dissect_url(self._base._connector.base_url)[1]
        if not server_host:
            console.log(f"[b]({self.project.name})({self.name})[/] GNS3 server host could not be parsed", style="error")
            raise typer.Exit(1)

        console.log(f"[b]({self.project.name})({self.name})[/] Applying configuration over console")
        response = node_console.run_action(
            action="config",
            server_host=server_host,
            data=config,
            node=self,
            user=user,
            password=password,
            delay_multiplier=delay_multiplier,
        )

        if not response.failed:
            console.log(f"[b]({self.project.name})({self.name})[/] Node configured over console", style="good")
            console.rule(title=f"Start of config applied for: [b cyan]{self.name}")
            console.print(response.result, highlight=True)
            console.rule(title=f"End of config applied for: [b cyan]{self.name}")
            return True

        console.print(response.result, highlight=True)
        console.log(
            f"[b]({self.project.name})({self.name})[/] Node could not be configured over console", style="error"
        )
        return False

    def get_config(self) -> Optional[Result]:
        """Retrieves the configuration file from the node.

        Raises:
            ValueError: If the nornir object is not properly initialized.

        Returns:
            bool: True if the configuration is retrieved, False otherwise.
        """
        if self.nornir is None:
            raise ValueError(f"Check nornir object is not initialised fot the node: {self.name}")

        if self.status != "started":
            self.start()
            time.sleep(30)

        result = self.nornir.run(task=backup_task, name="backup config")
        console.log(f"[b]({self.project.name})({self.name})[/] Node's config", style="good")
        console.rule(title=f"Start of configuration retrieved for: [b cyan]{self.name}")
        console.print(result[self.name][-1], highlight=True)
        console.rule(title=f"End of configuration retrieved for: [b cyan]{self.name}")
        try:
            result.raise_on_error()
            return result[self.name][-1]
        except Exception:  # pylint: disable=broad-except
            console.log(
                f"[b]({self.project.name})({self.name})[/] Could not retrieve node's configuration", style="error"
            )
            return None

    def get_config_over_console(self, user: Optional[str] = None, password: Optional[str] = None) -> Optional[str]:
        """Retrieves the configuration file from the node over the console.

        Args:
            user (Optional[str], optional): The user to login to the node. Defaults to None.
            password (Optional[str], optional): The password to login to the node. Defaults to None.

        Raises:
            typer.Exit: If the GNS3 server host could not be parsed

        Returns:
            Optional[str]: The configuration file if retrieved, None otherwise.
        """
        if self.status != "started":
            self.start()
            time.sleep(30)

        server_host = dissect_url(self._base._connector.base_url)[1]
        if not server_host:
            console.log(f"[b]({self.project.name})({self.name})[/] GNS3 server host could not be parsed", style="error")
            raise typer.Exit(1)

        response = node_console.run_action(
            action="command",
            server_host=server_host,
            data=SHOW_RUN_COMMANDS[self.net_os],  # type: ignore
            node=self,
            user=user,
            password=password,
        )

        console.log(f"[b]({self.project.name})({self.name})[/] Node's config", style="good")
        console.rule(title=f"Start of configuration retrieved for: [b cyan]{self.name}")
        console.print(response.result, highlight=True)
        console.rule(title=f"End of configuration retrieved for: [b cyan]{self.name}")

        if not response.failed:
            return response.result

        console.log(f"[b]({self.project.name})({self.name})[/] Could not retrieve node's configuration", style="error")
        return None

    def render_ports_detail(self) -> ConsoleRenderable:
        """Renders the ports detail.

        Returns:
            ConsoleRenderable: The rendered ports detail.
        """
        # The following helps highlight used ports
        list_ports = []
        flag = False
        for port in self._base.ports:
            for _, link in self._base.links.items():
                for gns3_port in link.nodes:
                    if gns3_port.name == port.name and gns3_port.node_name == self.name:
                        flag = True
            if flag:
                flag = False
                list_ports.append(f"[yellow i]{port.name}[/]")
            else:
                flag = False
                list_ports.append(port.name)
        ports = ", ".join(list_ports)
        return Panel(ports, expand=False, title="[b]Ports[/]", box=box.HEAVY_EDGE)

    def render_links_detail(self) -> ConsoleRenderable:
        """Renders the links detail.

        Returns:
            ConsoleRenderable: The rendered links detail.
        """
        paneles = []
        for index, link in enumerate(self._base.links.values()):
            paneles.append(
                Panel(
                    f"[yellow bold]{link.name}",
                    title=f"Link: {index}",
                )
            )
        return Panel(Group(*paneles), expand=False, title="[b]Links[/]", box=box.HEAVY_EDGE)

    def render_properties(self) -> ConsoleRenderable:
        """Renders the node's properties.

        Returns:
            ConsoleRenderable: The rendered properties.
        """
        return render_scope(self.properties if self.properties else {}, title="[b]Properties[/]")

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # pylint: disable=unused-argument
        # pylint: disable=redefined-outer-name
        """Renders all the node's properties.

        Args:
            console (Console): The Rich console instance.
            options (ConsoleOptions): The rendering options.

        Returns:
            RenderResult: The result of the rendering.

        Yields:
            Iterator[RenderResult]: The result of the rendering.
        """
        yield f"[b]Node:[/b] {self.name}"
        table = Table("Attributes", "Value", box=box.HEAVY_EDGE, highlight=True)
        table.add_row("[b]id[/b]", self.id)
        table.add_row("[b]template[/b]", self.template)
        table.add_row("[b]kind[/b]", self.kind)
        table.add_row("[b]project[/b]", self.project.name)
        table.add_row("[b]status[/b]", node_status(self.status))
        table.add_row("[b]console[/b]", str(self.console))
        table.add_row("[b]category[/b]", self.category)
        table.add_row("[b]net_os[/b]", node_net_os(self.net_os))
        table.add_row("[b]model[/b]", self.model)
        table.add_row("[b]version[/b]", self.version)
        table.add_row("[b]#Ports[/b]", str(len(self.interfaces)))
        table.add_row("[b]labels[/b]", str(self.labels))
        table.add_row("[b]mgmt_addr[/b]", self.mgmt_addr)
        table.add_row("[b]mgmt_port[/b]", self.mgmt_port)
        table.add_row("[b]config_managed[/b]", str(self.config_managed))
        yield table
