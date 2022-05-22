"""Module for testing labby settings."""
from pathlib import Path
import pytest
from toml import TomlDecodeError
from labby.config import get_config_current_path, get_config_base_path, load_toml, save_toml, SETTINGS, load_config


@pytest.fixture()
def mock_env_vars(monkeypatch):
    """Fixture for mocking environment variables.

    Args:
        monkeypatch: mokeypatch fixture
    """
    monkeypatch.setenv("LABBY_ENVIRONMENT_NAME", "aws")
    monkeypatch.setenv("LABBY_PROVIDER_NAME", "gns3-eu-server")
    monkeypatch.setenv("LABBY_PROVIDER_USER", "labops")
    monkeypatch.setenv("LABBY_PROVIDER_PASSWORD", "labops789")


def test_get_config_current_path():
    """Test getting the current config path."""
    assert get_config_current_path() == Path.cwd() / "labby.toml"


def test_get_config_base_path():
    """Test getting the base config path."""
    assert get_config_base_path() == Path.home() / ".config" / "labby" / "labby.toml"


def test_load_toml():
    """Test load of toml file."""
    toml_data = load_toml(Path(__file__).parent / "data" / "labby.toml")
    assert "main" in toml_data
    assert "environment" in toml_data
    assert toml_data["main"]["environment"] == "default"
    assert toml_data["environment"]["default"]["provider"] == "gns3-lab"
    assert (
        toml_data["environment"]["aws"]["providers"]["gns3-us-server"]["server_url"]
        == "http://gns3-us-east-server.aws:80"
    )


def test_save_toml(tmp_path):
    """Test saving TOML file.

    Args:
        tmp_path (_type_): Fixture for temporary path
    """
    toml_data = load_toml(Path(__file__).parent / "data" / "labby.toml")
    save_toml(tmp_path / "labby.toml", toml_data)
    new_toml_data = load_toml(tmp_path / "labby.toml")
    assert "main" in new_toml_data
    assert "environment" in new_toml_data
    assert new_toml_data["main"]["environment"] == "default"
    assert new_toml_data["environment"]["packet"]["provider"] == "gns3-main"
    assert (
        new_toml_data["environment"]["aws"]["providers"]["gns3-us-server"]["server_url"]
        == "http://gns3-us-east-server.aws:80"
    )


# def test_update_config_data():
#     config_file = Path(__file__).parent / "data" / "labby.toml"
#     new_data = config.update_config_data(config_file, "labby.environment", "packet")
#     assert "labby" in new_data
#     assert "environment" in new_data
#     assert new_data["labby"]["environment"] == "packet"


# def test_delete_config_data():
#     config_file = Path(__file__).parent / "data" / "labby.toml"
#     new_data = config.delete_config_data(config_file, "labby.environment")
#     assert "labby" in new_data
#     assert "environment" not in new_data["labby"]


@pytest.mark.skip(reason="needs to have deeper look")
def test_load_default_config():
    """Test load of default config."""
    load_config(Path(__file__).parent / "data" / "labby.toml")
    assert SETTINGS.environment.name == "default"
    assert SETTINGS.environment.provider.name == "gns3-lab"
    assert SETTINGS.debug is False
    assert SETTINGS.environment.provider.server_url == "http://gns3-lab:80"
    assert SETTINGS.environment.provider.user is None
    assert SETTINGS.environment.provider.password is None
    assert SETTINGS.environment.provider.verify_cert is False


@pytest.mark.skip(reason="needs to have deeper look")
def test_load_config_environment_passed_arg():
    """Test load of the config environment passed argument."""
    load_config(Path(__file__).parent / "data" / "labby.toml", environment_name="aws")
    assert SETTINGS.environment.name == "aws"
    assert SETTINGS.environment.provider.name == "gns3-us-server"
    assert SETTINGS.debug is False
    assert SETTINGS.environment.provider.server_url.scheme == "http"
    assert SETTINGS.environment.provider.server_url.port == "80"
    assert SETTINGS.environment.provider.server_url.host == "gns3-us-east-server.aws"
    assert SETTINGS.environment.provider.server_url.tld == "aws"
    assert SETTINGS.environment.provider.user == "netops"
    assert SETTINGS.environment.provider.password.get_secret_value() == "netops123"
    assert SETTINGS.environment.provider.verify_cert is True


@pytest.mark.skip(reason="needs to have deeper look")
def test_load_config_provider_passed_arg():
    """Test load of the config provider passed argument."""
    load_config(Path(__file__).parent / "data" / "labby.toml", environment_name="aws", provider_name="gns3-eu-server")
    assert SETTINGS.environment.name == "aws"
    assert SETTINGS.environment.provider.name == "gns3-eu-server"
    assert SETTINGS.debug is False
    assert SETTINGS.environment.provider.server_url.scheme == "http"
    assert SETTINGS.environment.provider.server_url.port == "8080"
    assert SETTINGS.environment.provider.server_url.host == "gns3-eu-east-server.awseu"
    assert SETTINGS.environment.provider.server_url.tld == "awseu"
    assert SETTINGS.environment.provider.user == "netops"
    assert SETTINGS.environment.provider.password.get_secret_value() == "netops123"
    assert SETTINGS.environment.provider.verify_cert is True


@pytest.mark.skip(reason="needs to have deeper look")
def test_load_config_environment_as_env_var(mock_env_vars):
    # pylint: disable=unused-argument
    # pylint: disable=redefined-outer-name
    """Test load of the config environment as environment variable.

    Args:
        mock_env_vars (_type_): Fixture for mocking ENVVARS
    """
    load_config(Path(__file__).parent / "data" / "labby_env_var.toml")
    assert SETTINGS.environment.name == "aws"
    assert SETTINGS.environment.provider.name == "gns3-eu-server"
    assert SETTINGS.debug is False
    assert SETTINGS.environment.provider.server_url.scheme == "http"
    assert SETTINGS.environment.provider.server_url.port == "8080"
    assert SETTINGS.environment.provider.server_url.host == "gns3-eu-east-server.awseu"
    assert SETTINGS.environment.provider.server_url.tld == "awseu"
    assert SETTINGS.environment.provider.user == "labops"
    assert SETTINGS.environment.provider.password.get_secret_value() == "labops789"
    assert SETTINGS.environment.provider.verify_cert is True


@pytest.mark.skip(reason="needs to have deeper look")
def test_error_unsoported_provider():
    """Test error for unsupported provider."""
    with pytest.raises(NotImplementedError, match="vrnetlab"):
        load_config(
            Path(__file__).parent / "data" / "labby.toml", environment_name="default", provider_name="container-lab"
        )


def test_load_invalid_toml():
    """Test invalid toml file."""
    with pytest.raises(TomlDecodeError, match="Found invalid character"):
        load_config(Path(__file__).parent / "data" / "invalid_labby.toml")


# @pytest.mark.parametrize(
#     ("node_spec,expected"),
#     [
#         (
#             dict(
#                 template="IOSv L2",
#                 nodes=["node-1", "node-2"],
#                 device_type="cisco_ios",
#                 mgmt_interface="Gi0/0",
#                 config_managed=True,
#             ),
#             dict(
#                 template="IOSv L2",
#                 nodes=["node-1", "node-2"],
#                 device_type="cisco_ios",
#                 mgmt_interface="Gi0/0",
#                 config_managed=True,
#             ),
#         ),
#         (
#             dict(
#                 template="vEOS",
#                 nodes=["node-3", "node-4"],
#                 device_type="arista_eos",
#                 mgmt_interface="",
#                 config_managed=True,
#             )
#         ),
#     ],
# )
# def test_project_nodes_spec():
#     pass
