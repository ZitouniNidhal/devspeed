"""Stable public API for DevSpeed stack plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

PLUGIN_API_VERSION = "1.0"


class PluginError(RuntimeError):
    """Raised when a plugin violates the DevSpeed plugin contract."""


class StackPlugin(ABC):
    """Base class implemented by every DevSpeed stack plugin.

    A plugin is a pure renderer and metadata provider. It must not perform
    filesystem or Docker operations while it is being discovered. The CLI
    owns those side effects after it has loaded and validated a plugin.

    Subclasses should keep ``name`` stable because it is persisted in
    ``devspeed.yaml``. The major component of ``api_version`` must match
    :data:`PLUGIN_API_VERSION`.
    """

    api_version: str = PLUGIN_API_VERSION

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable stack identifier used in ``devspeed.yaml``."""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a concise human-readable description for ``devspeed list``."""
        raise NotImplementedError

    @abstractmethod
    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return a complete starter configuration for ``project_name``."""
        raise NotImplementedError

    @abstractmethod
    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render a Docker Compose YAML document from validated configuration."""
        raise NotImplementedError

    @abstractmethod
    def env_file(self, config: Mapping[str, Any]) -> str:
        """Render host-side environment variables for the generated env file."""
        raise NotImplementedError

    @abstractmethod
    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return useful notes shown after the stack starts successfully."""
        raise NotImplementedError

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        """Return optional starter files keyed by project-relative path."""
        return {}

    def validate(self) -> None:
        """Validate plugin metadata before adding the plugin to a registry."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise PluginError("plugin name must be a non-empty string")
        if not isinstance(self.description, str) or not self.description.strip():
            raise PluginError(f"plugin '{self.name}' needs a description")
        if not _is_compatible_api(self.api_version):
            raise PluginError(
                f"plugin '{self.name}' uses API {self.api_version}; "
                f"DevSpeed supports {PLUGIN_API_VERSION}"
            )


def _is_compatible_api(version: str) -> bool:
    """Return whether a plugin API version shares DevSpeed's major version."""
    if not isinstance(version, str):
        return False
    return version.split(".", 1)[0] == PLUGIN_API_VERSION.split(".", 1)[0]
