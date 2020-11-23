import typer
import toml

from pathlib import Path
from typing import MutableMapping, Optional, Literal, Any, Tuple
from pydantic import BaseSettings, AnyHttpUrl, SecretStr
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


class LabbyConfig(LabbyBaseSettings):
    environment: str = "default"
    provider: Literal["gns3"] = "gns3"
    debug: bool = False


class LabbySettings(LabbyBaseSettings):
    labby: LabbyConfig = LabbyConfig()
    gns3: Gns3Config = Gns3Config()

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


def get_config_data(data: MutableMapping) -> Tuple[MutableMapping, MutableMapping]:
    """
    Based on a Dictionary of data, return the global and environment config
    """
    # Get all environment data
    all_environments = data.get("environment", {})

    # Get Global Labby config
    global_config = data.get("labby", {})

    # Get specific environment data for this run
    environment_config = all_environments.get(
        global_config.get("environment", "default"), {}
    )
    return global_config, environment_config


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
    global_config, environment_config = get_config_data(merged_data)

    try:
        _ = LabbySettings(labby=global_config, **environment_config)
        return merged_data
    except Exception as err:
        raise err


def delete_config_data(config_file: Path, parameter: str) -> MutableMapping:
    """
    Delets part of config data and is validated by the creation of labby settings
    """
    config_data = load_toml(config_file)
    merged_data = utils.delete_nested_key(config_data, parameter)
    global_config, environment_config = get_config_data(merged_data)

    try:
        _ = LabbySettings(labby=global_config, **environment_config)
        return merged_data
    except Exception as err:
        raise err


def load(config_file: Optional[Path] = None):
    """
    Read the config from a Path and return the labby settings.
    """
    # config_file = verify_config_path(config_file)
    if config_file is None:
        config_file = get_config_path()

    config_data = load_toml(config_file)

    # Get global and environment config data
    global_config, environment_config = get_config_data(config_data)

    global SETTINGS

    SETTINGS = LabbySettings(labby=global_config, **environment_config)
