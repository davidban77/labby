"""Labby Providers setup."""
from .gns3 import GNS3ProviderBuilder


class ObjectFactory:
    """Basic Object Factory class pattern."""

    def __init__(self):
        """Object Factory initialization."""
        self._builders = {}

    def register_builder(self, key, builder):
        """Register builder."""
        self._builders[key] = builder

    def create(self, key, **kwargs):
        """Create Provider record.

        Args:
            key: Key to access provider cache

        Raises:
            ValueError: if no provider was found
        """
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(f"Provider not found {key}")
        return builder(**kwargs)


class NetworkLabProvider(ObjectFactory):
    """Network Lab Provider Object Factory."""

    def get(self, service_id: str, **kwargs):
        """Creates a record of a service for network lab providers.

        Args:
            service_id (str): Service ID key
        """
        return self.create(service_id, **kwargs)


services = NetworkLabProvider()


def register_service(provider_name: str, provider_type: str):
    """Registers an specific service based on provider name and type.

    Args:
        provider_name (str): Provider Name
        provider_type (str): Provider Type

    Raises:
        NotImplementedError: raised when provider is not implemented
    """
    if provider_type == "gns3":
        services.register_builder(f"{provider_name}", GNS3ProviderBuilder())
    else:
        raise NotImplementedError(provider_type)
