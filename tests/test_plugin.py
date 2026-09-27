import unittest
from typing import Any
from unittest.mock import patch

from devspeed.plugin import (
    ENTRY_POINT_GROUP,
    PLUGIN_API_VERSION,
    PluginError,
    PluginRegistry,
    StackPlugin,
    builtin_registry,
)


class ExamplePlugin(StackPlugin):
    name = "example"
    description = "Example third-party stack"
    api_version = PLUGIN_API_VERSION

    def default_config(self, project_name: str) -> dict[str, Any]:
        return {"project": project_name, "stack": self.name, "services": {}}

    def compose_yaml(self, config: dict[str, Any]) -> str:
        return "services: {}"

    def env_file(self, config: dict[str, Any]) -> str:
        return ""

    def post_up_hints(self, config: dict[str, Any]) -> list[str]:
        return []


class PluginTests(unittest.TestCase):
    def test_builtin_registry_exposes_stack_plugins(self):
        registry = builtin_registry()
        self.assertEqual(registry.get("fastapi-postgres").name, "fastapi-postgres")
        self.assertEqual(registry.errors, [])

    def test_registry_discovers_entry_point_plugin(self):
        point = type("Point", (), {"name": "example", "load": lambda _self: ExamplePlugin()})()
        with patch("devspeed.plugins.registry._entry_points", return_value=[point]):
            registry = PluginRegistry().discover()
        self.assertEqual(registry.get("example").description, "Example third-party stack")

    def test_registry_rejects_incompatible_api(self):
        plugin = ExamplePlugin()
        plugin.api_version = "2.0"
        with self.assertRaises(PluginError):
            PluginRegistry().register(plugin)

    def test_entry_point_group_is_stable(self):
        self.assertEqual(ENTRY_POINT_GROUP, "devspeed.stacks")

    def test_registry_rejects_duplicate_names(self):
        registry = PluginRegistry()
        registry.register(ExamplePlugin())
        with self.assertRaises(PluginError):
            registry.register(ExamplePlugin())

    def test_registry_records_broken_optional_entry_point(self):
        point = type(
            "Point",
            (),
            {
                "name": "broken",
                "load": lambda _self: (_ for _ in ()).throw(ImportError("missing dependency")),
            },
        )()
        with patch("devspeed.plugins.registry._entry_points", return_value=[point]):
            registry = PluginRegistry().discover()
        self.assertEqual(registry.all(), [])
        self.assertIn("broken: missing dependency", registry.errors)

    def test_builtin_stack_contracts(self):
        from devspeed.plugins.registry import builtin_registry
        registry = builtin_registry()
        for plugin in registry.all():
            with self.subTest(plugin=plugin.name):
                config = plugin.default_config("contract-test")
                self.assertIsInstance(config, dict)
                self.assertTrue(plugin.compose_yaml(config))
                self.assertTrue(plugin.env_file(config))
                self.assertIsInstance(plugin.post_up_hints(config), list)


if __name__ == "__main__":
    unittest.main()
