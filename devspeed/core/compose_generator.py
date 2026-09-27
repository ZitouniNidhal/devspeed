"""Validated Docker Compose and environment generation for DevSpeed.

This module deliberately separates rendering from persistence. ``ComposeGenerator.generate``
validates configuration, resolves a :class:`~devspeed.plugins.base.StackPlugin`, renders
its outputs, validates the resulting YAML, and returns strings without touching the
filesystem. ``ComposeGenerator.write`` is the explicit persistence operation and uses
atomic replacement, a process-local lock, retries, and an explicit ``force`` flag.
"""

from __future__ import annotations

import logging
import os
import re
import socket
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import yaml

from devspeed.plugins.base import PluginError, StackPlugin
from devspeed.plugins.registry import PluginRegistry
from devspeed.stacks import get_registry

LOGGER = logging.getLogger(__name__)
DEFAULT_COMPOSE_FILENAME = "docker-compose.devspeed.yml"
DEFAULT_ENV_FILENAME = ".env.devspeed"
_PROJECT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,62}$")
_STACK_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


class ComposeGenerationError(RuntimeError):
    """Base exception for configuration, rendering, and output failures."""


class ConfigValidationError(ComposeGenerationError, ValueError):
    """Raised when a configuration cannot safely be rendered."""

    def __init__(self, message: str, errors: Optional[Sequence[str]] = None) -> None:  # noqa: UP045
        """Create a validation error with optional field-level diagnostics.

        Args:
            message: High-level explanation suitable for a CLI error message.
            errors: Individual validation messages, if available.

        Returns:
            None.

        Raises:
            TypeError: If ``message`` or an item in ``errors`` is not text.

        Examples:
            >>> str(ConfigValidationError("invalid", ["project is required"]))
            'invalid: project is required'
        """
        if not isinstance(message, str) or not message.strip():
            raise TypeError("message must be a non-empty string")
        normalized = [] if errors is None else list(errors)
        if any(not isinstance(error, str) or not error.strip() for error in normalized):
            raise TypeError("errors must contain only non-empty strings")
        self.errors = tuple(normalized)
        suffix = "; ".join(self.errors)
        super().__init__(f"{message}: {suffix}" if suffix else message)


class PluginResolutionError(ComposeGenerationError):
    """Raised when the configured stack plugin cannot be found or is invalid."""


class PortConflictError(ComposeGenerationError):
    """Raised when configured host ports conflict with one another or the host."""

    def __init__(self, conflicts: Sequence[str]) -> None:
        """Create a port conflict error.

        Args:
            conflicts: Human-readable conflict descriptions.

        Returns:
            None.

        Raises:
            ValueError: If no conflict descriptions are supplied.
            TypeError: If a conflict description is not text.

        Examples:
            >>> str(PortConflictError(["app uses port 8000 twice"]))
            'Port conflicts detected: app uses port 8000 twice'
        """
        values = list(conflicts)
        if not values or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("conflicts must contain at least one non-empty string")
        self.conflicts = tuple(values)
        super().__init__(f"Port conflicts detected: {'; '.join(values)}")


class OutputFileExistsError(ComposeGenerationError, FileExistsError):
    """Raised when output files exist and replacement was not explicitly enabled."""

    def __init__(self, paths: Sequence[Path]) -> None:
        """Create an output collision error.

        Args:
            paths: Existing output paths that would be replaced.

        Returns:
            None.

        Raises:
            ValueError: If ``paths`` is empty.

        Examples:
            >>> str(OutputFileExistsError([Path(".env.devspeed")]))
            "Output files already exist: .env.devspeed; pass force=True to replace them"
        """
        existing = [Path(path) for path in paths]
        if not existing:
            raise ValueError("paths must contain at least one path")
        self.paths = tuple(existing)
        formatted = ", ".join(str(path) for path in existing)
        super().__init__(
            f"Output files already exist: {formatted}; pass force=True to replace them"
        )


