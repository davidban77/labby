"""Lock file operations module."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional

import typer
from labby import config, utils
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=all
    from labby.models import LabbyLink, LabbyNode, LabbyProject


def get_lock_file():
    """Get lock_file object from SETTINGS.

    Raises:
        ValueError: Configuration not set

    Returns:
        Path: Lock file Path object
    """
    if config.SETTINGS is None:
        raise ValueError("Configuration is not set")
    return config.SETTINGS.lock_file


def gen_node_data(node: LabbyNode) -> Dict[str, Any]:
    """Generate Node data for lock file.

    Args:
        node (LabbyNode): Labby node object

    Returns:
        Dict[str, Any]: {node_name: {labels: labels, mgmt_port: mgmt_port, mgmt_addr}}
    """
    return {
        node.name: {
            "labels": node.labels,
            "mgmt_port": node.mgmt_port,
            "mgmt_addr": node.mgmt_addr,
            "config_managed": node.config_managed,
        }
    }


def gen_link_data(link: LabbyLink) -> Dict[str, Any]:
    """Generate Link data for lock file.

    Args:
        link (LabbyLink): Labby link object

    Returns:
        Dict[str, Any]: {link_name: {labels: labels}}
    """
    return {link.name: {"labels": link.labels}}


def gen_project_data(project: LabbyProject):
    """Generate Project data for lock file.

    Args:
        project (LabbyProject): Labby Project object

    Returns:
        Dict[str, Any]: {project_name: {labels: labels, nodes: nodes_data, links: links_data}}
    """
    nodes_lock_data = {}
    for _, node in project.nodes.items():
        nodes_lock_data.update(gen_node_data(node))
    links_lock_data = {}
    for _, link in project.links.items():
        links_lock_data.update(gen_link_data(link))
    return {project.name: {"labels": project.labels, "nodes": nodes_lock_data, "links": links_lock_data}}


def gen_lock_file_data(project: Optional[LabbyProject] = None):
    """Generate lock file data.

    Args:
        project (Optional[LabbyProject], optional): Labby project object. Defaults to None.

    Returns:
        Dict[str, Any]: {env_name: {env_provider: {projects: project_data}}}
    """
    env = config.get_environment()

    # Initialize lock file data
    lock_file_data = {env.name: {env.provider.name: {"projects": gen_project_data(project) if project else {}}}}

    return lock_file_data


def read_data(file_path: Path) -> Optional[MutableMapping[str, Any]]:
    """Read JSON file.

    Args:
        file_path (Path): File path

    Returns:
        Optional[MutableMapping[str, Any]]: JSON loaded data
    """
    if file_path.exists():
        # return toml.loads(file_path.read_text())
        data = json.loads(file_path.read_text())
        if not data:
            return None
        return data
    else:
        return None


def save_data(lock_file_data: MutableMapping[str, Any]):
    """Save lock file data to JSON file.

    Args:
        lock_file_data (MutableMapping[str, Any]): Lock file data
    """
    _lock_file = get_lock_file()
    _lock_file.write_text(json.dumps(lock_file_data, indent=4))


def apply_node_data(node: LabbyNode, project: Optional[LabbyProject] = None):
    """Apply node lock file data.

    Args:
        node (LabbyNode): Labby node object
        project (Optional[LabbyProject], optional): Labby project object. Defaults to None.

    Raises:
        typer.Exit: Cannot save node in lock file because project not present.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        if not project:
            utils.console.log("Cannot save node in lock file", style="error")
            raise typer.Exit(1)
        lock_file_data = gen_lock_file_data(project)

    else:
        env = config.get_environment()
        project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(node.project.name)

        if project_lock_file_data is None:
            if not project:
                utils.console.log("Cannot save node in lock file", style="error")
                raise typer.Exit(1)
            lock_file_data[env.name][env.provider.name]["projects"].update(gen_project_data(project))
            project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"][node.project.name]
        project_lock_file_data["nodes"].update(gen_node_data(node))

    save_data(lock_file_data)


