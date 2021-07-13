import os
import typer
import toml
# from labby.providers import register_service
from labby import utils

from pathlib import Path
from typing import MutableMapping, Optional, Dict, List, Any, Literal

# from nornir.core.helpers.jinja_helper import render_from_file
# from rich.table import Table
from pydantic import (
    AnyUrl,
    Field,
    BaseSettings,
    IPvAnyNetwork,
    SecretStr,
)


APP_NAME = "labby"
# BASE_CONFIG_TEMPLATE = Path(__file__).parent / "templates/base_config.toml.j2"
SETTINGS = None
DEBUG = False
PROJECT_SETTINGS = None
PROVIDER_NAME = os.getenv("LABBY_PROVIDER_NAME")
ENVIRONMENT_NAME = os.getenv("LABBY_ENVIRONMENT_NAME")


class LabbyBaseConfig:
    env_prefix = "LABBY_"
    env_file = ".env"
    env_file_encoding = "utf-8"
    extra = "ignore"
    validate_assignment = True


class ProviderSettings(BaseSettings):
    name: str
    kind: Literal["gns3", "eve_ng", "vrnetlab"]
    server_url: Optional[AnyUrl]
    user: Optional[str] = None
    password: Optional[SecretStr] = None
    verify_cert: bool = False

    class Config:
        env_prefix = "LABBY_PROVIDER_"


class NornirInventoryOptions(BaseSettings):
    host_file: Path = Path.cwd() / "inventory/groups.yml"
    group_file: Path = Path.cwd() / "inventory/hosts.yml"

    class Config(LabbyBaseConfig):
        env_prefix = "LABBY_NORNIR_INVENTORY_OPTIONS_"


class NornirInventory(BaseSettings):
    plugin: str = "SimpleInventory"
    options: NornirInventoryOptions

    class Config(LabbyBaseConfig):
        env_prefix = "LABBY_NORNIR_INVENTORY_"


class NornirRunner(BaseSettings):
    plugin: str = "threaded"
    options: Dict[str, Any] = {"num_workers": 5}

    class Config(LabbyBaseConfig):
        env_prefix = "LABBY_NORNIR_RUNNER_"


class EnvironmentSettings(BaseSettings):
    name: str
    description: Optional[str]
    provider: ProviderSettings
    nornir_runner: NornirRunner
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        env_prefix = "LABBY_ENVIRONMENT_"


class NodeSpec(BaseSettings):
    template: str
    nodes: List[str]
    device_type: str
    mgmt_interface: Optional[str]
    config_managed: bool = True


class LinkSpec(BaseSettings):
    node_a: str
    port_a: str
    node_b: str
    port_b: str
    link_filter: Optional[Dict[str, Any]] = None


class ProjectSettings(BaseSettings):
    name: str
    description: Optional[str]
    contributors: Optional[List[str]]
    version: Optional[str]
    nodes_spec: List[NodeSpec]
    links_spec: List[LinkSpec]
    mgmt_net: Optional[IPvAnyNetwork] = None
    mgmt_user: str
    mgmt_password: SecretStr
    nornir_inventory: Optional[NornirInventory] = None

    class Config(LabbyBaseConfig):
        env_prefix = "LABBY_PROJECT_"


class LabbySettings(BaseSettings):
    environment: EnvironmentSettings
    lock_file: Path
    debug: bool = False

    class Config(LabbyBaseConfig):
        # env_prefix = "LABBY_SETTINGS_"
        pass


def generate_default_provider_name(server_url: str) -> Optional[str]:
    return utils.dissect_url(server_url)[1]


def get_config_current_path() -> Path:
    """
    Returns labby.toml path of current dir
    """
    return Path.cwd() / "labby.toml"


def get_config_base_path() -> Path:
    """
    Returns labby.toml in user's home .config/labby dir
    """
    return Path(typer.get_app_dir(APP_NAME, force_posix=True).replace(".labby", ".config/labby")) / "labby.toml"


def get_config_path() -> Path:
    """
    Verifies config on current dir and lastly against user's home .config/labby dir
    """
    config_file = get_config_current_path()
    if not config_file.exists():
        config_file = get_config_base_path()
    if not config_file.is_file():
        raise ValueError("Config file not found")
    return config_file


def get_config_env() -> EnvironmentSettings:
    """Get Environment object from SETTINGS.

    Raises:
        ValueError: Configuration not set

    Returns:
        EnvironmentSettings: Environment object
    """
    if SETTINGS is None:
        raise ValueError("Configuration is not set")
    return SETTINGS.environment


def load_toml(config_file: Path) -> MutableMapping:
    """
    Reades TOML file from Path
    """
    return toml.loads(config_file.read_text())


