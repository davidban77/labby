from pathlib import Path
from nornir import InitNornir
from nornir.core.task import Task, Result
import typer
from labby import settings
from labby.utils import console
from labby.models import Project, Node
from labby.providers import provider_setup


CONFIG_FILE = Path(__file__) / ".." / "example/labby.toml"
example_cfg = settings.load_toml(CONFIG_FILE.resolve())


nr = InitNornir(**example_cfg["labby"]["nornir"])


# Filter function based on the gns3_template attribute
def gns3_host(host):
    return True if host.data.get("gns3_template") else False


def group_gns3(host):
    return host.has_parent_group("gns3")


# Example of filtering hosts based on GNS3 attributes
gns3_nornir_hosts = nr.filter(filter_func=gns3_host).inventory.hosts

# Other way to get GNS3 hosts
other_gns3_nornir_hosts = nr.filter(filter_func=group_gns3).inventory.hosts


def hello_world(task: Task) -> Result:
    if task.host.name == "r1":
        return Result(
            host=task.host,
            result="Falta la broma!",
            changed=True,
            diff="algun diff",
            failed=True,
        )
    return Result(host=task.host, result=f"{task.host.name} says hello world!")


new_nr = nr.filter(filter_func=group_gns3)
result = new_nr.run(task=hello_world)

result.failed

result.failed_hosts

result["r1"].result


def build(project_name: str):
    # Initialize Nornir
    nr = InitNornir(**settings.SETTINGS.nornir.dict())

    # Filter only gns3 hosts
    nr = nr.filter(filter_func=group_gns3)

    # Initialize provider
    provider = provider_setup(f"Building project: {project_name}")

    # Create project object and on provider
    project = Project(name=project_name)
    created = provider.create_project(project)
    if not created:
        raise typer.Exit(code=1)

    # Based on each Nornir host, create the provider object and save it
    for name, host in nr.inventory.hosts.items():
        # Create Labby Node from Nornir host
        node = Node(name=name, project=project.name, template=host["gns3_template"])

        # Create node on provider lab
        created = provider.create_node(node=node, project=project)
        if not created:
            raise typer.Exit(code=1)

        # Save object on Nornir host
        host.date["node"] = node

        # Generate bootstrap config? (maybe it can be passed as a jinja template)
        # checkout https://github.com/writememe/day-one-net-toolkit/blob/master/day-one-toolkit.py

    return
