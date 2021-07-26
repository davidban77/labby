"""Labby build command.

Handles the complete build of a Labby Project.

Example:
> labby build project --project-file "myproject.yaml"
"""
import typer
from pathlib import Path
from netaddr import IPNetwork
from nornir.core.task import AggregatedResult
from nornir.core.helpers.jinja_helper import render_from_file
from labby import utils
from labby.project_data import get_project_from_file
from labby.nornir_tasks import config_task


app = typer.Typer(help="Builds a complete Network Provider Lab in a declarative way.")


@app.command(short_help="Builds a Project in a declarative way.")
def project(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
):
    """
    Build a Project in a declarative way.

    The project is built based on the contents of the project file.

    Example:

    > labby build project --project-file "myproject.yaml"
    """
    project, project_data = get_project_from_file(project_file)

    # Create nodes
    for node_spec in project_data.nodes_spec:
        for node in node_spec.get("nodes", []):
            node_name = node["name"]
            print(f"Creating node: {node_name}")
            node = project.create_node(name=node_name, template=node_spec["template"], **node)

            # Bootstrap noode
            node.bootstrap(config="this where the config should be for bootstrap")

    # Create links
    for link_spec in project_data.links_spec:
        for link_info in link_spec.get("links", []):
            # link_name = link_info["name"]
            # print(f"Creating link: {link_name}")
            link = project.create_link(
                node_a=link_spec["node"],
                port_a=link_info["port"],
                port_b=link_info["port_b"],
                node_b=link_info["node_b"],
                filters=link_info.get("filters"),
                **link_info,
            )
            print(f"Created link: {link}")

    # Render configs
    if project_data.template:
        for node_name, node in project.nodes.items():
            cfg_data = render_from_file(
                path=str(Path(project_data.template).parent),
                template=Path(project_data.template).name,
                jinja_filters={"ipaddr": utils.ipaddr_renderer},
                **dict(project=project, node=node, **project_data.vars),
            )

            # Configure nodes
            project.init_nornir()
            if project.nornir is None:
                raise ValueError("Nornir not initialized")
            responses: AggregatedResult = project.nornir.run(task=config_task, config=cfg_data)
            print(responses)


@app.command(short_help="Builds a Project Topology.")
def topology(
    project_file: Path = typer.Option(..., "--project-file", "-f", help="Project file", envvar="LABBY_PROJECT_FILE"),
):
    """
    Builds a topology from a given project file.

    Example:

    > labby build topology --project-file "myproject.yml"
    """
    project, project_data = get_project_from_file(project_file)

    mgmt_network = IPNetwork(project_data.mgmt_network)
    # Verify nodes created to be managed match the ones in the project

    # Create nodes
    index = 0
    for node_spec in project_data.nodes_spec:
        for node_name in node_spec.get("nodes", []):

            node = project.search_node(name=node_name)

            # Validate devices exists in the project
            if node:
                utils.console.log(f"[b]({project.name})[/] Node already created: [i dark_orange3]{node_name}")
                continue

            params = dict()

            # Update params
            params["labels"] = node_spec.get("labels", [])

            if node_spec.get("config_managed"):
                params["config_managed"] = node_spec.get("config_managed")

            # TODO: Add support to detect changes in node.mgmt_addr assignments
            params["mgmt_port"] = node_spec.get("mgmt_port")
            params["mgmt_addr"] = f"{list(mgmt_network.iter_hosts())[index]}/{mgmt_network.prefixlen}"
            index += 1

            utils.console.log(f"[b]({project.name})[/] Creating node: [i dark_orange3]{node_name}")
            _ = project.create_node(name=node_name, template=node_spec["template"], **params)

    # Create links
    for link_spec in project_data.links_spec:
        for link_info in link_spec.get("links", []):

            utils.console.log(f"[b]({project.name})[/] Creating link: [i dark_orange3]{link_info['name']}")
            _ = project.create_link(
                node_a=link_spec["node"],
                port_a=link_info["port"],
                port_b=link_info["port_b"],
                node_b=link_info["node_b"],
                filters=link_info.get("filters"),
                **link_info,
            )
