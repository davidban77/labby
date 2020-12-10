import typer
import tomlkit

from pathlib import Path
from typing import Literal, MutableMapping, Optional, Any, Dict, List, Union
from pydantic import BaseSettings, AnyHttpUrl, FilePath, AnyUrl, BaseModel
from nornir.core.helpers.jinja_helper import render_from_file


APP_NAME = "labby"
BASE_CONFIG_TEMPLATE = Path(__file__).parent / "templates/base_config.toml.j2"


class ProviderVrnetlab(BaseModel):
    server_url: Optional[AnyUrl]
    verify_cert: bool = False


class ProviderEveng(BaseModel):
    server_url: Optional[AnyHttpUrl]
    user: Optional[str] = None
    # TODO: Issue with pydantic and SecretStr on Mac apparently need to test on docker
    password: Optional[str] = None
    # TODO: Issue with pydantic and bool comparison, needed to set as string
    verify_cert: bool = False


class ProviderGns3(BaseModel):
    server_url: Optional[AnyHttpUrl]
    user: Optional[str] = None
    password: Optional[str] = None
    verify_cert: bool = False


class EnvironmentSettings(BaseModel):
    name: str
    description: Optional[str]
    # provider: Optional[str]
    gns3: Optional[ProviderGns3]
    vrnetlab: Optional[ProviderVrnetlab]
    eve_ng: Optional[ProviderEveng]

    def get_provider(
        self, name: str
    ) -> Union[ProviderGns3, ProviderVrnetlab, ProviderEveng]:
        return getattr(self, name)

    class Config:
        # env_prefix = "LABBY_ENV_"
        # env_file = ".env"
        # env_file_encoding = "utf-8"
        extra = "ignore"
        validate_assignment = True


class NornirInventoryOptions(BaseModel):
    host_file: FilePath
    group_file: FilePath


class NornirInventory(BaseModel):
    plugin: str = "SimpleInventory"
    options: NornirInventoryOptions


class NornirRunner(BaseModel):
    plugin: str = "threaded"
    options: Dict[str, Any] = {"num_workers": 5}


class NornirSettings(BaseModel):
    runner: NornirRunner
    inventory: NornirInventory


class ProjectSettings(BaseModel):
    name: str
    description: Optional[str]
    version: Optional[str]
    authors: Optional[List[str]]
    nornir: NornirSettings

    class Config:
        # env_prefix = "LABBY_PROJECT_"
        # env_file = ".env"
        # env_file_encoding = "utf-8"
        extra = "ignore"
        validate_assignment = True


class LabbyGlobalSettings(BaseSettings):
    provider: Literal["gns3", "vrnetlab", "eve_ng"]
    environment: str
    project: Optional[str] = None
    debug: bool = False

    class Config:
        env_prefix = "LABBY_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        validate_assignment = True


class LabbySettings(BaseModel):
    labby: LabbyGlobalSettings
    # environment: Optional[EnvironmentSettings]
    # project: Optional[ProjectSettings]
    envs: Dict[str, EnvironmentSettings]
    prjs: Dict[str, ProjectSettings]

    def get_environment(self) -> EnvironmentSettings:
        try:
            return self.envs[self.labby.environment]
        except KeyError:
            raise ValueError(f"No environment {self.labby.environment} found")

    def get_project(self) -> ProjectSettings:
        try:
            if self.labby.project is None:
                raise KeyError
            return self.prjs[self.labby.project]
        except KeyError:
            raise ValueError(f"No project {self.labby.project} found")

    def get_provider_settings(
        self,
    ) -> Union[ProviderGns3, ProviderVrnetlab, ProviderEveng]:
        return self.get_environment().get_provider(self.labby.provider)


# SETTINGS = LabbySettings()
SETTINGS = None


def get_config_current_path() -> Path:
    """
    Returns labby.toml path of current dir
    """
    return Path.cwd() / "labby.toml"


