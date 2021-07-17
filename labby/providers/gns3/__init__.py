from __future__ import annotations
from .provider import GNS3Provider
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from labby.config import ProviderSettings


class GNS3ProviderBuilder:
    def __init__(self):
        self._instance = None

    def __call__(
        self,
        settings: ProviderSettings,
        **_ignored,
    ):
        if not settings.server_url:
            raise ValueError(f"Server URL for provider {settings.name} has not been set")
        if not self._instance:
            self._instance = GNS3Provider(
                name=settings.name,
                kind=settings.kind,
                server_url=settings.server_url,
                user=settings.user,
                password=settings.password.get_secret_value() if settings.password else None,
                verify_cert=settings.verify_cert if settings.verify_cert is not None else False,
            )
        return self._instance
