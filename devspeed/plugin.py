"""Public plugin API and discovery for DevSpeed stack extensions."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from html.parser import HTMLParser
from importlib import import_module
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Callable

PLUGIN_API_VERSION = "1.0"
ENTRY_POINT_GROUP = "devspeed.stacks"
PYPI_SIMPLE_INDEX = "https://pypi.org/simple/"


class StackPlugin(ABC):
    """Stable interface implemented by every DevSpeed stack plugin.

    Plugin packages should export an instance named ``plugin`` through the
    ``devspeed.stacks`` entry-point group. The API version uses major/minor
    compatibility: a plugin must have the same major API version as DevSpeed.
    """

    api_version = PLUGIN_API_VERSION

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable config identifier, for example ``flask-postgres``."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a short human-readable description."""

    @abstractmethod
    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return a serializable starter configuration."""

    @abstractmethod
    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render the Docker Compose document."""

    @abstractmethod
    def env_file(self, config: Mapping[str, Any]) -> str:
        """Render host environment values for the generated environment file."""

    @abstractmethod
    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return actionable notes shown after the environment starts."""

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        """Return optional starter files; plugins may override this hook."""
        return {}

    def validate(self) -> None:
        """Validate the public metadata before registration."""
        if not self.name or not isinstance(self.name, str):
            raise PluginError("plugin name must be a non-empty string")
        if not self.description or not isinstance(self.description, str):
            raise PluginError(f"plugin '{self.name}' needs a description")
        if not _compatible_api_version(self.api_version):
            raise PluginError(
                f"plugin '{self.name}' uses API {self.api_version}; "
                f"DevSpeed supports {PLUGIN_API_VERSION}"
            )


@dataclass(frozen=True)
class ModuleStackPlugin(StackPlugin):
    """Compatibility adapter for the original function-based stack modules."""

    module: Any

    @property
    def name(self) -> str:
        return self.module.NAME

    @property
    def description(self) -> str:
        return self.module.DESCRIPTION

    def default_config(self, project_name: str) -> dict[str, Any]:
        return self.module.default_config(project_name)

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        return self.module.compose_yaml(config)

    def env_file(self, config: Mapping[str, Any]) -> str:
        return self.module.env_file(config)

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        return self.module.post_up_hints(config)

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        return self.module.starter_files(config)


class PluginError(RuntimeError):
    """Raised when a plugin cannot be loaded or does not satisfy the API."""


class _SimpleIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.packages: list[str] = []

    def handle_data(self, data: str) -> None:
        package = data.strip()
        if package.startswith("devspeed-stack-"):
            self.packages.append(package)


def _compatible_api_version(version: str) -> bool:
    try:
        return version.split(".", 1)[0] == PLUGIN_API_VERSION.split(".", 1)[0]
    except AttributeError:
        return False


def _coerce_plugin(value: Any) -> StackPlugin:
    if isinstance(value, StackPlugin):
        plugin = value
    elif isinstance(value, type) and issubclass(value, StackPlugin):
        plugin = value()
    elif callable(value):
        plugin = value()
        if not isinstance(plugin, StackPlugin):
            raise PluginError("entry point factory did not return a StackPlugin")
    else:
        raise PluginError("entry point must expose a StackPlugin or factory")
    plugin.validate()
    return plugin


class PluginRegistry:
    """Registry combining built-in adapters and installed third-party plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, StackPlugin] = {}
        self.errors: list[str] = []

    def register(self, plugin: StackPlugin, *, replace: bool = False) -> StackPlugin:
        plugin.validate()
        if plugin.name in self._plugins and not replace:
            raise PluginError(f"duplicate stack plugin name: {plugin.name}")
        self._plugins[plugin.name] = plugin
        return plugin

    def discover(self) -> "PluginRegistry":
        """Load installed entry points, retaining usable plugins if one fails."""
        for point in _entry_points():
            try:
                self.register(_coerce_plugin(point.load()))
            except (PluginError, ImportError, AttributeError, TypeError) as error:
                self.errors.append(f"{point.name}: {error}")
        return self

    def get(self, name: str) -> StackPlugin:
        if name not in self._plugins:
            available = ", ".join(sorted(self._plugins)) or "none"
            raise KeyError(f"Unknown stack '{name}'. Available stacks: {available}")
        return self._plugins[name]

    def all(self) -> list[StackPlugin]:
        return list(self._plugins.values())


def _entry_points() -> list[EntryPoint]:
    discovered = entry_points()
    if hasattr(discovered, "select"):
        return list(discovered.select(group=ENTRY_POINT_GROUP))
    return list(discovered.get(ENTRY_POINT_GROUP, []))


def builtin_registry() -> PluginRegistry:
    """Build the default registry without requiring package installation metadata."""
    modules = ("node_postgres_redis", "fastapi_postgres", "django_postgres", "flask_postgres")
    registry = PluginRegistry()
    for module_name in modules:
        module = import_module(f"devspeed.stacks.{module_name}")
        registry.register(ModuleStackPlugin(module))
    return registry.discover()


def discover_pypi_stack_packages(timeout: float = 5.0) -> list[str]:
    """Return published package names following the ``devspeed-stack-*`` convention."""
    request = urllib.request.Request(PYPI_SIMPLE_INDEX, headers={"User-Agent": "devspeed"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parser = _SimpleIndexParser()
        parser.feed(response.read().decode("utf-8"))
    return sorted(set(parser.packages))


def pypi_package_metadata(package_name: str, timeout: float = 5.0) -> dict[str, Any]:
    """Fetch metadata for a named stack package without installing or executing it."""
    encoded_name = urllib.parse.quote(package_name)
    request = urllib.request.Request(
        f"https://pypi.org/pypi/{encoded_name}/json", headers={"User-Agent": "devspeed"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["info"]


PluginFactory = Callable[[], StackPlugin]
