import abc
from typing import Dict, Optional, List, Any
from nornir.core import Nornir
from pydantic import BaseModel
from pydantic.fields import Field
from rich.console import ConsoleRenderable


class LabbyNodeTemplate(BaseModel):
    name: str
    id: Optional[str]
    kind: Optional[str]
    image: Optional[str]
    net_os: Optional[str]
    model: Optional[str]
    version: Optional[str]

    class Config:
        extra = "allow"

    @abc.abstractmethod
    def get(self) -> None:
        pass

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def delete(self) -> bool:
        pass


class LabbyProjectInfo(BaseModel):
    name: str
    id: Optional[str]


class LabbyPort(BaseModel):
    name: str
    kind: str

    class Config:
        validate_assignment = True
        extra = "allow"


class LabbyNode(BaseModel, abc.ABC):
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
    nornir: Optional[Nornir]

    class Config:
        validate_assignment = True
        extra = "allow"
        arbitrary_types_allowed = True

    @abc.abstractmethod
    def get(self) -> None:
        pass

    @abc.abstractmethod
    def start(self) -> bool:
        pass

    @abc.abstractmethod
    def stop(self) -> bool:
        pass

    @abc.abstractmethod
    def restart(self) -> bool:
        pass

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def delete(self) -> bool:
        pass

    @abc.abstractmethod
    def bootstrap(self, config: str, boot_delay: int = 5) -> bool:
        pass

    @abc.abstractmethod
    def render_ports_detail(self) -> ConsoleRenderable:
        pass

    @abc.abstractmethod
    def render_links_detail(self) -> ConsoleRenderable:
        pass

    @abc.abstractmethod
    def render_properties(self) -> ConsoleRenderable:
        pass

    @abc.abstractmethod
    def apply_config(self, config: str, user: Optional[str] = None, password: Optional[str] = None) -> bool:
        pass

    @abc.abstractmethod
    def get_config(self) -> bool:
        pass

    @abc.abstractmethod
    def get_config_over_console(self, user: Optional[str] = None, password: Optional[str] = None) -> bool:
        pass


class LabbyLinkEndpoint(BaseModel):
    node_a: str
    port_a: str
    node_b: str
    port_b: str


class LabbyLink(BaseModel, abc.ABC):
    name: str
    id: Optional[str]
    kind: Optional[str]
    project: LabbyProjectInfo
    endpoint: Optional[LabbyLinkEndpoint]
    # status: Optional[str]
    filters: Optional[Dict[str, Any]]
    labels: List[str] = Field(default_factory=list)

    class Config:
        validate_assignment = True
        extra = "allow"

    @abc.abstractmethod
    def get(self) -> None:
        pass

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def delete(self) -> bool:
        pass

    @abc.abstractmethod
    def apply_metric(self, **kwargs) -> bool:
        pass


class LabbyProject(BaseModel, abc.ABC):
    name: str
    id: Optional[str]  # Inherited from provider
    status: Optional[str]
    nodes: Dict[str, LabbyNode] = Field(default_factory=dict)
    links: Dict[str, LabbyLink] = Field(default_factory=dict)
    labels: List[str] = Field(default_factory=list)
    nornir: Optional[Nornir]

    class Config:
        validate_assignment = True
        extra = "allow"
        arbitrary_types_allowed = True

    @abc.abstractmethod
    def get(self) -> None:
        pass

    @abc.abstractmethod
    def start(self, start_nodes: Optional[str], nodes_delay: int = 5) -> bool:
        pass

    @abc.abstractmethod
    def stop(self, stop_nodes: bool = True) -> bool:
        pass

    @abc.abstractmethod
    def update(self, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def delete(self) -> bool:
        pass

    @abc.abstractmethod
    def start_nodes(self, start_nodes: str, nodes_delay: int = 5) -> None:
        pass

    @abc.abstractmethod
    def stop_nodes(self) -> None:
        pass

    @abc.abstractmethod
    def search_node(self, name: str) -> Optional[LabbyNode]:
        pass

    @abc.abstractmethod
    def create_node(self, name: str, template: str, labels: List[str] = [], **kwargs) -> LabbyNode:
        pass

    # @abc.abstractmethod
    # def delete_node(self) -> None:
    #     pass

    @abc.abstractmethod
    def search_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> Optional[LabbyLink]:
        pass

    @abc.abstractmethod
    def create_link(
        self,
        node_a: str,
        port_a: str,
        node_b: str,
        port_b: str,
        filters: Optional[Dict[str, Any]] = None,
        labels: List[str] = [],
        **kwargs
    ) -> LabbyLink:
        pass

    # @abc.abstractmethod
    # def delete_link(self, node_a: str, port_a: str, node_b: str, port_b: str) -> None:
    #     pass

    @abc.abstractmethod
    def render_nodes_summary(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        pass

    @abc.abstractmethod
    def render_links_summary(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        pass

    @abc.abstractmethod
    def to_initial_state(self) -> None:
        pass

    @abc.abstractmethod
    def get_web_url(self) -> str:
        pass


class LabbyProvider(BaseModel, abc.ABC):
    name: str
    kind: str

    class Config:
        validate_assignment = True
        extra = "allow"

    # @abc.abstractmethod
    # def get_projects(self) -> List[LabbyProject]:
    #     pass

    @abc.abstractmethod
    def search_project(self, project_name: str) -> Optional[LabbyProject]:
        pass

    @abc.abstractmethod
    def create_project(self, project_name: str, labels: List[str] = [], **kwargs) -> LabbyProject:
        pass

    # @abc.abstractmethod
    # def delete_project(self, project_name: str) -> None:
    #     pass

    @abc.abstractmethod
    def search_template(self, template_name: str) -> Optional[LabbyNodeTemplate]:
        pass

    @abc.abstractmethod
    def create_template(self, template_name: str, **kwargs) -> LabbyNodeTemplate:
        pass

    # @abc.abstractmethod
    # def start_project(self, project: str) -> LabbyProject:
    #     pass

    # @abc.abstractmethod
    # def stop_project(self, project: str) -> LabbyProject:
    #     pass

    @abc.abstractmethod
    def render_templates_list(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        pass

    @abc.abstractmethod
    def render_project_list(self, field: Optional[str] = None, value: Optional[str] = None) -> ConsoleRenderable:
        pass