def get_config_base_path() -> Path:
    """
    Returns labby.toml in user's home .config/labby dir
    """
    return (
        Path(
            typer.get_app_dir(APP_NAME, force_posix=True).replace(
                ".labby", ".config/labby"
            )
        )
        / "labby.toml"
    )


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


def load_toml(config_file: Path) -> MutableMapping:
    """
    Reades TOML file from Path
    """
    return tomlkit.loads(config_file.read_text())


def save_toml(config_file: Path, data: MutableMapping):
    """
    Saves TOML string to file
    """
    config_file.write_text(tomlkit.dumps(data))  # type: ignore
    return


def get_envs_config(config_data: MutableMapping) -> Dict[str, EnvironmentSettings]:
    aver = {}
    for env_data in config_data.get("environment", []):
        # print(env_data)
        aver[env_data["name"]] = EnvironmentSettings(**env_data)
    return aver
    # return {
    #     env_data["name"]: EnvironmentSettings(**env_data)
    #     for env_data in config_data.get("environment", [])
    # }


def get_prjs_config(config_data: MutableMapping) -> Dict[str, ProjectSettings]:
    return {
        project_config["name"]: ProjectSettings(
            name=project_config["name"],
            description=project_config.get("description"),
            version=project_config.get("version"),
            authors=project_config.get("authors"),
            nornir=NornirSettings(
                runner=project_config.get("runner", NornirRunner()),
                inventory=project_config.get("inventory"),
            ),
        )
        for project_config in config_data.get("project", [])
    }


def load(
    config_file: Optional[Path] = None,
    environment: Optional[str] = None,
    provider: Optional[str] = None,
    project: Optional[str] = None,
):
    """
    Read the config from a Path and return the labby settings.
    """
    if config_file is None:
        config_file = get_config_path()

    config_data = load_toml(config_file)
    # from rich import print
    # print(config_data)

    # Get Global Labby config
    global_config = config_data.get("labby", {})

    # Environments config
    environments_settings = get_envs_config(config_data)

    # Projects config
    projects_settings = get_prjs_config(config_data)

    # Labby global settings (override where possible)
    labby_settings = LabbyGlobalSettings(
        environment=environment
        if environment
        else global_config.get("environment", "default"),
        provider=provider if provider else global_config.get("provider"),
        project=project if project else global_config.get("project"),
        debug=global_config.get("debug", False),
    )

    global SETTINGS

    SETTINGS = LabbySettings(
        labby=labby_settings,
        envs=environments_settings,
        prjs=projects_settings,
    )

    # SETTINGS.load_environment(global_config.get("environment", "default"))

    # if global_config.get("project"):
    #     SETTINGS.load_project(global_config.get("project"))  # type: ignore


def create_config_data(data: MutableMapping) -> str:
    return render_from_file(
        path=str(BASE_CONFIG_TEMPLATE.parent),
        template=BASE_CONFIG_TEMPLATE.name,
        **data,
    )


# class Gns3Config(LabbyBaseSettings):
#     server_url: Optional[AnyHttpUrl] = None
#     user: Optional[str] = None
#     password: Optional[SecretStr] = None
#     verify_cert: bool = False


# class NornirRunnerConfig(LabbyBaseSettings):
#     plugin: str = "threaded"
#     options: Dict[str, Any] = {"num_workers": 5}


# class NornirInventoryOptions(LabbyBaseSettings):
#     host_file: FilePath
#     group_file: FilePath


# class NornirInventoryConfig(LabbyBaseSettings):
#     plugin: str = "SimpleInventory"
#     options: NornirInventoryOptions


# class NornirConfig(LabbyBaseSettings):
#     runner: NornirRunnerConfig = NornirRunnerConfig()
#     inventory: NornirInventoryConfig


# class LabbyConfig(LabbyBaseSettings):
#     environment: str = "default"
#     provider: Literal["gns3"] = "gns3"
#     project: Optional[str] = None
#     debug: bool = False


# class LabbySettings(LabbyBaseSettings):
#     labby: LabbyConfig = LabbyConfig()
#     gns3: Gns3Config = Gns3Config()
#     nornir: Optional[NornirConfig]

