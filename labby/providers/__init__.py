from .gns3 import GNS3ProviderBuilder


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


# Usage will be
# import labby.providers as lab_provider
# config = dict(gns3_client_key="algo", gns3_client_secret="aqui")
# gns3 = lab_providers.services.get("GNS3", **config)
