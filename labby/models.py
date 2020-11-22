from dataclasses import dataclass
from typing import Dict, Optional, List, Any


@dataclass
class Connection:
    name: str
    project: str
    project_id: Optional[str] = None
    id: Optional[str] = None
    is_created: Optional[bool] = None
    type: Optional[str] = None
    endpoints: Optional[List[Dict[str, Any]]] = None
    _provider: Optional[Any] = None       # Inner object with provider specific settings


@dataclass
class Node:
    name: str
    project: str
    project_id: Optional[str] = None
    id: Optional[str] = None
    template: Optional[str] = None
    type: Optional[str] = None
    is_created: Optional[bool] = None
    console: Optional[int] = None
    status: Optional[str] = None
    category: Optional[str] = None
    net_os: Optional[str] = None
    model: Optional[str] = None
    interfaces: Optional[List[str]] = None
    properties: Optional[Dict[str, str]] = None
    _provider: Optional[Any] = None       # Inner object with provider specific settings


@dataclass
class Project:
    name: str
    id: Optional[str] = None  # Inherited from provider
    status: Optional[str] = None
    is_created: Optional[bool] = None    # Flags that specifies if project existis
    nodes: Optional[List[Node]] = None   # List of nodes in project
    connections: Optional[List[Connection]] = None
    _provider: Optional[Any] = None      # Inner object with provider specific settings
    # mgmt: Object  -> Possibly.. like a nested attr with mgmt nodes info


if __name__ == "__main__":
    @dataclass
    class Gns3Project(Project):
        another: Optional[bool] = None

        def create(self, arg1: str = "ok") -> bool:
            print(f"Created project {self.name}")
            return True

        def delete(self) -> bool:
            raise NotImplementedError("delete ... yet")

        def start(self, algo1):
            raise NotImplementedError("start ... yet")

        def stop(self) -> bool:
            raise NotImplementedError("stop ... yet")

        def open(self) -> bool:
            print(f"Opening project {self.name}...")
            return True

    aver = Gns3Project(name="testing")
    print(aver)
    print(aver.create())
    aver.open()
