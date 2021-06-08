import typer
from .gns3 import GNS3ProviderBuilder

# from labby import config
# from labby import utils

# from labby import settings
# from labby.models import ProviderGeneral, ProviderDocker
from labby.config import ProviderSettings
from labby.models import LabbyProvider
from labby import utils


class ObjectFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, key, builder):
        self._builders[key] = builder

    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(f"Provider not found {key}")
        return builder(**kwargs)


class NetworkLabProvider(ObjectFactory):
    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)


services = NetworkLabProvider()


def register_service(provider_name: str, provider_type: str):
    if provider_type == "gns3":
        services.register_builder(f"{provider_name}", GNS3ProviderBuilder())
    else:
        raise NotImplementedError(provider_type)


def get_provider(provider_name: str, provider_settings: ProviderSettings) -> LabbyProvider:
    provider = services.get(
        provider_name,
        settings=provider_settings,
    )
    # if header_msg is not None:
    #     utils.provider_header(
    #         environment=settings.SETTINGS.labby.environment,
    #         provider=settings.SETTINGS.labby.provider,
    #         provider_version=provider.get_version(),
    #         msg=header_msg,
    #     )
    return provider


def get_provider_instance() -> LabbyProvider:
    # Importing at command runtime - not import load time
    from labby.config import SETTINGS
    if not SETTINGS:
        utils.console.log("No config settings applied. Please check configuration file labby.toml", style="error")
        raise typer.Exit(1)
    return get_provider(
        provider_name=SETTINGS.environment.provider.name, provider_settings=SETTINGS.environment.provider
    )