def apply_link_data(link: LabbyLink, project: Optional[LabbyProject] = None):
    """Apply link lock file data.

    Args:
        link (LabbyLink): Labby link object
        project (Optional[LabbyProject], optional): Labby project object. Defaults to None.

    Raises:
        typer.Exit: Cannot save node in lock file because project not present.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        if not project:
            utils.console.log("Cannot save link in lock file", style="error")
            raise typer.Exit(1)
        lock_file_data = gen_lock_file_data(project)

    else:
        env = config.get_environment()
        project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(link.project.name)

        if project_lock_file_data is None:
            if not project:
                utils.console.log("Cannot save link in lock file, missing project data", style="error")
                raise typer.Exit(1)
            lock_file_data[env.name][env.provider.name]["projects"].update(gen_project_data(project))
            project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"][link.project.name]
        project_lock_file_data["links"].update(gen_link_data(link))

    save_data(lock_file_data)


def apply_project_data(project: LabbyProject):
    """Apply project lock file data.

    Args:
        project (LabbyProject): Labby project object.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        lock_file_data = gen_lock_file_data(project)

    else:
        env = config.get_environment()
        project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(project.name)

        if project_lock_file_data is None:
            lock_file_data[env.name][env.provider.name]["projects"].update(gen_project_data(project))
        else:
            project_lock_file_data.update(labels=project.labels)

    save_data(lock_file_data)


def get_project_data(project_name: str) -> Optional[Dict[str, Any]]:
    """Get project data from lock file.

    Args:
        project_name (str): Name of the project

    Returns:
        Optional[Dict[str, Any]]: Project data if available.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        return None
    try:
        env = config.get_environment()
        return lock_file_data[env.name][env.provider.name]["projects"].get(project_name)
    except KeyError:
        # Initialize lock file data if new environment/provider
        lock_file_data.update(gen_lock_file_data())
        save_data(lock_file_data)
        return None


def get_node_data(node_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    """Get node data from lock file.

    Args:
        node_name (str): Name of the node.
        project_name (str): Name of the project.

    Returns:
        Optional[Dict[str, Any]]: Node data if available.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        return None

    env = config.get_environment()
    project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["nodes"].get(node_name)


def get_link_data(link_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    """Get link data from lock file.

    Args:
        link_name (str): Name of the link.
        project_name (str): Name of the project.

    Returns:
        Optional[Dict[str, Any]]: Link data if available.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        return None

    env = config.get_environment()
    project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["links"].get(link_name)


def delete_project_data(project_name: str) -> Optional[Dict[str, Any]]:
    """Delete project data on lock file.

    Args:
        project_name (str): Name of the project.

    Returns:
        Optional[Dict[str, Any]]: Project data if present.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        return None

    env = config.get_environment()
    return lock_file_data[env.name][env.provider.name]["projects"].pop(project_name, None)


def delete_node_data(node_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    """Delete node data on lock file.

    Args:
        node_name (str): Name of the node.
        project_name (str): Name of the project.

    Returns:
        Optional[Dict[str, Any]]: Node data if present.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        return None

    env = config.get_environment()
    project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["nodes"].pop(node_name, None)


def delete_link_data(link_name: str, project_name: str) -> Optional[Dict[str, Any]]:
    """Delete link data on lock file.

    Args:
        link_name (str): Name of the link.
        project_name (str): Name of the project.

    Returns:
        Optional[Dict[str, Any]]: Link data if present.
    """
    lock_file_data = read_data(get_lock_file())
    if lock_file_data is None:
        return None

    env = config.get_environment()
    project_lock_file_data = lock_file_data[env.name][env.provider.name]["projects"].get(project_name)

    if project_lock_file_data is None:
        return None

    return project_lock_file_data["links"].pop(link_name, None)
