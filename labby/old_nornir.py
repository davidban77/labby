import logging
from nornir.core import Nornir
import typer
from pathlib import Path
from typing import Optional
from netaddr import IPNetwork
from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir.core.helpers.jinja_helper import render_from_file
from nornir_utils.plugins.tasks.files import write_file
from nornir_utils.plugins.functions import print_result
from nornir_scrapli.tasks import send_command
# from labby import settings, utils
from labby import models
from labby.models import LabbyProject, LabbyNode
from labby.providers import get_provider


# CONFIG_FILE = Path(__file__) / ".." / "example/labby.toml"
# example_cfg = settings.load_toml(CONFIG_FILE.resolve())


# nr = InitNornir(**example_cfg["labby"]["nornir"])


# Filter function based on the gns3_template attribute
def labby_node(host):
    return True if host.data.get("labby_builtin", False) is False else False


def group_labby(host):
    return host.has_parent_group("labby")


def ipaddress(value: str, action: str = "address") -> str:
    to_render = ""
    if action == "address":
        to_render = str(IPNetwork(addr=value).ip)
    elif action == "netmask":
        to_render = str(IPNetwork(addr=value).netmask)
    return to_render


# # Example of filtering hosts based on GNS3 attributes
# gns3_nornir_hosts = nr.filter(filter_func=gns3_host).inventory.hosts

# # Other way to get GNS3 hosts
# other_gns3_nornir_hosts = nr.filter(filter_func=group_gns3).inventory.hosts


# def hello_world(task: Task) -> Result:
#     if task.host.name == "r1":
#         return Result(
#             host=task.host,
#             result="Falta la broma!",
#             changed=True,
#             diff="algun diff",
#             failed=True,
#         )
#     return Result(host=task.host, result=f"{task.host.name} says hello world!")


# new_nr = nr.filter(filter_func=group_gns3)
# result = new_nr.run(task=hello_world)

# result.failed

# result.failed_hosts

# result["r1"].result


def generate_bootstrap_config(task: Task, template: Path):
    rendered_data = render_from_file(
        path=str(template.parent),
        template=template.name,
        jinja_filters={"ipaddress": ipaddress},
        **task.host.dict(),
    )
    task.run(
        task=write_file,
        content=rendered_data,
        filename=str(
            Path(
                template.parent / ".." / f"configs/build/{task.host.name}_bootstrap.txt"
            ).resolve()
        ),
    )


# def build(project_name: str):
#     if settings.SETTINGS.nornir is None:
#         utils.console.print("[red]Nornir settings not found[/]")
#         raise typer.Exit(code=1)
#     # Initialize Nornir
#     nr = InitNornir(**settings.SETTINGS.nornir.dict())

#     # Filter only gns3 hosts
#     nr = nr.filter(filter_func=group_gns3)

#     # Initialize provider
#     # provider = provider_setup(f"Building project: {project_name}")

#     # Create project object and on provider
#     project = Project(name=project_name)
#     # created = provider.create_project(project)
#     # if not created:
#     #     raise typer.Exit(code=1)

#     # Based on each Nornir host, create the provider object and save it
#     for name, host in nr.inventory.hosts.items():
#         # Create Labby Node from Nornir host
#         node = Node(name=name, project=project.name, template=host["gns3_template"])

#         # Create node on provider lab
#         # created = provider.create_node(node=node, project=project)
#         # if not created:
#         #     raise typer.Exit(code=1)

#         # Save object on Nornir host
#         host.data["node"] = node

#     # Generate bootstrap config? (maybe it can be passed as a jinja template)
#     nr_gn3_buildable = nr.filter(filter_func=gns3_host)
#     result = nr_gn3_buildable.run(
#         task=generate_bootstrap_config,
#         template=Path(
#             Path(__file__) / "../.." / "example/labby_test/templates/bootstrap.j2"
#         ).resolve(),
#     )
#     print_result(result)

#     return


def backup_task(task: Task):
    if task.host.platform == "cisco_iosxe" or task.host.platform == "cisco_nxos":
        command = "show run"
    else:
        command = "show run"
    task.run(task=send_command, command=command)


class LabbyNornir:
    def __init__(self) -> None:
        # Project settings
        self.project_config = settings.SETTINGS.get_project()

        # Initialize Nornir object and filter for provider objects
        nr = InitNornir(**self.project_config.nornir.dict())
        self.nr = nr.filter(filter_func=group_labby)

        # Initialize Labby project
        self.project = models.LabbyProject(name=self.project_config.name)

        # Initialize Labby nodes and store in Nornir objs
        for name, host in self.nr.inventory.hosts.items():
            host.data["labby_node"] = LabbyNode(
                name=name, project=self.project.name, template=host["gns3_template"]
            )

    def backup(self) -> bool:
        # Filter the nodes if needed
        _nr = self.nr.filter(filter_func=labby_node)
        result = _nr.run(task=backup_task, name="backup config")
        print_result(result)  # type: ignore
        try:
            result.raise_on_error()
            return True
        except Exception:
            return False

    def bootstrap(self, template: Path) -> bool:
        # Filter the nodes if needed
        _nr = self.nr.filter(filter_func=labby_node)
        result = _nr.run(
            task=generate_bootstrap_config,
            name="generate bootstrap config",
            template=template,
        )
        print_result(result)  # type: ignore
        try:
            result.raise_on_error()
            return True
        except Exception:
            return False
