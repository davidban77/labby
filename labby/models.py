"""The models module for Labby."""
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value
# pylint: disable=too-few-public-methods
# pylint: disable=no-name-in-module
import abc
from typing import Dict, Optional, List, Any

from nornir.core import Nornir
from pydantic import BaseModel
from pydantic.fields import Field
from rich.console import ConsoleRenderable


class LabbyNodeTemplate(BaseModel):
    """
    Labby Node template.

    Attributes:
        name (str): Name of the node.
        id (Optional[str]): ID for the node.
        kind (Optional[str]): A kind of template.
        image (Optional[str]): Image for the template.
        net_os (Optional[str]): The net os for the node.
        model (Optional[str]): The model for the node.
        version (Optional[str]): The version of the node/net_os?
    """

    name: str
    id: Optional[str]
    kind: Optional[str]
    image: Optional[str]
    net_os: Optional[str]
    model: Optional[str]
    version: Optional[str]

    class Config:
        """Configuration class for LabbyNodeTemplate."""

        extra = "allow"

    @abc.abstractmethod
    def get(self) -> None:
        """Abstract method for LabbyNodeTemplate."""

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        """Abstract method for LabbyNodeTemplate."""

    @abc.abstractmethod
    def delete(self) -> bool:
        """Abstract method for LabbyNodeTemplate."""


class LabbyProjectInfo(BaseModel):
    """Project information class, has a name and id attribute."""

    name: str
    id: Optional[str]


class LabbyPort(BaseModel):
    """Labby Port class, has a name and a kind attribute."""

    name: str
    kind: str

    class Config:
        """Configuration class for LabbyPort."""

        validate_assignment = True
        extra = "allow"