def save_toml(config_file: Path, data: MutableMapping):
    """
    Saves TOML string to file
    """
    config_file.write_text(toml.dumps(data))  # type: ignore
    return


def get_provider_settings(provider_name: str, providers_data: Dict[str, Any]) -> ProviderSettings:
    provider_args = dict(name=provider_name)

    try:
        provider_settings = providers_data[provider_args["name"]]
    except KeyError:
        raise ValueError(f"Provider '{provider_args['name']}' not found")

    if "kind" in provider_settings:
        provider_args.update(kind=provider_settings["kind"])

    if "server_url" in provider_settings:
        provider_args.update(server_url=provider_settings["server_url"])

    if "user" in provider_settings:
        provider_args.update(user=provider_settings["user"])

    if "password" in provider_settings:
        provider_args.update(password=provider_settings["password"])

    if "verify_cert" in provider_settings:
        provider_args.update(verify_cert=provider_settings["verify_cert"])

    return ProviderSettings(**provider_args)


def get_nornir_runner_settings(nornir_data: Dict[str, Any]) -> NornirRunner:
    nornir_args: Dict[str, Any] = {}
    if "plugin" in nornir_data:
        nornir_args.update(plugin=nornir_data["plugin"])
    if "options" in nornir_data:
        nornir_args.update(options=nornir_data["options"])

    return NornirRunner(**nornir_args)


def get_env_settings(
    environment_name: Optional[str], provider_name: Optional[str], config_data: MutableMapping[str, Any]
) -> EnvironmentSettings:
    envs = config_data.get("environment", {})
    env_args: Dict[str, Any] = {}

    # Get environment name
    if environment_name is None:
        environment_name = config_data.get("main", {}).get("environment")
        if environment_name is None:
            try:
                environment_name = os.environ["LABBY_ENVIRONMENT_NAME"]
            except KeyError:
                raise ValueError("Environment name needs to be set as CLI option, config or environment variable")
    env_args.update(name=environment_name)

    try:
        env_settings = envs[env_args["name"]]
    except KeyError:
        raise ValueError(f"Environment '{env_args['name']}' not found")

    providers = env_settings.get("providers", {})

    # Get provider name
    if provider_name is None:
        provider_name = env_settings.get("provider")
        if provider_name is None:
            try:
                provider_name = os.environ["LABBY_PROVIDER_NAME"]
            except KeyError:
                raise ValueError("Provider name needs to be set as CLI option, config or environment variable")

    # Set Provider settings
    env_args.update(provider=get_provider_settings(provider_name, providers))

    # Set Nornir Runner settings
    env_args.update(nornir_runner=get_nornir_runner_settings(env_settings.get("nornir_runner", {})))

    # Get extra options
    if "meta" in env_settings:
        env_args.update(meta=env_settings["meta"])

    if "description" in env_settings:
        env_args.update(description=env_settings["description"])

    return EnvironmentSettings(**env_args)


def load_config(
    config_file: Optional[Path] = None,
    environment_name: Optional[str] = ENVIRONMENT_NAME,
    provider_name: Optional[str] = PROVIDER_NAME,
    debug: bool = False,
):
    """
    Read the config from a Path and return the labby settings.
    """
    if config_file is None:
        config_file = get_config_path()

    config_data = load_toml(config_file)

    # Environment config
    environment = get_env_settings(environment_name, provider_name, config_data)

    options: Dict[str, Any] = {"lock_file": config_file.parent / ".labby.json"}

    if debug is not None:
        options.update(debug=debug)

    global SETTINGS

    SETTINGS = LabbySettings(environment=environment, **options)

    global DEBUG

    DEBUG = SETTINGS.debug

    # # Register each provider environment
    # register_service(environment.provider.name, environment.provider.type)


def get_nornir_inventory_settings(nornir_data: Dict[str, Any], project_file: Path) -> NornirInventory:
    group_file = Path(nornir_data["group_file"])
    if not group_file.is_absolute():
        group_file = project_file.parent / group_file
    host_file = Path(nornir_data["host_file"])
    if not host_file.is_absolute():
        host_file = project_file.parent / host_file

    return NornirInventory(options=NornirInventoryOptions(group_file=group_file, host_file=host_file))


def get_project_node_spec(node_data: Dict[str, Any]) -> NodeSpec:
    return NodeSpec(**node_data)


def get_project_link_spec(link_data: Dict[str, Any]) -> List[LinkSpec]:
    links = []
    for link in link_data["links"]:
        links.append(
            LinkSpec(
                node_a=link_data["node"],
                port_a=link["port"],
                node_b=link["node_b"],
                port_b=link["port_b"],
                link_filter=link.get("filter"),
            )
        )

    return links


