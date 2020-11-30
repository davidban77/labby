import typer
import toml

from pathlib import Path
from typing import MutableMapping, Optional, Literal, Any, Tuple, Dict
from pydantic import BaseSettings, AnyHttpUrl, SecretStr, FilePath
from labby import utils


APP_NAME = "labby"


class LabbyBaseSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        validate_assignment = True


class Gns3Config(LabbyBaseSettings):
    server_url: Optional[AnyHttpUrl] = None
    user: Optional[str] = None
    password: Optional[SecretStr] = None
    verify_cert: bool = False


class NornirRunnerConfig(LabbyBaseSettings):
    plugin: str = "threaded"
    options: Dict[str, Any] = {"num_workers": 5}


class NornirInventoryOptions(LabbyBaseSettings):
    host_file: Optional[FilePath] = None
    group_file: Optional[FilePath] = None


class NornirInventoryConfig(LabbyBaseSettings):
    plugin: str = "SimpleInventory"
    options: Optional[NornirInventoryOptions]


class NornirConfig(LabbyBaseSettings):
    runner: NornirRunnerConfig = NornirRunnerConfig()
    inventory: NornirInventoryConfig = NornirInventoryConfig()


class LabbyConfig(LabbyBaseSettings):
    environment: str = "default"
    provider: Literal["gns3"] = "gns3"
    project: Optional[str] = None
    debug: bool = False


class LabbySettings(LabbyBaseSettings):
    labby: LabbyConfig = LabbyConfig()
    gns3: Gns3Config = Gns3Config()
    nornir: NornirConfig = NornirConfig()

    def get_provider_settings(self) -> MutableMapping:
        return getattr(self, self.labby.provider).dict()


SETTINGS = LabbySettings()


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
    return toml.loads(config_file.read_text())


def save_toml(config_file: Path, data: MutableMapping):
    """
    Saves TOML string to file
    """
    config_file.write_text(toml.dumps(data))
    return


def get_config_data(
    data: MutableMapping,
) -> Tuple[MutableMapping, MutableMapping, MutableMapping]:
    """
    Based on a Dictionary of data, return the global and environment config
    """
    # Get all environment data
    all_environments = data.get("environment", {})

    # Get all projects data
    all_projects = data.get("project", {})

    # Get Global Labby config
    global_config = data.get("labby", {})

    # Get specific environment data for this run
    environment_config = all_environments.get(
        global_config.get("environment", "default"), {}
    )

    # Get specific project data for this run
    project_config = all_projects.get(global_config.get("project", ""), {})

    # Get Nornir config
    nornir_config = dict(
        runner=global_config.get("nornir", {}).get("runner", {}),
        inventory=project_config.get("nornir", {}).get("inventory", {}),
    )

    return global_config, environment_config, nornir_config


def create_config_data(parameter: str, value: Any) -> MutableMapping:
    """
    Based on a parameter (that can be set as nested with `.`) and a value, create
    a config dictionary
    """
    if value == "false":
        value = False
    elif value == "true":
        value = True
    new_data = {}
    _parameters = parameter.split(".")
    _parameters.reverse()
    for index, param in enumerate(_parameters):
        if index == 0:
            new_data = {param: value}
        else:
            new_data = {param: new_data}
            # last_dict.update({param: last_dict})
    # new_data.update(last_dict)
    return new_data


def update_config_data(config_file: Path, parameter: str, value: str) -> MutableMapping:
    """
    Updates config data that is validated by the creation of labby settings
    """
    new_data = create_config_data(parameter, value)
    config_data = load_toml(config_file)
    merged_data = utils.mergedicts(config_data, new_data)
    global_config, environment_config, nornir_config = get_config_data(merged_data)

    try:
        _ = LabbySettings(
            labby=global_config, nornir=nornir_config, **environment_config
        )
        return merged_data
    except Exception as err:
        raise err


def delete_config_data(config_file: Path, parameter: str) -> MutableMapping:
    """
    Delets part of config data and is validated by the creation of labby settings
    """
    config_data = load_toml(config_file)
    merged_data = utils.delete_nested_key(config_data, parameter)
    global_config, environment_config, nornir_config = get_config_data(merged_data)

    try:
        _ = LabbySettings(
            labby=global_config, nornir=nornir_config, **environment_config
        )
        return merged_data
    except Exception as err:
        raise err


def get_project_data(project_file: Path):
    """
    Loads Project TOML file and sets inventory to its resolved path
    """
    data = load_toml(project_file)
    inv_options = data.get("nornir", {}).get("inventory", {}).get("options", {})
    if inv_options.get("host_file") is not None:
        inv_options["host_file"] = Path(
            project_file.parent.resolve() / inv_options["host_file"]
        )
        inv_options["group_file"] = Path(
            project_file.parent.resolve() / inv_options["group_file"]
        )
        data["nornir"]["inventory"]["options"] = inv_options
    return data


def load(config_file: Optional[Path] = None, project_file: Optional[Path] = None):
    """
    Read the config from a Path and return the labby settings.
    """
    # config_file = verify_config_path(config_file)
    if config_file is None:
        config_file = get_config_path()

    config_data = load_toml(config_file)

    if project_file:
        # It overrides project data from main config file
        config_data["project"][project_file.stem] = get_project_data(project_file)

    # Get global and environment config data
    global_config, environment_config, nornir_config = get_config_data(config_data)

    global SETTINGS

    SETTINGS = LabbySettings(
        labby=global_config, nornir=nornir_config, **environment_config
    )
