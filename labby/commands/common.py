"""Common functionalities between commands."""
from __future__ import annotations
from typing import Tuple, TYPE_CHECKING

import typer

from labby import utils, config
from labby.models import LabbyNodeTemplate

if TYPE_CHECKING:
    # pylint: disable=all
    from labby.models import LabbyProvider, LabbyProject, LabbyNode, LabbyLink


def get_labby_objs_from_project(project_name: str) -> Tuple[LabbyProvider, LabbyProject]:
    """Gets a Provider and Project from a project's name.

    Args:
        project_name (str): Project name.

    Raises:
        typer.Exit: If project not found

    Returns:
        Tuple[LabbyProvider, LabbyProject]: Labby provider and project found.
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get project
    prj = provider.search_project(project_name=project_name)
    if not prj:
        utils.console.log(f"Project [cyan i]{project_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    return provider, prj


def get_labby_objs_from_node_template(template_name: str) -> Tuple[LabbyProvider, LabbyNodeTemplate]:
    """Gets a Provider and Project from a node template's name.

    Args:
        template_name (str): Node Template name.

    Raises:
        typer.Exit: If node template is not found.

    Returns:
        Tuple[LabbyProvider, LabbyNodeTemplate]: Provider and Node Template object.
    """
    # Get network lab provider
    provider = config.get_provider()

    # Get node template
    tplt = provider.search_template(template_name)
    if not tplt:
        utils.console.log(f"Node Template [cyan i]{template_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    return provider, tplt


def get_labby_objs_from_node(project_name: str, node_name: str) -> Tuple[LabbyProvider, LabbyProject, LabbyNode]:
    """Gets a Provider, Project and Node based on node's name.

    Args:
        project_name (str): Project name.
        node_name (str): Node name.

    Raises:
        typer.Exit: If node not found.

    Returns:
        Tuple[LabbyProvider, LabbyProject, LabbyNode]: Provider, project and node objects.
    """
    # Get network lab provider
    provider, prj = get_labby_objs_from_project(project_name=project_name)

    # Get node
    device = prj.search_node(node_name)
    if not device:
        utils.console.log(f"Node [cyan i]{node_name}[/] not found. Nothing to do...", style="error")
        raise typer.Exit(1)

    return provider, prj, device


def get_labby_objs_from_link(
    project_name: str,
    node_a: str,
    port_a: str,
    node_b: str,
    port_b: str,
) -> Tuple[LabbyProvider, LabbyProject, LabbyLink]:
    """Gets a Provider, Project and Link based on link's endpoints.

    Args:
        project_name (str): Project name.
        node_a (str): Node A
        port_a (str): Port A
        node_b (str): Node B
        port_b (str): Port B

    Raises:
        typer.Exit: If link not found.

    Returns:
        Tuple[LabbyProvider, LabbyProject, LabbyLink]: Provider, Project and Link object.
    """
    # Get network lab provider
    provider, prj = get_labby_objs_from_project(project_name=project_name)

    # Get link
    enlace = prj.search_link(node_a, port_a, node_b, port_b)
    if not enlace:
        utils.console.log(
            f"Link [cyan i]{node_a}: {port_a} == {node_b}: {port_b}[/] not found. Nothing to do...", style="error"
        )
        raise typer.Exit(1)

    return provider, prj, enlace