class LabbyNode(BaseModel, abc.ABC):
    """
    A Labby Node.

    Attributes:
        name (Optional[str]): Name of the node.
        id (Optional[str]): Identification for the node.
        template (Optional[str]): Template for the node.
        kind (Optional[str]): Type of the node.
        project (LabbyProjectInfo): Project the node belongs to.
        status (Optional[str]): Status of the node.
        console (Optiona[int]): The console port.
        category (Optional[str]): Category of the node.
        net_os (Optional[str]): The net_os for the node.
        model (Optional[str]): The model of the node.
        version (Optional[str]): The version of the node.
        interfaces (Dict[str, LabbyPort]): Interface for the Node.
        mgmt_port (Optional[str]): The management port for the node.
        mgmt_addr (Optional[str]): The management address for the node.
        properties (Optional[Dict[str, Any]]): The different properties for the node.
        labels (List[str]): The different labels for the node.
        config_managed (bool): Configuration managed.
        nornir (Optional[Nornir]): Nornir object.
    """

    name: str
    id: Optional[str]
    template: Optional[str]
    kind: Optional[str]
    project: LabbyProjectInfo
    status: Optional[str]
    console: Optional[int]
    category: Optional[str]
    net_os: Optional[str]
    model: Optional[str]
    version: Optional[str]
    interfaces: Dict[str, LabbyPort] = Field(default_factory=dict)
    mgmt_port: Optional[str]
    mgmt_addr: Optional[str]
    properties: Optional[Dict[str, Any]]
    labels: List[str] = Field(default_factory=list)
    config_managed: bool = True
    nornir: Optional[Nornir]

    class Config:
        """Configuration class for LabbyNode."""

        validate_assignment = True
        extra = "allow"
        arbitrary_types_allowed = True

    @abc.abstractmethod
    def get(self) -> None:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def start(self) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def stop(self) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def restart(self) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def delete(self) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def bootstrap(self, config: str, boot_delay: int = 5, delay_multiplier: int = 1) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def render_ports_detail(self) -> ConsoleRenderable:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def render_links_detail(self) -> ConsoleRenderable:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def render_properties(self) -> ConsoleRenderable:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def apply_config(self, config: str, user: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def apply_config_over_console(
        self, config: str, user: Optional[str] = None, password: Optional[str] = None, delay_multiplier: int = 1
    ) -> bool:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def get_config(self) -> Optional[str]:
        """Abstract method for LabbyNode."""

    @abc.abstractmethod
    def get_config_over_console(self, user: Optional[str] = None, password: Optional[str] = None) -> Optional[str]:
        """Abstract method for LabbyNode."""


class LabbyLinkEndpoint(BaseModel):
    """
    LabbyLinkEndpoint abstract class.

    Attributes:
        node_a (str): Name of node_a.
        port_a (str): Name of port_a.
        node_b (str): Name of node_b.
        port_b (str): Name of port_b.
    """

    node_a: str
    port_a: str
    node_b: str
    port_b: str


class LabbyLink(BaseModel, abc.ABC):
    """
    Labby Link abstract class.

    Attributes:
        name (str): Name of the link.
        id (Optional[str]): Identification for the link.
        kind (Optional[str]): A kind of link.
        project (LabbyProjectInfo): Project which the link belongs to.
        endpoint (Optional[LabbyLinkEndpoint]): Endpoint of the link.
        filters (Optional[Dict[str, Any]]): All the different filters for the link.
        labels (List[str]): All the different labels for the link.
    """

    name: str
    id: Optional[str]
    kind: Optional[str]
    project: LabbyProjectInfo
    endpoint: Optional[LabbyLinkEndpoint]
    # status: Optional[str]
    filters: Optional[Dict[str, Any]]
    labels: List[str] = Field(default_factory=list)

    class Config:
        """Configuartion class for LabbyLink."""

        validate_assignment = True
        extra = "allow"

    @abc.abstractmethod
    def get(self) -> None:
        """Abstract method for LabbyLink."""

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        """Abstract method for LabbyLink."""

    @abc.abstractmethod
    def delete(self) -> bool:
        """Abstract method for LabbyLink."""

    @abc.abstractmethod
    def apply_metric(self, **kwargs) -> bool:
        """Abstract method for LabbyLink."""


class LabbyProject(BaseModel, abc.ABC):
    """
    A Labby Project class.

    Attributes:
        name (str): The name of the project.
        id (Optional[str]): The identification for the project. #Inherited from provider.
        status (Optional[str]): The status of the project.
        nodes (Dict[str, LabbyNode]): A dictionary of all the nodes in the project.
        links (Dict[str, LabbyLink]): A dictionary of all the links in the project.
        labels (List[str]): All the different labels of the project.
        nornir (Optional[Nornir]): Nornir Object.
    """

    name: str
    id: Optional[str]  # Inherited from provider
    status: Optional[str]
    nodes: Dict[str, LabbyNode] = Field(default_factory=dict)
    links: Dict[str, LabbyLink] = Field(default_factory=dict)
    labels: List[str] = Field(default_factory=list)
    nornir: Optional[Nornir]

    class Config:
        """Configuration class for LabbyProject."""

        validate_assignment = True
        extra = "allow"
        arbitrary_types_allowed = True

    @abc.abstractmethod
    def init_nornir(self) -> None:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def get(self) -> None:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def start(self, start_nodes: Optional[str], nodes_delay: int = 5) -> bool:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def stop(self, stop_nodes: bool = True) -> bool:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def delete(self) -> bool:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def start_nodes(self, start_nodes: str, nodes_delay: int = 5) -> None:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def stop_nodes(self) -> None:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def search_node(self, name: str) -> Optional[LabbyNode]:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def create_node(self, name: str, template: str, labels: List[str] = [], **kwargs) -> LabbyNode:
        """Abstract method for LabbyProject."""

    # @abc.abstractmethod
    # def delete_node(self) -> None:

    @abc.abstractmethod
    def search_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> Optional[LabbyLink]:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def create_link(
        self,
        node_a: str,
        port_a: str,
        node_b: str,
        port_b: str,
        filters: Optional[Dict[str, Any]] = None,
        labels: List[str] = [],
        **kwargs,
    ) -> LabbyLink:
        """Abstract method for LabbyProject."""

    # @abc.abstractmethod
    # def delete_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> None:

    @abc.abstractmethod
    def render_nodes_summary(
        self, field: Optional[str] = None, value: Optional[str] = None, labels: Optional[List[str]] = []
    ) -> ConsoleRenderable:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def render_links_summary(
        self, field: Optional[str] = None, value: Optional[str] = None, labels: Optional[List[str]] = []
    ) -> ConsoleRenderable:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def to_initial_state(self) -> None:
        """Abstract method for LabbyProject."""

    @abc.abstractmethod
    def get_web_url(self) -> str:
        """Abstract method for LabbyProject."""


class LabbyProvider(BaseModel, abc.ABC):
    """
    A Labby Provider class.

    Attribute:
        name (str): The name of the provider.
        kind (str): The kind of provider.
    """

    name: str
    kind: str

    class Config:
        """Configuration class for LabbyProvider."""

        validate_assignment = True
        extra = "allow"

    # @abc.abstractmethod
    # def get_projects(self) -> List[LabbyProject]:

    @abc.abstractmethod
    def search_project(self, project_name: str) -> Optional[LabbyProject]:
        """Abstract method for LabbyProvider."""

    @abc.abstractmethod
    def create_project(self, project_name: str, labels: List[str] = [], **kwargs) -> LabbyProject:
        """Abstract method for LabbyProvider."""

    # @abc.abstractmethod
    # def delete_project(self, project_name: str) -> None:

    @abc.abstractmethod
    def search_template(self, template_name: str) -> Optional[LabbyNodeTemplate]:
        """Abstract method for LabbyProvider."""

    @abc.abstractmethod
    def create_template(self, template_name: str, **kwargs) -> LabbyNodeTemplate:
        """Abstract method for LabbyProvider."""

    # @abc.abstractmethod
    # def start_project(self, project: str) -> LabbyProject:

    # @abc.abstractmethod
    # def stop_project(self, project: str) -> LabbyProject:

    @abc.abstractmethod
    def render_templates_list(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        """Abstract method for LabbyProvider."""

    @abc.abstractmethod
    def render_project_list(
        self, field: Optional[str] = None, value: Optional[str] = None, labels: Optional[List[str]] = []
    ) -> ConsoleRenderable:
        """Abstract method for LabbyProvider."""
