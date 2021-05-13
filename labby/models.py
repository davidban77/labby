import abc
from typing import Dict, Optional, List, Any
from pydantic import BaseModel
from pydantic.fields import Field
from rich.console import ConsoleRenderable


# @dataclass
# class LabbyPort:
#     name: str
#     type: str


# @dataclass
# class LabbyNode:
#     name: str
#     project: str
#     project_id: Optional[str] = None
#     id: Optional[str] = None
#     template: Optional[str] = None
#     type: Optional[str] = None
#     exists: Optional[bool] = None
#     console: Optional[int] = None
#     status: Optional[str] = None
#     category: Optional[str] = None
#     net_os: Optional[str] = None
#     model: Optional[str] = None
#     interfaces: Optional[List[LabbyPort]] = None
#     x: int = 0
#     y: int = 0
#     properties: Optional[Dict[str, str]] = None
#     _provider: Optional[Any] = None       # Inner object with provider specific settings


# @dataclass
# class LabbyEndpoint:
#     node: LabbyNode
#     port: LabbyPort


# @dataclass
# class LabbyLink:
#     name: str
#     project: str
#     endpoints: List[LabbyEndpoint]
#     project_id: Optional[str] = None
#     id: Optional[str] = None
#     exists: Optional[bool] = None
#     type: Optional[str] = None
#     _provider: Optional[Any] = None       # Inner object with provider specific settings


# @dataclass
# class LabbyProject:
#     name: str
#     id: Optional[str] = None  # Inherited from provider
#     status: Optional[str] = None
#     exists: Optional[bool] = None    # Flags that specifies if project existis
#     nodes: Optional[List[LabbyNode]] = None   # List of nodes in project
#     connections: Optional[List[LabbyLink]] = None
#     _provider: Optional[Any] = None      # Inner object with provider specific settings
#     # mgmt: Object  -> Possibly.. like a nested attr with mgmt nodes info


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

    class Config:
        validate_assignment = True
        extra = "allow"

    @abc.abstractmethod
    def get(self) -> None:
        pass

    @abc.abstractmethod
    def start(self) -> None:
        pass

    @abc.abstractmethod
    def stop(self) -> None:
        pass

    @abc.abstractmethod
    def restart(self) -> None:
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
    def delete(self) -> None:
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

    class Config:
        validate_assignment = True
        extra = "allow"

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
    def delete(self) -> None:
        pass

    @abc.abstractmethod
    def start_nodes(self) -> None:
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

    @abc.abstractmethod
    def get_projects(self) -> List[LabbyProject]:
        pass

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


# class BaseProvider(BaseModel):
#     name: str
#     type: str
#     server_url: Optional[AnyHttpUrl]
#     user: Optional[str] = None
#     password: Optional[str] = None
#     verify_cert: bool = False


# class ProviderDocker(BaseProvider):
#     server_url: Optional[AnyUrl]


# class ProviderGeneral(BaseProvider):
#     pass


# class EnvironmentSettings(BaseModel):
#     name: str
#     description: Optional[str]
#     # provider: Optional[str]
#     # gns3: Optional[ProviderGns3]
#     # vrnetlab: Optional[ProviderVrnetlab]
#     # eve_ng: Optional[ProviderEveng]
#     # providers: Union[List[ProviderVrnetlab], List[ProviderGns3], List[ProviderEveng]]
#     providers: List[Union[ProviderGeneral, ProviderDocker]]
#     metadata: Dict[str, Any] = Field(default_factory=dict)

#     def get_provider(self, name: str) -> Union[ProviderGeneral, ProviderDocker]:
#         # return getattr(self, name)
#         try:
#             return next(_p for _p in self.providers if _p.name == name)
#         except StopIteration:
#             raise ValueError(f"Provider not found: {name}")

#     class Config:
#         extra = "ignore"
#         validate_assignment = True


# class NornirInventoryOptions(BaseModel):
#     host_file: FilePath
#     group_file: FilePath


# class NornirInventory(BaseModel):
#     plugin: str = "SimpleInventory"
#     options: NornirInventoryOptions


# class NornirRunner(BaseModel):
#     plugin: str = "threaded"
#     options: Dict[str, Any] = {"num_workers": 5}


# class NornirSettings(BaseModel):
#     runner: NornirRunner
#     inventory: NornirInventory


# class NodeSpec(BaseModel):
#     template: str
#     nodes: List[str]
#     device_type: str
#     mgmt_interface: Optional[str]
#     config_managed: bool = True


# class LinkSpec(BaseModel):
#     node_a: str
#     port_a: str
#     node_b: str
#     port_b: str
#     link_filter: Optional[Dict[str, Any]] = None


# class ProjectSettings(BaseModel):
#     name: str
#     description: Optional[str]
#     contributors: Optional[List[str]]
#     version: Optional[str]
#     nodes_spec: List[NodeSpec]
#     links_spec: List[LinkSpec]

#     class Config:
#         extra = "ignore"
#         validate_assignment = True


# class LabbyGlobalSettings(BaseSettings):
#     provider: str
#     provider_type: Literal["gns3", "vrnetlab", "eve_ng"]
#     environment: str
#     project: Optional[str] = None
#     debug: bool = False

#     class Config:
#         env_prefix = "LABBY_"
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#         extra = "ignore"
#         validate_assignment = True


# class LabbySettings(BaseModel):
#     labby: LabbyGlobalSettings
#     envs: Dict[str, EnvironmentSettings]
#     prjs: Dict[str, ProjectSettings]

#     def get_environment(self) -> EnvironmentSettings:
#         try:
#             return self.envs[self.labby.environment]
#         except KeyError:
#             raise ValueError(f"No environment {self.labby.environment} found")

#     def get_project(self) -> ProjectSettings:
#         try:
#             if self.labby.project is None:
#                 raise KeyError
#             return self.prjs[self.labby.project]
#         except KeyError:
#             raise ValueError(f"No project {self.labby.project} found")

#     def get_provider_settings(
#         self,
#     ) -> Union[ProviderGeneral, ProviderDocker]:
#         return self.get_environment().get_provider(self.labby.provider)
