"""Built-in stack compatibility exports and the public plugin registry."""

from devspeed.plugin import PluginRegistry, StackPlugin, builtin_registry

_REGISTRY = builtin_registry()

# Kept as a snapshot for callers that used the old STACKS mapping.
STACKS: dict[str, StackPlugin] = {plugin.name: plugin for plugin in _REGISTRY.all()}


def get_registry() -> PluginRegistry:
    """Return the process registry containing built-ins and installed plugins."""
    return _REGISTRY


def get_stack(name: str) -> StackPlugin:
    """Return a stack plugin by its stable configuration name."""
    return _REGISTRY.get(name)


def list_stacks() -> list[tuple[str, str]]:
    """Return stack names and descriptions for the CLI and integrations."""
    return [(plugin.name, plugin.description) for plugin in _REGISTRY.all()]


__all__ = [
    "PluginRegistry",
    "STACKS",
    "StackPlugin",
    "get_registry",
    "get_stack",
    "list_stacks",
]
