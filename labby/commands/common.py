import typer
from typing import Tuple
from pathlib import Path
from netaddr import IPNetwork
from nornir.core.task import Task
from nornir_scrapli.tasks import send_config, send_command
from nornir.core.helpers.jinja_helper import render_from_file
from labby.models import LabbyProject
from labby import config, utils


SHOW_RUN_COMMANDS = {
    "arista_eos": "show run",
    "cisco_ios": "show run",
    "cisco_iosxe": "show run",
    "cisco_nxos": "show run",
}


SAVE_COMMANDS = {
    "arista_eos": "wr mem",
    "cisco_ios": "wr mem",
    "cisco_iosxe": "wr mem",
    "cisco_nxos": "copy running-config startup-config",
}


class ProjectData:
    def __init__(self, project_file: Path) -> None:
        if project_file.is_file():
            self.project_file = project_file
            self.project_data = self.get_project_data()
            for required in config.REQUIRED_PROJECT_FIELDS:
                if required not in self.project_data:
                    raise ValueError(f"Missing required fields in project file: {required}")
            self.name = self.project_data["main"]["name"]
            self.mgmt_network = self.project_data["main"]["mgmt_network"]
            self.mgmt_creds = self.project_data["main"]["mgmt_creds"]
            self.version = self.project_data["main"].get("version", "1.0")
            self.description = self.project_data["main"].get("description", "")
            self.contributors = self.project_data["main"].get("contributors", [])
            self.template = self.project_data["main"].get("template", "")
            self.labels = self.project_data["main"].get("labels", [])

            # Check creds
            self.check_creds()

            # Project nodes and links
            self.nodes_spec = self.project_data.get("nodes_spec", [])
            self.links_spec = self.project_data.get("links_spec", [])

            # Vars
            self.vars = self.project_data.get("vars", {})

            # Extra properties
            self.extra_properties = self.project_data.get("extra_properties", {})

        else:
            raise FileNotFoundError(f"Project file not found: {project_file}")

    def get_project_data(self) -> dict:
        """Get the project data from the project file."""
        return utils.load_yaml_file(str(self.project_file))

    def check_creds(self) -> None:
        """Check if the credentials are valid."""
        if not utils.check_creds(self.mgmt_network, self.mgmt_creds):
            raise ValueError("Invalid credentials for the management network")


def backup_task(task: Task):
    task.run(task=send_command, command=SHOW_RUN_COMMANDS[task.host.platform])  # type: ignore


def save_task(task: Task):
    task.run(task=send_command, command=SAVE_COMMANDS[task.host.platform])  # type: ignore


def config_task(task: Task, project_data: ProjectData, project: LabbyProject):
    cfg_data = render_from_file(
        path=str(Path(project_data.template).parent),
        template=Path(project_data.template).name,
        jinja_filters={"ipaddr": utils.ipaddr_renderer},
        **dict(project=project, node=task.host.data["labby_obj"], **project_data.vars),
    )
    task.run(task=send_config, config=cfg_data)


def get_project_from_file(project_file: Path) -> Tuple[LabbyProject, ProjectData]:
    """Get the project from the project file."""
    project_data = ProjectData(project_file)
    utils.console.log(f"[b]({project_data.name})[/] Retrieving project specification")
    provider = config.get_provider()
    project = provider.search_project(project_name=project_data.name)
    if project:
        utils.console.log(f"[b]({project.name})[/] Project already exists")
    else:
        project_args = dict(project_name=project_data.name, labels=project_data.labels, **project_data.extra_properties)
        project = provider.create_project(**project_args)
        utils.console.log(f"[b]({project.name})[/] Project created")
    return project, project_data


def sync_project_data(project_file: Path) -> Tuple[LabbyProject, ProjectData]:
    project, project_data = get_project_from_file(project_file)

    mgmt_network = IPNetwork(project_data.mgmt_network)
    # Verify nodes created to be managed match the ones in the project
    index = 0
    for node_spec in project_data.nodes_spec:
        for node_name in node_spec.get("nodes", []):
            # TODO: Add logs for DEBUG example, like this one:
            # utils.console.log(f"[b]({project.name})[/] Checking parameters on node: [i dark_orange3]{node_name}")
            node = project.search_node(name=node_name)

            # Validate devices exists in the project
            if not node:
                utils.console.log(f"[b]({project.name})[/] Node not found: [i red]{node_name}")
                raise typer.Exit(1)

            # Update properties
            for label in node_spec.get("labels", []):
                if label not in node.labels:
                    node.labels.append(label)

            node.config_managed = node_spec.get("config_managed", node.config_managed)

            # TODO: Add support to detect changes in node.mgmt_addr assignments
            node.mgmt_port = node_spec.get("mgmt_port", node.mgmt_port)
            node.mgmt_addr = (
                f"{list(mgmt_network.iter_hosts())[index]}/{mgmt_network.prefixlen}"
                if node.mgmt_addr is None
                else node.mgmt_addr
            )
            index += 1

    # Refresh Nornir Inventory
    project.init_nornir()

    return project, project_data