#     def get_provider_settings(self) -> MutableMapping:
#         return getattr(self, self.labby.provider).dict()


# def get_config_data(
#     data: MutableMapping,
# ) -> Tuple[MutableMapping, MutableMapping, MutableMapping]:
#     """
#     Based on a Dictionary of data, return the global and environment config
#     """
#     # Get all environment data
#     all_environments = data.get("environment", {})

#     # Get all projects data
#     all_projects = data.get("project", {})

#     # Get Global Labby config
#     global_config = data.get("labby", {})

#     # Get specific environment data for this run
#     environment_config = all_environments.get(
#         global_config.get("environment", "default"), {}
#     )

#     # Get specific project data for this run
#     project_config = all_projects.get(global_config.get("project", ""), {})

#     # Get Nornir config
#     nornir_config = dict(
#         runner=global_config.get("nornir", {}).get("runner", {}),
#         inventory=project_config.get("nornir", {}).get("inventory", {}),
#     )

#     return global_config, environment_config, nornir_config


# def create_config_data(parameter: str, value: Any) -> MutableMapping:
#     """
#     Based on a parameter (that can be set as nested with `.`) and a value, create
#     a config dictionary
#     """
#     if value == "false":
#         value = False
#     elif value == "true":
#         value = True
#     new_data = {}
#     _parameters = parameter.split(".")
#     _parameters.reverse()
#     for index, param in enumerate(_parameters):
#         if index == 0:
#             new_data = {param: value}
#         else:
#             new_data = {param: new_data}
#             # last_dict.update({param: last_dict})
#     # new_data.update(last_dict)
#     return new_data


# def update_config_data(config_file: Path, parameter: str, lue: str) -> MutableMapping:
#     """
#     Updates config data that is validated by the creation of labby settings
#     """
#     new_data = create_config_data(parameter, value)
#     config_data = load_toml(config_file)
#     merged_data = utils.mergedicts(config_data, new_data)
#     global_config, environment_config, nornir_config = get_config_data(merged_data)

#     try:
#         _ = LabbySettings(
#             labby=global_config, nornir=nornir_config, **environment_config
#         )
#         return merged_data
#     except Exception as err:
#         raise err


# def delete_config_data(config_file: Path, parameter: str) -> MutableMapping:
#     """
#     Delets part of config data and is validated by the creation of labby settings
#     """
#     config_data = load_toml(config_file)
#     merged_data = utils.delete_nested_key(config_data, parameter)
#     global_config, environment_config, nornir_config = get_config_data(merged_data)

#     try:
#         _ = LabbySettings(
#             labby=global_config, nornir=nornir_config, **environment_config
#         )
#         return merged_data
#     except Exception as err:
#         raise err


# def get_project_data(project_file: Path):
#     """
#     Loads Project TOML file and sets inventory to its resolved path
#     """
#     data = load_toml(project_file)
#     inv_options = data.get("nornir", {}).get("inventory", {}).get("options", {})
#     if inv_options.get("host_file") is not None:
#         inv_options["host_file"] = Path(
#             project_file.parent.resolve() / inv_options["host_file"]
#         )
#         inv_options["group_file"] = Path(
#             project_file.parent.resolve() / inv_options["group_file"]
#         )
#         data["nornir"]["inventory"]["options"] = inv_options
#     return data


# def load(config_file: Optional[Path] = None, project: Optional[str] = None):
#     """
#     Read the config from a Path and return the labby settings.
#     """
#     # config_file = verify_config_path(config_file)
#     if config_file is None:
#         config_file = get_config_path()

#     config_data = load_toml(config_file)

#     if project:
#         # It overrides project data from main config file
#         config_data["labby"]["project"] = project

#     # Get global and environment config data
#     print(config_data)
#     global_config, environment_config, nornir_config = get_config_data(config_data)
#     print(nornir_config)
#     if not nornir_config["runner"] or not nornir_config["inventory"]:


#     global SETTINGS

#     SETTINGS = LabbySettings(
#         labby=global_config, nornir=nornir_config, **environment_config
#     )
