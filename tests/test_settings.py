import pytest

from pathlib import Path
from toml import TomlDecodeError
from labby import config


@pytest.fixture()
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("LABBY_ENVIRONMENT_NAME", "aws")
    monkeypatch.setenv("LABBY_PROVIDER_NAME", "gns3-eu-server")
    monkeypatch.setenv("LABBY_PROVIDER_USER", "labops")
    monkeypatch.setenv("LABBY_PROVIDER_PASSWORD", "labops789")


def test_get_config_current_path():
    assert config.get_config_current_path() == Path.cwd() / "labby.toml"


def test_get_config_base_path():
    assert config.get_config_base_path() == Path.home() / ".config" / "labby" / "labby.toml"


def test_load_toml():
    toml_data = config.load_toml(Path(__file__).parent / "data" / "labby.toml")
    assert "main" in toml_data
    assert "environment" in toml_data
    assert toml_data["main"]["environment"] == "default"
    assert toml_data["environment"]["default"]["provider"] == "gns3-lab"
    assert (
        toml_data["environment"]["aws"]["providers"]["gns3-us-server"]["server_url"]
        == "http://gns3-us-east-server.aws:80"
    )


def test_save_toml(tmp_path):
    toml_data = config.load_toml(Path(__file__).parent / "data" / "labby.toml")
    config.save_toml(tmp_path / "labby.toml", toml_data)
    new_toml_data = config.load_toml(tmp_path / "labby.toml")
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


def test_load_default_config():
    config.load_config(Path(__file__).parent / "data" / "labby.toml")
    assert config.SETTINGS.environment.name == "default"
    assert config.SETTINGS.environment.provider.name == "gns3-lab"
    assert config.SETTINGS.debug is False
    assert config.SETTINGS.environment.provider.server_url == "http://gns3-lab:80"
    assert config.SETTINGS.environment.provider.user is None
    assert config.SETTINGS.environment.provider.password is None
    assert config.SETTINGS.environment.provider.verify_cert is False


def test_load_config_environment_passed_arg():
    config.load_config(Path(__file__).parent / "data" / "labby.toml", environment_name="aws")
    assert config.SETTINGS.environment.name == "aws"
    assert config.SETTINGS.environment.provider.name == "gns3-us-server"
    assert config.SETTINGS.debug is False
    assert config.SETTINGS.environment.provider.server_url.scheme == "http"
    assert config.SETTINGS.environment.provider.server_url.port == "80"
    assert config.SETTINGS.environment.provider.server_url.host == "gns3-us-east-server.aws"
    assert config.SETTINGS.environment.provider.server_url.tld == "aws"
    assert config.SETTINGS.environment.provider.user == "netops"
    assert config.SETTINGS.environment.provider.password.get_secret_value() == "netops123"
    assert config.SETTINGS.environment.provider.verify_cert is True


def test_load_config_provider_passed_arg():
    config.load_config(
        Path(__file__).parent / "data" / "labby.toml", environment_name="aws", provider_name="gns3-eu-server"
    )
    assert config.SETTINGS.environment.name == "aws"
    assert config.SETTINGS.environment.provider.name == "gns3-eu-server"
    assert config.SETTINGS.debug is False
    assert config.SETTINGS.environment.provider.server_url.scheme == "http"
    assert config.SETTINGS.environment.provider.server_url.port == "8080"
    assert config.SETTINGS.environment.provider.server_url.host == "gns3-eu-east-server.awseu"
    assert config.SETTINGS.environment.provider.server_url.tld == "awseu"
    assert config.SETTINGS.environment.provider.user == "netops"
    assert config.SETTINGS.environment.provider.password.get_secret_value() == "netops123"
    assert config.SETTINGS.environment.provider.verify_cert is True


def test_load_config_environment_as_env_var(mock_env_vars):
    config.load_config(Path(__file__).parent / "data" / "labby_env_var.toml")
    assert config.SETTINGS.environment.name == "aws"
    assert config.SETTINGS.environment.provider.name == "gns3-eu-server"
    assert config.SETTINGS.debug is False
    assert config.SETTINGS.environment.provider.server_url.scheme == "http"
    assert config.SETTINGS.environment.provider.server_url.port == "8080"
    assert config.SETTINGS.environment.provider.server_url.host == "gns3-eu-east-server.awseu"
    assert config.SETTINGS.environment.provider.server_url.tld == "awseu"
    assert config.SETTINGS.environment.provider.user == "labops"
    assert config.SETTINGS.environment.provider.password.get_secret_value() == "labops789"
    assert config.SETTINGS.environment.provider.verify_cert is True


def test_error_unsoported_provider():
    with pytest.raises(NotImplementedError, match="vrnetlab"):
        config.load_config(
            Path(__file__).parent / "data" / "labby.toml", environment_name="default", provider_name="container-lab"
        )


def test_load_invalid_toml():
    with pytest.raises(TomlDecodeError, match="Found invalid character"):
        config.load_config(Path(__file__).parent / "data" / "invalid_labby.toml")


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
