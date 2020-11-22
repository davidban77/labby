import os
import pytest

from pathlib import Path
from toml import TomlDecodeError
from labby import settings


USER = os.getlogin()


def test_get_config_current_path():
    assert settings.get_config_current_path() == Path.cwd() / "labby.toml"


def test_get_config_base_path():
    assert (
        settings.get_config_base_path()
        == Path.home() / ".config" / "labby" / "labby.toml"
    )


def test_verify_config_path_valid_location(tmp_path):
    labby_config = tmp_path / "labby.toml"
    labby_config.write_text("LABBY")
    assert labby_config.read_text() == "LABBY"
    assert settings.verify_config_path(labby_config) == labby_config


def test_load_toml():
    toml_data = settings.load_toml(Path(__file__).parent / "data" / "labby.toml")
    assert "labby" in toml_data
    assert "environment" in toml_data
    assert toml_data["labby"]["environment"] == "aws"
    assert toml_data["labby"]["provider"] == "gns3"
    assert (
        toml_data["environment"]["aws"]["gns3"]["server_url"] == "http://gns3-server:80"
    )


def test_save_toml(tmp_path):
    toml_data = settings.load_toml(Path(__file__).parent / "data" / "labby.toml")
    settings.save_toml(tmp_path / "labby.toml", toml_data)
    new_toml_data = settings.load_toml(tmp_path / "labby.toml")
    assert "labby" in new_toml_data
    assert "environment" in new_toml_data
    assert new_toml_data["labby"]["environment"] == "aws"
    assert new_toml_data["labby"]["provider"] == "gns3"
    assert (
        new_toml_data["environment"]["aws"]["gns3"]["server_url"]
        == "http://gns3-server:80"
    )


def test_update_config_data():
    config_file = Path(__file__).parent / "data" / "labby.toml"
    new_data = settings.update_config_data(config_file, "labby.environment", "packet")
    assert "labby" in new_data
    assert "environment" in new_data
    assert new_data["labby"]["environment"] == "packet"


def test_delete_config_data():
    config_file = Path(__file__).parent / "data" / "labby.toml"
    new_data = settings.delete_config_data(config_file, "labby.environment")
    assert "labby" in new_data
    assert "environment" not in new_data["labby"]


def test_load_default_config():
    config = settings.load(Path(__file__).parent / "data" / "default_labby.toml")
    assert config.labby.provider == "gns3"
    assert config.labby.environment == "default"
    assert config.labby.debug is False
    assert config.gns3.server_url is None
    assert config.gns3.user == USER
    assert config.gns3.password is None
    assert config.gns3.verify_cert is False


def test_load_config():
    config = settings.load(Path(__file__).parent / "data" / "labby.toml")
    assert config.labby.provider == "gns3"
    assert config.labby.environment == "aws"
    assert config.labby.debug is False
    assert config.gns3.server_url.scheme == "http"
    assert config.gns3.server_url.port == "80"
    assert config.gns3.server_url.host == "gns3-server"
    assert config.gns3.server_url.host_type == "int_domain"
    assert config.gns3.user == USER
    assert config.gns3.password is None
    assert config.gns3.verify_cert is False


def test_load_invalid_toml():
    with pytest.raises(TomlDecodeError, match="Found invalid character"):
        settings.load(Path(__file__).parent / "data" / "invalid_labby.toml")
