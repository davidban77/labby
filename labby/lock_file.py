# LOCK_FILE = {
#     "environment1": {
#         "provider1": {
#             "projects": {
#                 "project1": {
#                     "labels": ["project1_label"],
#                     "nodes": {
#                         "router1": {
#                             "labels": ["router1_label"],
#                             "mgmt_port": "Management1",
#                             "mgmt_ip": "192.168.1.1/30",
#                         },
#                     },
#                     "links": {
#                         "link1": {
#                             "labels": ["link1_label"],
#                         },
#                     },
#                 }
#             }
#         }
#     }
# }
import toml
from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional

import typer
from labby.models import LabbyLink, LabbyNode, LabbyProject
from labby import config, utils


DEFAULT_LOCK_FILE = Path().cwd() / ".labby.lock"


def gen_node_data(node: LabbyNode) -> Dict[str, Any]:
    return {node.name: {"labels": node.labels, "mgmt_port": node.mgmt_port, "mgmt_addr": node.mgmt_addr}}


def gen_link_data(link: LabbyLink) -> Dict[str, Any]:
    return {link.name: {"labels": link.labels}}


def gen_project_data(project: LabbyProject):
    nodes_lock_data = {}
    for _, node in project.nodes.items():
        nodes_lock_data.update(gen_node_data(node))
    links_lock_data = {}
    for _, link in project.links.items():
        links_lock_data.update(gen_link_data(link))
    return {project.name: {"labels": project.labels, "nodes": nodes_lock_data, "links": links_lock_data}}


def gen_lock_file_data(project: LabbyProject):
    # Initialize lock file data
    lock_file_data = {
        config.SETTINGS.environment.name: {
            config.SETTINGS.environment.provider.name: {"projects": gen_project_data(project)}
        }
    }

    return lock_file_data


def read_data(file_path: Path) -> Optional[MutableMapping[str, Any]]:
    if file_path.exists():
        return toml.loads(file_path.read_text())
    else:
        return None


def save_data(lock_file_data: MutableMapping[str, Any], lock_file: Path = DEFAULT_LOCK_FILE):
    lock_file.write_text(toml.dumps(lock_file_data))


def apply_node_data(node: LabbyNode, project: Optional[LabbyProject] = None, lock_file: Path = DEFAULT_LOCK_FILE):
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        if not project:
            utils.console.log("Cannot save node in lock file", style="error")
            raise typer.Exit(1)
        lock_file_data = gen_lock_file_data(project)
    else:
        project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
            config.SETTINGS.environment.provider.name
        ]["projects"].get(node.project.name)

        if project_lock_file_data is None:
            if not project:
                utils.console.log("Cannot save node in lock file", style="error")
                raise typer.Exit(1)
            lock_file_data = gen_lock_file_data(project)

        else:
            project_lock_file_data["nodes"].update(gen_node_data(node))
    save_data(lock_file_data, lock_file)


def apply_link_data(link: LabbyLink, project: Optional[LabbyProject] = None, lock_file: Path = DEFAULT_LOCK_FILE):
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        if not project:
            utils.console.log("Cannot save node in lock file", style="error")
            raise typer.Exit(1)
        lock_file_data = gen_lock_file_data(project)
    else:
        project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
            config.SETTINGS.environment.provider.name
        ]["projects"].get(link.project.name)

        if project_lock_file_data is None:
            if not project:
                utils.console.log("Cannot save node in lock file", style="error")
                raise typer.Exit(1)
            lock_file_data = gen_lock_file_data(project)

        else:
            project_lock_file_data["links"].update(gen_link_data(link))
    save_data(lock_file_data, lock_file)


def apply_project_data(project: LabbyProject, lock_file: Path = DEFAULT_LOCK_FILE):
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        lock_file_data = gen_lock_file_data(project)
    else:
        project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
            config.SETTINGS.environment.provider.name
        ]["projects"].get(project.name)

        if project_lock_file_data is None:
            lock_file_data = gen_lock_file_data(project)
        else:
            project_lock_file_data.update(labels=project.labels)

    save_data(lock_file_data, lock_file)


def get_project_data(project_name: str, lock_file: Path = DEFAULT_LOCK_FILE) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        return None
    return lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name]["projects"].get(
        project_name
    )


def get_node_data(node_name: str, project_name: str, lock_file: Path = DEFAULT_LOCK_FILE) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["nodes"].get(node_name)


def get_link_data(link_name: str, project_name: str, lock_file: Path = DEFAULT_LOCK_FILE) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["links"].get(link_name)


def delete_project_data(project_name: str, lock_file: Path = DEFAULT_LOCK_FILE) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        return None
    return lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name]["projects"].pop(
        project_name, None
    )


def delete_node_data(
    node_name: str, project_name: str, lock_file: Path = DEFAULT_LOCK_FILE
) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["nodes"].pop(node_name, None)


def delete_link_data(
    link_name: str, project_name: str, lock_file: Path = DEFAULT_LOCK_FILE
) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["links"].pop(link_name, None)
