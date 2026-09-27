"""Unit tests for the enterprise Compose generator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml

from devspeed.core.compose_generator import (
    ComposeGenerationError,
    ComposeGenerator,
    ConfigValidationError,
    GeneratedArtifacts,
    GeneratorSettings,
    OutputFileExistsError,
    PluginResolutionError,
    PortConflictError,
)
from devspeed.plugins.base import StackPlugin
from devspeed.plugins.registry import PluginRegistry


class InvalidYamlPlugin(StackPlugin):
    """Plugin used to verify malformed renderer output is rejected."""

    @property
    def name(self) -> str:
        """Return the test plugin identifier."""
        return "invalid-yaml"

    @property
    def description(self) -> str:
        """Return the test plugin description."""
        return "Invalid YAML test plugin"

    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return a minimal test configuration."""
        return {"project": project_name, "stack": self.name, "services": {"app": {}}}

    def compose_yaml(self, config: dict[str, Any]) -> str:
        """Return intentionally malformed YAML."""
        return "services: ["

    def env_file(self, config: dict[str, Any]) -> str:
        """Return a valid environment value."""
        return "VALUE=test\n"

    def post_up_hints(self, config: dict[str, Any]) -> list[str]:
        """Return no startup hints."""
        return []


class EmptyEnvPlugin(InvalidYamlPlugin):
    """Plugin used to verify empty environment output is rejected."""

    @property
    def name(self) -> str:
        """Return the empty environment test identifier."""
        return "empty-env"

    def compose_yaml(self, config: dict[str, Any]) -> str:
        """Return valid minimal Compose YAML."""
        return "services:\n  app:\n    image: test\n"

    def env_file(self, config: dict[str, Any]) -> str:
        """Return an invalid empty environment file."""
        return ""


