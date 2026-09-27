from __future__ import annotations

import pathlib
import sys
from typing import Any, Optional

import yaml

CONFIG_FILENAME = "devspeed.yaml"


def config_path(directory: Optional[pathlib.Path] = None) -> pathlib.Path:
    directory = directory or pathlib.Path.cwd()
    return directory / CONFIG_FILENAME


def load_config(directory: Optional[pathlib.Path] = None) -> dict[str, Any]:
    path = config_path(directory)
    if not path.exists():
        print(f"No {CONFIG_FILENAME} found in {path.parent}. Run 'devspeed init <stack>' first.")
        sys.exit(1)
    try:
        with path.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as error:
        print(f"Could not read {CONFIG_FILENAME}: invalid YAML ({error}).")
        sys.exit(1)

    errors = validate_config(config)
    if errors:
        print(f"{CONFIG_FILENAME} needs attention:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    return config


def validate_config(config: Any) -> list[str]:
    """Return friendly configuration errors without importing stack modules."""
    if not isinstance(config, dict):
        return ["the file must contain a YAML object"]

    errors = []
    if not config.get("project"):
        errors.append("project is required")
    if not config.get("stack"):
        errors.append("stack is required")
    if not isinstance(config.get("services"), dict):
        errors.append("services must be a YAML object")
    lifecycle = config.get("lifecycle")
    if lifecycle is not None and not isinstance(lifecycle, dict):
        errors.append("lifecycle must be a YAML object")
    elif isinstance(lifecycle, dict):
        for key in ("install", "dev"):
            if key in lifecycle and not isinstance(lifecycle[key], str):
                errors.append(f"lifecycle.{key} must be a string")
    return errors


def save_config(config: dict[str, Any], directory: Optional[pathlib.Path] = None) -> pathlib.Path:
    path = config_path(directory)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)
    return path
