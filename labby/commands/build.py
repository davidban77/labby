"""Labby build command.

Handles the complete build of a Labby Project.

Example:
> labby build project --project-file "myproject.yaml"
"""
import typer
from pathlib import Path
from labby import utils
from labby import config


app = typer.Typer(help="Builds a complete Network Provider Lab in a declarative way.")


SHOW_RUN_COMMANDS = {
    "arista_eos": "show run",
    "cisco_ios": "show run",
    "cisco_iosxe": "show run",
    "cisco_nxos": "show run",
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

            # Check creds
            self.check_creds()

            # Project nodes and links
            self.nodes_spec = self.project_data["nodes_spec"]
            self.links_spec = self.project_data["links_spec"]

            # Vars
            self.vars = self.project_data.get("vars", {})

        else:
            raise FileNotFoundError(f"Project file not found: {project_file}")

    def get_project_data(self) -> dict:
        """Get the project data from the project file."""
        return utils.load_yaml_file(str(self.project_file))

    def check_creds(self) -> None:
        """Check if the credentials are valid."""
        if not utils.check_creds(self.mgmt_network, self.mgmt_creds):
            raise ValueError("Invalid credentials for the management network")


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
    project_data = ProjectData(project_file)
    print(f"Project name: {project_data.name}")
    provider = config.get_provider()
    project = provider.search_project(project_name=project_data.name)
    if project:
        print(f"Project already exists: {project.name}")
    else:
        print(f"Creating project: {project_data.name}")
        # TODO: fix with the right parameters
        project = provider.create_project(project_name=project_data.name, **project_data.project_data["main"])

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

    # Configure nodes