class FileWriteError(ComposeGenerationError, OSError):
    """Raised when generated files cannot be persisted after retries."""


PortChecker = Callable[[int], bool]
Clock = Callable[[], float]


@dataclass(frozen=True)
class GeneratorSettings:
    """Operational controls for validation, host probing, and atomic writes.

    Args:
        check_host_ports: Probe host sockets in addition to checking duplicate config ports.
        retries: Number of attempts for retryable filesystem operations.
        retry_delay_seconds: Delay between filesystem attempts.
        operation_timeout_seconds: Maximum time allowed for one filesystem operation.
        check_compose_yaml: Validate the plugin output with PyYAML.
        inject_network: Add a managed network to every rendered Compose service.
        inject_restart_policy: Add ``unless-stopped`` where the plugin omitted one.

    Returns:
        A validated immutable settings object.

    Raises:
        ValueError: If numeric values are outside safe operational ranges.
        TypeError: If a setting has the wrong type.

    Examples:
        >>> GeneratorSettings(check_host_ports=False, retries=1).retries
        1
    """

    check_host_ports: bool = True
    retries: int = 3
    retry_delay_seconds: float = 0.05
    operation_timeout_seconds: float = 10.0
    check_compose_yaml: bool = True
    inject_network: bool = True
    inject_restart_policy: bool = True

    def __post_init__(self) -> None:
        """Validate settings once so generation can rely on their invariants.

        Raises:
            TypeError: If a setting is not the declared primitive type.
            ValueError: If retries, delays, or timeout are unsafe.
        """
        for name in (
            "check_host_ports",
            "check_compose_yaml",
            "inject_network",
            "inject_restart_policy",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a bool")
        if not isinstance(self.retries, int) or isinstance(self.retries, bool):
            raise TypeError("retries must be an integer")
        if self.retries < 1 or self.retries > 10:
            raise ValueError("retries must be between 1 and 10")
        for name in ("retry_delay_seconds", "operation_timeout_seconds"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be numeric")
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.operation_timeout_seconds == 0:
            raise ValueError("operation_timeout_seconds must be greater than zero")


@dataclass(frozen=True)
class GeneratedArtifacts:
    """Immutable rendered outputs returned by :meth:`ComposeGenerator.generate`.

    Args:
        project: Validated project name.
        stack: Validated stack name.
        compose_yaml: Complete Docker Compose YAML text.
        env_file: Complete host environment file text.
        host_ports: Unique host ports referenced by the configuration.

    Returns:
        A reusable artifact value that can be written later.

    Raises:
        TypeError: If values have incorrect types.
        ValueError: If required text fields are empty.

    Examples:
        >>> GeneratedArtifacts("demo", "fastapi-postgres", "services: {}", "", ()).stack
        'fastapi-postgres'
    """

    project: str
    stack: str
    compose_yaml: str
    env_file: str
    host_ports: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Enforce artifact invariants before an artifact can be persisted.

        Raises:
            TypeError: If an artifact field has an invalid type.
            ValueError: If identifiers or Compose content are empty.
        """
        for name in ("project", "stack", "compose_yaml", "env_file"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} must be a string")
        if not self.project.strip() or not self.stack.strip() or not self.compose_yaml.strip():
            raise ValueError("project, stack, and compose_yaml must be non-empty")
        if not isinstance(self.host_ports, tuple):
            raise TypeError("host_ports must be a tuple")
        if any(not isinstance(port, int) or isinstance(port, bool) for port in self.host_ports):
            raise TypeError("host_ports must contain integers")


@dataclass(frozen=True)
class WriteResult:
    """Paths written by :meth:`ComposeGenerator.write`.

    Args:
        compose_path: Absolute or caller-provided path of the Compose output.
        env_path: Absolute or caller-provided path of the environment output.
        replaced: Whether existing files were intentionally replaced.

    Returns:
        A result object for CLI reporting and audit logging.

    Raises:
        TypeError: If paths are not ``Path`` objects.

    Examples:
        >>> WriteResult(Path("compose.yml"), Path(".env"), False).replaced
        False
    """

    compose_path: Path
    env_path: Path
    replaced: bool

    def __post_init__(self) -> None:
        """Validate path and replacement metadata."""
        if not isinstance(self.compose_path, Path) or not isinstance(self.env_path, Path):
            raise TypeError("compose_path and env_path must be pathlib.Path instances")
        if not isinstance(self.replaced, bool):
            raise TypeError("replaced must be a bool")


class ComposeGenerator:
    """Generate and safely persist stack-specific Compose and env outputs.

    Args:
        registry: Plugin registry used to resolve configured stack names.
        settings: Validation and persistence behavior controls.
        port_checker: Optional injectable host-port probe used by tests and integrations.
        clock: Optional monotonic clock used for deterministic timeout tests.

    Returns:
        A generator instance.

    Raises:
        TypeError: If dependencies are not the expected types.
        ValueError: If settings are invalid.

    Examples:
        >>> generator = ComposeGenerator(settings=GeneratorSettings(check_host_ports=False))
        >>> artifacts = generator.generate({"project": "demo", "stack": "fastapi-postgres", "services": {"app": {"port": 8000}, "postgres": {"port": 5432}}})
        >>> artifacts.stack
        'fastapi-postgres'
    """

    _write_lock = threading.RLock()

    def __init__(
        self,
        registry: Optional[PluginRegistry] = None,  # noqa: UP045
        settings: Optional[GeneratorSettings] = None,  # noqa: UP045
        port_checker: Optional[PortChecker] = None,  # noqa: UP045
        clock: Optional[Clock] = None,  # noqa: UP045
    ) -> None:
        """Initialize a generator with injectable enterprise-safe dependencies.

        Args:
            registry: Registry used for stack resolution; defaults to the application registry.
            settings: Operational controls; defaults to :class:`GeneratorSettings`.
            port_checker: Function returning ``True`` when a host port is available.
            clock: Monotonic clock used for filesystem operation deadlines.

        Returns:
            None.

        Raises:
            TypeError: If an injected dependency is not callable or correctly typed.
            ValueError: If supplied settings fail validation.
        """
        if registry is not None and not isinstance(registry, PluginRegistry):
            raise TypeError("registry must be a PluginRegistry or None")
        if settings is not None and not isinstance(settings, GeneratorSettings):
            raise TypeError("settings must be a GeneratorSettings or None")
        if port_checker is not None and not callable(port_checker):
            raise TypeError("port_checker must be callable or None")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable or None")
        self.registry = registry or get_registry()
        self.settings = settings or GeneratorSettings()
        self.port_checker = port_checker or self._default_port_checker
        self.clock = clock or time.monotonic
        LOGGER.debug(
            "Initialized ComposeGenerator settings=%s registry_plugins=%s",
            self.settings,
            len(self.registry.all()),
        )

    def generate(self, config: Mapping[str, Any]) -> GeneratedArtifacts:
        """Validate configuration and render complete outputs without writing files.

        Args:
            config: Mapping containing ``project``, ``stack``, and ``services``.

        Returns:
            Rendered Compose and environment artifacts.

        Raises:
            ConfigValidationError: If required fields or service settings are invalid.
            PluginResolutionError: If the configured stack cannot be resolved.
            PortConflictError: If configured or host ports conflict.
            ComposeGenerationError: If a plugin renders invalid output.

        Examples:
            >>> generator = ComposeGenerator(settings=GeneratorSettings(check_host_ports=False))
            >>> output = generator.generate({"project": "demo", "stack": "fastapi-postgres", "services": {"app": {"port": 8000}, "postgres": {"port": 5432}}})
            >>> "services:" in output.compose_yaml
            True
        """
        LOGGER.info("Generating DevSpeed artifacts")
        normalized = self.validate_config(config)
        plugin = self._resolve_plugin(normalized["stack"])
        ports = self._validate_ports(normalized["services"])
        self._check_host_ports(ports)
        try:
            compose_text = plugin.compose_yaml(normalized)
            env_text = plugin.env_file(normalized)
        except Exception as error:
            LOGGER.exception("Stack plugin %s failed while rendering", plugin.name)
            raise ComposeGenerationError(
                f"stack plugin '{plugin.name}' failed to render: {error}"
            ) from error
        compose_text = self._normalize_compose(compose_text, plugin.name)
        if not isinstance(env_text, str) or not env_text.strip():
            raise ComposeGenerationError(f"stack plugin '{plugin.name}' returned an empty env file")
        artifacts = GeneratedArtifacts(
            project=normalized["project"],
            stack=plugin.name,
            compose_yaml=compose_text,
            env_file=env_text,
            host_ports=tuple(sorted(ports)),
        )
        LOGGER.info(
            "Generated stack=%s project=%s ports=%s", artifacts.stack, artifacts.project, ports
        )
        return artifacts

    def validate_config(self, config: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and copy the configuration before plugin rendering.

        Args:
            config: Candidate YAML mapping.

        Returns:
            A shallow normalized dictionary safe to pass to a plugin.

        Raises:
            ConfigValidationError: If the value is malformed or missing required data.
            TypeError: If ``config`` is not a mapping.

        Examples:
            >>> generator = ComposeGenerator(settings=GeneratorSettings(check_host_ports=False))
            >>> value = generator.validate_config({"project": "demo", "stack": "fastapi-postgres", "services": {"app": {}, "postgres": {}}})
            >>> value["project"]
            'demo'
        """
        if not isinstance(config, Mapping):
            raise TypeError("config must be a mapping")
        errors: list[str] = []
        project = config.get("project")
        stack = config.get("stack")
        services = config.get("services")
        if not isinstance(project, str) or not _PROJECT_PATTERN.fullmatch(project):
            errors.append(
                "project must contain 1-63 letters, numbers, '.', '_' or '-' and start alphanumerically"
            )
        if not isinstance(stack, str) or not _STACK_PATTERN.fullmatch(stack):
            errors.append(
                "stack must be a lowercase identifier containing letters, numbers, and hyphens"
            )
        if not isinstance(services, Mapping) or not services:
            errors.append("services must be a non-empty mapping")
        if errors:
            LOGGER.warning("Configuration rejected before plugin resolution: %s", errors)
            raise ConfigValidationError("invalid DevSpeed configuration", errors)
        validated_services = services
        if not isinstance(validated_services, Mapping):
            raise ConfigValidationError(
                "invalid DevSpeed configuration", ["services must be a mapping"]
            )
        copied = dict(config)
        copied["services"] = {str(key): value for key, value in validated_services.items()}
        for service_name, service in copied["services"].items():
            if not service_name or not isinstance(service, Mapping):
                errors.append(f"services.{service_name} must be a mapping")
                continue
            if "port" in service:
                try:
                    self._validate_port(service_name, service["port"])
                except ConfigValidationError as error:
                    errors.extend(error.errors or [str(error)])
        if errors:
            raise ConfigValidationError("invalid DevSpeed configuration", errors)
        return copied

    def write(
        self,
        artifacts: GeneratedArtifacts,
        output_dir: Union[str, os.PathLike[str], Path] = ".",  # noqa: UP007
        *,
        force: bool = False,
    ) -> WriteResult:
        """Atomically write Compose and env outputs to ``output_dir``.

        Args:
            artifacts: Previously generated artifacts.
            output_dir: Existing or creatable directory for output files.
            force: Replace existing files only when explicitly true.

        Returns:
            Paths written and whether replacement occurred.

        Raises:
            TypeError: If arguments have invalid types.
            FileNotFoundError: If ``output_dir`` does not exist and cannot be created.
            OutputFileExistsError: If files exist and ``force`` is false.
            FileWriteError: If atomic writes fail after retries.
            PermissionError: If the process cannot access the output directory.

        Examples:
            >>> generator = ComposeGenerator(settings=GeneratorSettings(check_host_ports=False))
            >>> artifacts = generator.generate({"project": "demo", "stack": "fastapi-postgres", "services": {"app": {"port": 8000}, "postgres": {"port": 5432}}})
            >>> result = generator.write(artifacts, "/tmp/devspeed-example", force=True)
            >>> result.replaced
            False
        """
        if not isinstance(artifacts, GeneratedArtifacts):
            raise TypeError("artifacts must be GeneratedArtifacts")
        if not isinstance(force, bool):
            raise TypeError("force must be a bool")
        directory = Path(output_dir)
        if not directory.exists():
            raise FileNotFoundError(f"output directory does not exist: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"output path is not a directory: {directory}")
        compose_path = directory / DEFAULT_COMPOSE_FILENAME
        env_path = directory / DEFAULT_ENV_FILENAME
        paths = (compose_path, env_path)
        with self._write_lock:
            existing = tuple(path for path in paths if path.exists())
            if existing and not force:
                LOGGER.warning("Refusing to overwrite existing outputs: %s", existing)
                raise OutputFileExistsError(existing)
            backups = {path: path.read_bytes() for path in existing} if force else {}
            temporary_paths: list[Path] = []
            try:
                temporary_paths.append(self._write_atomic(compose_path, artifacts.compose_yaml))
                temporary_paths.append(self._write_atomic(env_path, artifacts.env_file))
                LOGGER.info("Wrote generated files compose=%s env=%s", compose_path, env_path)
            except Exception as error:
                LOGGER.exception("Failed to persist generated outputs; attempting rollback")
                for temporary in temporary_paths:
                    temporary.unlink(missing_ok=True)
                if force:
                    for path, content in backups.items():
                        try:
                            path.write_bytes(content)
                        except OSError:
                            LOGGER.critical("Rollback failed for %s", path, exc_info=True)
                if isinstance(error, FileWriteError):
                    raise
                raise FileWriteError(f"could not write generated files: {error}") from error
        return WriteResult(compose_path, env_path, bool(existing))

    def _resolve_plugin(self, stack_name: str) -> StackPlugin:
        """Resolve and validate one plugin from the configured registry."""
        try:
            plugin = self.registry.get(stack_name)
            plugin.validate()
            return plugin
        except (KeyError, PluginError, AttributeError) as error:
            LOGGER.error("Unable to resolve stack plugin %s", stack_name)
            raise PluginResolutionError(
                f"unable to resolve stack plugin '{stack_name}': {error}"
            ) from error

    def _validate_ports(self, services: Mapping[str, Any]) -> set[int]:
        """Validate service ports and detect duplicate host bindings."""
        ports: dict[int, str] = {}
        for service_name, service in services.items():
            if not isinstance(service, Mapping) or "port" not in service:
                continue
            port = self._validate_port(str(service_name), service["port"])
            if port in ports:
                raise PortConflictError(
                    [f"services.{service_name}.port and {ports[port]} both use host port {port}"]
                )
            ports[port] = f"services.{service_name}.port"
        return set(ports)

    def _validate_port(self, service_name: str, value: Any) -> int:
        """Validate one TCP host port value."""
        if not isinstance(service_name, str) or not service_name.strip():
            raise ConfigValidationError("invalid service name")
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigValidationError(
                "invalid service port", [f"services.{service_name}.port must be an integer"]
            )
        if value < 1 or value > 65535:
            raise ConfigValidationError(
                "invalid service port",
                [f"services.{service_name}.port must be between 1 and 65535"],
            )
        return value

    def _check_host_ports(self, ports: set[int]) -> None:
        """Probe host ports when enabled, converting socket failures to domain errors."""
        if not self.settings.check_host_ports:
            LOGGER.debug("Host port probing disabled")
            return
        conflicts: list[str] = []
        for port in sorted(ports):
            try:
                available = self.port_checker(port)
            except OSError as error:
                LOGGER.warning("Host port probe failed port=%s error=%s", port, error)
                conflicts.append(f"host port {port} could not be checked: {error}")
                continue
            if not available:
                conflicts.append(f"host port {port} is already in use")
        if conflicts:
            raise PortConflictError(conflicts)

    @staticmethod
    def _default_port_checker(port: int) -> bool:
        """Return whether a TCP port can be bound on all local interfaces."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            try:
                probe.bind(("0.0.0.0", port))
            except OSError:
                return False
        return True

    def _normalize_compose(self, text: Any, plugin_name: str) -> str:
        """Validate plugin YAML and inject managed network/restart defaults."""
        if not isinstance(text, str) or not text.strip():
            raise ComposeGenerationError(
                f"stack plugin '{plugin_name}' returned empty Compose YAML"
            )
        if not self.settings.check_compose_yaml:
            return text if text.endswith("\n") else f"{text}\n"
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise ComposeGenerationError(
                f"stack plugin '{plugin_name}' returned invalid YAML: {error}"
            ) from error
        if not isinstance(document, dict):
            raise ComposeGenerationError("generated Compose document must be a YAML mapping")
        services = document.get("services")
        if not isinstance(services, dict) or not services:
            raise ComposeGenerationError(
                "generated Compose document must contain non-empty services"
            )
        if self.settings.inject_restart_policy:
            for service_name, service in services.items():
                if not isinstance(service, dict):
                    raise ComposeGenerationError(
                        f"Compose service '{service_name}' must be a mapping"
                    )
                service.setdefault("restart", "unless-stopped")
        if self.settings.inject_network:
            networks = document.setdefault("networks", {})
            if not isinstance(networks, dict):
                raise ComposeGenerationError("generated Compose networks must be a mapping")
            networks.setdefault("devspeed_network", {"driver": "bridge"})
            for service in services.values():
                current = service.get("networks", [])
                if isinstance(current, dict):
                    current.setdefault("devspeed_network", None)
                elif isinstance(current, list):
                    if "devspeed_network" not in current:
                        current.append("devspeed_network")
                else:
                    raise ComposeGenerationError(
                        "Compose service networks must be a list or mapping"
                    )
                service["networks"] = current
        document.setdefault("volumes", {})
        return yaml.safe_dump(document, sort_keys=False)

    def _write_atomic(self, destination: Path, content: str) -> Path:
        """Write content to a temporary sibling and atomically replace destination."""
        if not isinstance(content, str):
            raise TypeError("content must be a string")
        started = self.clock()
        last_error: Optional[BaseException] = None  # noqa: UP045
        for attempt in range(1, self.settings.retries + 1):
            temporary: Optional[Path] = None  # noqa: UP045
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=destination.parent,
                    prefix=f".{destination.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as handle:
                    temporary = Path(handle.name)
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, destination)
                return destination
            except OSError as error:
                last_error = error
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
                elapsed = self.clock() - started
                LOGGER.warning(
                    "Atomic write failed path=%s attempt=%s/%s elapsed=%.3f error=%s",
                    destination,
                    attempt,
                    self.settings.retries,
                    elapsed,
                    error,
                )
                if (
                    elapsed >= self.settings.operation_timeout_seconds
                    or attempt == self.settings.retries
                ):
                    break
                time.sleep(self.settings.retry_delay_seconds)
        raise FileWriteError(f"failed to write {destination}: {last_error}") from last_error


__all__ = [
    "DEFAULT_COMPOSE_FILENAME",
    "DEFAULT_ENV_FILENAME",
    "ComposeGenerationError",
    "ComposeGenerator",
    "ConfigValidationError",
    "FileWriteError",
    "GeneratedArtifacts",
    "GeneratorSettings",
    "OutputFileExistsError",
    "PluginResolutionError",
    "PortConflictError",
    "WriteResult",
]