class ComposeGeneratorTests(unittest.TestCase):
    """Exercise rendering, validation, conflicts, and persistence behavior."""

    def setUp(self) -> None:
        """Create a generator that does not depend on local machine ports."""
        self.settings = GeneratorSettings(check_host_ports=False, retries=2)
        self.generator = ComposeGenerator(settings=self.settings)

    def fastapi_config(self) -> dict[str, Any]:
        """Return a valid FastAPI configuration with non-default test ports."""
        return {
            "project": "test-project",
            "stack": "fastapi-postgres",
            "services": {
                "app": {"port": 18000, "python_version": "3.12"},
                "postgres": {
                    "port": 15432,
                    "db": "test_db",
                    "user": "tester",
                    "password": "secret",
                },
            },
        }

    def test_settings_accept_valid_values(self) -> None:
        """Accept explicitly configured operational settings."""
        settings = GeneratorSettings(check_host_ports=False, retries=1, retry_delay_seconds=0)
        self.assertEqual(settings.retries, 1)

    def test_settings_reject_zero_retries(self) -> None:
        """Reject settings that would perform no write attempts."""
        with self.assertRaises(ValueError):
            GeneratorSettings(retries=0)

    def test_settings_reject_negative_delay(self) -> None:
        """Reject negative retry delays."""
        with self.assertRaises(ValueError):
            GeneratorSettings(retry_delay_seconds=-1)

    def test_non_mapping_config_is_rejected(self) -> None:
        """Reject scalar configuration before any plugin is resolved."""
        with self.assertRaises(TypeError):
            self.generator.generate(None)  # type: ignore[arg-type]

    def test_missing_required_config_fields_are_reported(self) -> None:
        """Report missing project, stack, and services together."""
        with self.assertRaises(ConfigValidationError) as raised:
            self.generator.generate({})
        self.assertIn("project", str(raised.exception))
        self.assertIn("stack", str(raised.exception))
        self.assertIn("services", str(raised.exception))

    def test_invalid_project_name_is_rejected(self) -> None:
        """Reject unsafe project identifiers before rendering."""
        config = self.fastapi_config()
        config["project"] = "../escape"
        with self.assertRaises(ConfigValidationError):
            self.generator.generate(config)

    def test_invalid_stack_name_is_rejected(self) -> None:
        """Reject malformed stack identifiers before registry lookup."""
        config = self.fastapi_config()
        config["stack"] = "FastAPI Postgres"
        with self.assertRaises(ConfigValidationError):
            self.generator.generate(config)

    def test_empty_services_are_rejected(self) -> None:
        """Reject an empty service mapping."""
        config = self.fastapi_config()
        config["services"] = {}
        with self.assertRaises(ConfigValidationError):
            self.generator.generate(config)

    def test_non_mapping_service_is_rejected(self) -> None:
        """Reject service values that cannot contain settings."""
        config = self.fastapi_config()
        config["services"]["app"] = "not-a-mapping"
        with self.assertRaises(ConfigValidationError):
            self.generator.generate(config)

    def test_non_integer_port_is_rejected(self) -> None:
        """Reject string ports instead of silently coercing them."""
        config = self.fastapi_config()
        config["services"]["app"]["port"] = "18000"
        with self.assertRaises(ConfigValidationError):
            self.generator.generate(config)

    def test_out_of_range_port_is_rejected(self) -> None:
        """Reject ports outside the TCP host-port range."""
        config = self.fastapi_config()
        config["services"]["app"]["port"] = 70000
        with self.assertRaises(ConfigValidationError):
            self.generator.generate(config)

    def test_duplicate_ports_are_rejected(self) -> None:
        """Reject two services binding the same configured host port."""
        config = self.fastapi_config()
        config["services"]["postgres"]["port"] = 18000
        with self.assertRaises(PortConflictError):
            self.generator.generate(config)

    def test_unknown_stack_is_rejected(self) -> None:
        """Convert a registry lookup failure into a generator exception."""
        config = self.fastapi_config()
        config["stack"] = "unknown-stack"
        with self.assertRaises(PluginResolutionError):
            self.generator.generate(config)

    def test_compose_output_is_valid_yaml(self) -> None:
        """Render valid YAML for the selected FastAPI plugin."""
        artifacts = self.generator.generate(self.fastapi_config())
        document = yaml.safe_load(artifacts.compose_yaml)
        self.assertIn("services", document)
        self.assertIn("app", document["services"])

    def test_compose_output_contains_managed_network(self) -> None:
        """Add the shared DevSpeed network to generated Compose output."""
        artifacts = self.generator.generate(self.fastapi_config())
        document = yaml.safe_load(artifacts.compose_yaml)
        self.assertIn("devspeed_network", document["networks"])
        self.assertIn("devspeed_network", document["services"]["app"]["networks"])

    def test_compose_output_contains_restart_policy(self) -> None:
        """Add restart policies without overriding plugin-provided values."""
        artifacts = self.generator.generate(self.fastapi_config())
        document = yaml.safe_load(artifacts.compose_yaml)
        self.assertEqual(document["services"]["app"]["restart"], "unless-stopped")

    def test_environment_output_is_generated(self) -> None:
        """Return the plugin-generated host connection URL."""
        artifacts = self.generator.generate(self.fastapi_config())
        self.assertIn("localhost:15432", artifacts.env_file)
        self.assertIn("secret", artifacts.env_file)

    def test_host_port_checker_detects_conflict(self) -> None:
        """Raise a domain error when an injected host probe reports unavailable."""
        generator = ComposeGenerator(
            settings=GeneratorSettings(check_host_ports=True),
            port_checker=lambda port: False,
        )
        with self.assertRaises(PortConflictError):
            generator.generate(self.fastapi_config())

    def test_host_port_checker_exception_is_reported(self) -> None:
        """Translate probe failures into actionable port conflict details."""

        def failing_checker(port: int) -> bool:
            raise OSError("permission denied")

        generator = ComposeGenerator(
            settings=GeneratorSettings(check_host_ports=True),
            port_checker=failing_checker,
        )
        with self.assertRaises(PortConflictError) as raised:
            generator.generate(self.fastapi_config())
        self.assertIn("permission denied", str(raised.exception))

    def test_invalid_plugin_yaml_is_rejected(self) -> None:
        """Reject malformed YAML returned by an installed plugin."""
        registry = PluginRegistry()
        registry.register(InvalidYamlPlugin())
        generator = ComposeGenerator(registry=registry, settings=self.settings)
        config = {"project": "demo", "stack": "invalid-yaml", "services": {"app": {}}}
        with self.assertRaises(ComposeGenerationError):
            generator.generate(config)

    def test_empty_plugin_env_is_rejected(self) -> None:
        """Reject an empty environment file returned by a plugin."""
        registry = PluginRegistry()
        registry.register(EmptyEnvPlugin())
        generator = ComposeGenerator(registry=registry, settings=self.settings)
        config = {"project": "demo", "stack": "empty-env", "services": {"app": {}}}
        with self.assertRaises(ComposeGenerationError):
            generator.generate(config)

    def test_write_creates_two_output_files(self) -> None:
        """Persist Compose and environment outputs in a clean directory."""
        artifacts = self.generator.generate(self.fastapi_config())
        with tempfile.TemporaryDirectory() as directory:
            result = self.generator.write(artifacts, directory)
            self.assertFalse(result.replaced)
            self.assertTrue(result.compose_path.exists())
            self.assertTrue(result.env_path.exists())

    def test_write_refuses_existing_outputs_without_force(self) -> None:
        """Protect existing files unless replacement is explicit."""
        artifacts = self.generator.generate(self.fastapi_config())
        with tempfile.TemporaryDirectory() as directory:
            self.generator.write(artifacts, directory)
            with self.assertRaises(OutputFileExistsError):
                self.generator.write(artifacts, directory)

    def test_write_force_replaces_existing_outputs(self) -> None:
        """Replace both outputs when force is explicitly enabled."""
        artifacts = self.generator.generate(self.fastapi_config())
        replacement = GeneratedArtifacts(
            project=artifacts.project,
            stack=artifacts.stack,
            compose_yaml=artifacts.compose_yaml + "# replacement\n",
            env_file=artifacts.env_file + "REPLACED=true\n",
            host_ports=artifacts.host_ports,
        )
        with tempfile.TemporaryDirectory() as directory:
            self.generator.write(artifacts, directory)
            result = self.generator.write(replacement, directory, force=True)
            self.assertTrue(result.replaced)
            self.assertIn("REPLACED=true", result.env_path.read_text(encoding="utf-8"))

    def test_write_requires_existing_directory(self) -> None:
        """Reject a missing output directory instead of creating surprises."""
        artifacts = self.generator.generate(self.fastapi_config())
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaises(FileNotFoundError):
                self.generator.write(artifacts, missing)

    def test_write_rejects_file_as_output_directory(self) -> None:
        """Reject an output path that points to a regular file."""
        artifacts = self.generator.generate(self.fastapi_config())
        with tempfile.NamedTemporaryFile() as output, self.assertRaises(NotADirectoryError):
            self.generator.write(artifacts, output.name)

    def test_generated_artifacts_reject_empty_compose(self) -> None:
        """Enforce artifact invariants even when constructed directly."""
        with self.assertRaises(ValueError):
            GeneratedArtifacts("demo", "stack", "", "", ())

    def test_generated_artifacts_reject_non_tuple_ports(self) -> None:
        """Reject mutable host-port collections in immutable artifacts."""
        with self.assertRaises(TypeError):
            GeneratedArtifacts("demo", "stack", "services: {}", "", [])  # type: ignore[arg-type]

    def test_generation_does_not_write_files(self) -> None:
        """Confirm rendering remains side-effect free."""
        with tempfile.TemporaryDirectory() as directory:
            with patch("pathlib.Path.cwd", return_value=Path(directory)):
                self.generator.generate(self.fastapi_config())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
