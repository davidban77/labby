import json
from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional

import typer
from labby.models import LabbyLink, LabbyNode, LabbyProject
from labby import config, utils


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


def gen_lock_file_data(project: Optional[LabbyProject] = None):
    # Initialize lock file data
    lock_file_data = {
        config.SETTINGS.environment.name: {
            config.SETTINGS.environment.provider.name: {"projects": gen_project_data(project) if project else {}}
        }
    }

    return lock_file_data


def read_data(file_path: Path) -> Optional[MutableMapping[str, Any]]:
    if file_path.exists():
        # return toml.loads(file_path.read_text())
        return json.loads(file_path.read_text())
    else:
        return None


def save_data(lock_file_data: MutableMapping[str, Any]):
    # lock_file.write_text(toml.dumps(lock_file_data))
    config.SETTINGS.lock_file.write_text(json.dumps(lock_file_data, indent=4))


def apply_node_data(node: LabbyNode, project: Optional[LabbyProject] = None):
    lock_file_data = read_data(config.SETTINGS.lock_file)
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
            lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name][
                "projects"
            ].update(gen_project_data(project))
            project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
                config.SETTINGS.environment.provider.name
            ]["projects"][node.project.name]
        project_lock_file_data["nodes"].update(gen_node_data(node))

    save_data(lock_file_data)


def apply_link_data(link: LabbyLink, project: Optional[LabbyProject] = None):
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        if not project:
            utils.console.log("Cannot save link in lock file", style="error")
            raise typer.Exit(1)
        lock_file_data = gen_lock_file_data(project)

    else:
        project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
            config.SETTINGS.environment.provider.name
        ]["projects"].get(link.project.name)

        if project_lock_file_data is None:
            if not project:
                utils.console.log("Cannot save link in lock file, missing project data", style="error")
                raise typer.Exit(1)
            lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name][
                "projects"
            ].update(gen_project_data(project))
            project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
                config.SETTINGS.environment.provider.name
            ]["projects"][link.project.name]
        project_lock_file_data["links"].update(gen_link_data(link))

    save_data(lock_file_data)


def apply_project_data(project: LabbyProject):
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        lock_file_data = gen_lock_file_data(project)

    else:
        project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
            config.SETTINGS.environment.provider.name
        ]["projects"].get(project.name)

        if project_lock_file_data is None:
            lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name][
                "projects"
            ].update(gen_project_data(project))
        else:
            project_lock_file_data.update(labels=project.labels)

    save_data(lock_file_data)


def get_project_data(project_name: str) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        return None
    try:
        return lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name][
            "projects"
        ].get(project_name)
    except KeyError:
        # Initialize lock file data if new environment/provider
        lock_file_data.update(gen_lock_file_data())
        save_data(lock_file_data)
        return None


def get_node_data(node_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["nodes"].get(node_name)


def get_link_data(link_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["links"].get(link_name)


def delete_project_data(project_name: str) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        return None
    return lock_file_data[config.SETTINGS.environment.name][config.SETTINGS.environment.provider.name]["projects"].pop(
        project_name, None
    )


def delete_node_data(node_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["nodes"].pop(node_name, None)


def delete_link_data(link_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    lock_file_data = read_data(config.SETTINGS.lock_file)
    if not lock_file_data:
        return None
    project_lock_file_data = lock_file_data[config.SETTINGS.environment.name][
        config.SETTINGS.environment.provider.name
    ]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["links"].pop(link_name, None)
