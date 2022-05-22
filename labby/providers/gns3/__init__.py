"""Labby GNS3 Provider Setup."""
from __future__ import annotations
from typing import TYPE_CHECKING

from .provider import GNS3Provider

if TYPE_CHECKING:
    from labby.config import ProviderSettings


class GNS3ProviderBuilder:
    # pylint: disable=too-few-public-methods
    """Builder of GNS3 Providers."""

    def __init__(self):
        """GNS3 Provider Builder instantiation."""
        self._instance = None

    def __call__(
        self,
        settings: ProviderSettings,
        **_ignored,
    ) -> GNS3Provider:
        """GNS3 Provider Builder instantiation.

        Args:
            settings (ProviderSettings): General GNS3 Provider Settings

        Raises:
            ValueError: if the server URL is not set.

        Returns:
            GNS3Provider: GNS3 Provider instance.
        """
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
