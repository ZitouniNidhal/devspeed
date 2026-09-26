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
    with open(path) as f:
        return yaml.safe_load(f)


def save_config(config: dict, directory: pathlib.Path = None) -> pathlib.Path:
    path = config_path(directory)
    with open(path, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)
    return path
