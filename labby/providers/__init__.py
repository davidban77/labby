from .gns3 import GNS3ProviderBuilder
from labby import utils
from labby import settings


class ObjectFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, key, builder):
        self._builders[key] = builder

    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


class NetworkLabProvider(ObjectFactory):
    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)


services = NetworkLabProvider()
services.register_builder("GNS3", GNS3ProviderBuilder())


def provider_setup(header_msg: str):
    provider = services.get(
            settings.SETTINGS.labby.provider.upper(),
            **settings.SETTINGS.get_provider_settings().dict(),
        )
    utils.provider_header(
        environment=settings.SETTINGS.labby.environment,
        provider=settings.SETTINGS.labby.provider,
        provider_version=provider.get_version(),
        msg=header_msg,
    )
    return provider
