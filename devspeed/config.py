import pathlib
import sys

import yaml

CONFIG_FILENAME = "devspeed.yaml"


def config_path(directory: pathlib.Path = None) -> pathlib.Path:
    directory = directory or pathlib.Path.cwd()
    return directory / CONFIG_FILENAME


def load_config(directory: pathlib.Path = None) -> dict:
    path = config_path(directory)
    if not path.exists():
        print(f"No {CONFIG_FILENAME} found in {path.parent}. Run 'devspeed init <stack>' first.")
        sys.exit(1)
    try:
        with open(path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as error:
        print(f"Could not read {CONFIG_FILENAME}: invalid YAML ({error}).")
        sys.exit(1)

    errors = validate_config(config)
    if errors:
        print(f"{CONFIG_FILENAME} needs attention:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    return config


def validate_config(config: dict) -> list[str]:
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
    return errors


def save_config(config: dict, directory: pathlib.Path = None) -> pathlib.Path:
    path = config_path(directory)
    with open(path, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)
    return path