def load_project(project_file: Optional[Path]):
    if project_file is None:
        project_file = Path.cwd() / "labby_project.toml"

    project_data = load_toml(project_file)

    nodes_spec = []
    for node_spec in project_data["nodes_spec"]:
        nodes_spec.append(get_project_node_spec(node_spec))

    links_spec = []
    for link_spec in project_data["links_spec"]:
        links_spec.extend(get_project_link_spec(link_spec))

    options = {}

    # Determine main options
    for option in ["name", "description", "version", "contributors", "mgmt_net"]:
        if project_data["main"].get(option) is not None:
            options.update({option: project_data["main"].get(option)})

    options.update(
        nornir_inventory=get_nornir_inventory_settings(project_data["main"].get("nornir_inventory", {}), project_file)
    )

    # Determine project creds
    if project_data["main"].get("mgmt_user") is not None:
        options.update(mgmt_user=project_data["main"]["mgmt_user"])
    if project_data["main"].get("mgmt_password") is not None:
        options.update(mgmt_password=project_data["main"]["mgmt_password"])

    global PROJECT_SETTINGS

    PROJECT_SETTINGS = ProjectSettings(nodes_spec=nodes_spec, links_spec=links_spec, **options)


#####################
# AQUI AQUI AQUI AQUI
# def create_config_data(data: MutableMapping) -> str:
#     return render_from_file(
#         path=str(BASE_CONFIG_TEMPLATE.parent),
#         template=BASE_CONFIG_TEMPLATE.name,
#         **data,
#     )


# def create_environment_table() -> Table:
#     table = Table(
#         show_header=True,
#         header_style="bold cyan",
#         title="Network Lab Providers",
#         title_style="bold cyan",
#     )
#     table.add_column("Environment", style="bold", justify="center")
#     table.add_column("Description")
#     table.add_column("Network Provider")
#     table.add_column("Type")
#     table.add_column("URL", overflow="fold")
#     table.add_column("Version")
#     table.add_column("Online", justify="center")
#     table.add_column("Selected", justify="center")
#     return table


# def add_environment_data_table(
#     env_name: str, env_settings: EnvironmentSettings, table: Table
# ):
#     for provider_settings in env_settings.providers:
#         try:
#             provider = provider_setup(provider_settings.name, provider_settings)
#             provider_version = provider.get_version()
#             provider_online = "[green]Yes[/]"
#             utils.console.log(f"Provider {provider_settings.name} data collected")
#         except NotImplementedError:
#             provider_version = "[red bold]NotImplemented[/]"
#             provider_online = "[red]No[/]"
#             utils.console.log(f"Provider type {provider_settings.type} not implemented")
#         # TODO: Need to fix gns3fy timeout/unreachable for get_version
#         except Exception:
#             provider_version = "[red]N/A[/]"
#             provider_online = "[red]No[/]"
#             utils.console.log(f"Provider {provider_settings.name} unreachable")

#         if env_name == SETTINGS.labby.environment:
#             provider_selected = "[green bold]Yes[/]"
#         else:
#             provider_selected = "[red bold]No[/]"

#         table.add_row(
#             env_name,
#             env_settings.description,
#             provider_settings.name,
#             f"[bold]{provider_settings.type.upper()}[/]",
#             provider_settings.server_url,
#             provider_version,
#             provider_online,
#             provider_selected,
#         )


# def get_environments_table() -> Table:
#     table = create_environment_table()
#     for env, env_settings in SETTINGS.envs.items():
#         with utils.console.status(
#             "[bold cyan] Checking provider availability", spinner="aesthetic"
#         ):
#             add_environment_data_table(env, env_settings, table)

#     return table


# def get_environment_detail_table(environment: str) -> Table:
#     table = create_environment_table()
#     add_environment_data_table(
#         env_name=environment, env_settings=SETTINGS.envs[environment], table=table
#     )
#     return table


# def get_environment_metadata_table(environment: str) -> Table:
#     table = Table(
#         show_header=True,
#         header_style="bold cyan",
#         title="Metadata",
#         title_style="bold cyan",
#     )
#     table.add_column("Field", style="bold", justify="center")
#     table.add_column("Value")
#     for k, v in SETTINGS.envs[environment].metadata.items():
#         table.add_row(k, v)
#     return table


# def get_projects_table() -> Table:
#     table = Table(
#         show_header=True,
#         header_style="bold_cyan",
#         title="Network Lab Projects",
#         title_style="bold cyan",
#     )
#     table.add_column("Project", style="bold", justify="center")
#     table.add_column("Description")
#     table.add_column("Version")
#     table.add_column("Authors")
#     table.add_column("Online", justify="center")
#     table.add_column("Selected", justify="center")
