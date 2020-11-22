import abc
import labby.models as models


class ProvidersBase(abc.ABC):
    @abc.abstractmethod
    def get_project_details(self, project: models.Project):
        ...

    @abc.abstractmethod
    def create_project(self, project: models.Project):
        ...

    @abc.abstractmethod
    def delete_project(self, project: models.Project):
        ...

    @abc.abstractmethod
    def start_project(self, project: models.Project):
        ...

    @abc.abstractmethod
    def stop_project(self, project: models.Project):
        ...

    @abc.abstractmethod
    def create_node(self, node: models.Node, project: models.Project):
        ...

    @abc.abstractmethod
    def delete_node(self, node: models.Node, project: models.Project):
        ...

    @abc.abstractmethod
    def start_node(self, node: models.Node, project: models.Project):
        ...

    @abc.abstractmethod
    def stop_node(self, node: models.Node, project: models.Project):
        ...

    @abc.abstractmethod
    def reload_node(self, node: models.Node, project: models.Project):
        ...

    @abc.abstractmethod
    def suspend_node(self, node: models.Node, project: models.Project):
        ...

    @abc.abstractmethod
    def create_connection(self, connection: models.Connection, project: models.Project):
        ...

    @abc.abstractmethod
    def delete_connection(self, connection: models.Connection, project: models.Project):
        ...


# if __name__ == "__main__":
#     class GNS3Provider(ProvidersBase):
#         def create_project(self, project: models.Project):
#             pass

#         def delete_project(self, project: models.Project):
#             pass

#         def start_project(self, project: models.Project, start_nodes: str = "none"):
#             pass

#         def stop_project(self, project: models.Project):
#             pass

#     aver = GNS3Provider()
#     print(aver)
