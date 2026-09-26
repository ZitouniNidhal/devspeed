import argparse
import pathlib
import shutil
import subprocess
import sys

from devspeed import config as cfg
from devspeed.stacks import get_stack, list_stacks

GENERATED_COMPOSE = "docker-compose.devspeed.yml"
GENERATED_ENV = ".env.devspeed"


def cmd_list(_args):
    print("Available stacks:\n")
    for name, description in list_stacks():
        print(f"  {name:<24} {description}")
    print("\nRun 'devspeed init <stack>' inside your project folder to get started.")


def cmd_init(args):
    project_name = args.project_name or pathlib.Path.cwd().name
    try:
        stack = get_stack(args.stack)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    path = cfg.config_path()
    if path.exists() and not args.force:
        print(f"{cfg.CONFIG_FILENAME} already exists. Use --force to overwrite.")
        sys.exit(1)

    config = stack.default_config(project_name)
    cfg.save_config(config)
    print(f"Created {cfg.CONFIG_FILENAME} for stack '{stack.NAME}' (project: {project_name}).")
    print("Next: review the file, then run 'devspeed up'.")


def _require_docker():
    if shutil.which("docker") is None:
        print("Docker CLI not found. Install Docker Desktop (or the docker engine) and make sure "
              "'docker compose' works, then try again.")
        sys.exit(1)


def _generate_files(config: dict):
    stack = get_stack(config["stack"])
    compose_text = stack.compose_yaml(config)
    env_text = stack.env_file(config)

    pathlib.Path(GENERATED_COMPOSE).write_text(compose_text)
    pathlib.Path(GENERATED_ENV).write_text(env_text)
    return stack


def cmd_up(_args):
    _require_docker()
    config = cfg.load_config()
    stack = _generate_files(config)

    print(f"Starting '{config['project']}' ({config['stack']}) with Docker Compose...\n")
    result = subprocess.run(
        ["docker", "compose", "-f", GENERATED_COMPOSE, "up", "-d"],
    )
    if result.returncode != 0:
        print("\ndocker compose failed to start. See output above for details.")
        sys.exit(result.returncode)

    print(f"\nCopied service URLs into {GENERATED_ENV} — copy the values you need into your app's .env.")
    print("\nUp and running. A few notes:")
    for hint in stack.post_up_hints(config):
        print(f"  - {hint}")
    print("\nRun 'devspeed down' to stop, or 'devspeed cleanup' to also remove data volumes.")


def cmd_down(_args):
    _require_docker()
    if not pathlib.Path(GENERATED_COMPOSE).exists():
        print("Nothing to stop — no generated compose file found. Did you run 'devspeed up'?")
        sys.exit(1)
    subprocess.run(["docker", "compose", "-f", GENERATED_COMPOSE, "down"])


def cmd_cleanup(_args):
    _require_docker()
    if pathlib.Path(GENERATED_COMPOSE).exists():
        subprocess.run(["docker", "compose", "-f", GENERATED_COMPOSE, "down", "-v"])
        pathlib.Path(GENERATED_COMPOSE).unlink(missing_ok=True)
    pathlib.Path(GENERATED_ENV).unlink(missing_ok=True)
    print("Containers, volumes, and generated files removed. devspeed.yaml is left untouched.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="devspeed",
        description="Spin up a local dev environment from a single config file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List available stack templates")
    p_list.set_defaults(func=cmd_list)

    p_init = sub.add_parser("init", help="Create a devspeed.yaml for a stack in this directory")
    p_init.add_argument("stack", help="Stack template name (see 'devspeed list')")
    p_init.add_argument("--name", dest="project_name", default=None, help="Project name (default: folder name)")
    p_init.add_argument("--force", action="store_true", help="Overwrite an existing devspeed.yaml")
    p_init.set_defaults(func=cmd_init)

    p_up = sub.add_parser("up", help="Generate compose files from devspeed.yaml and start everything")
    p_up.set_defaults(func=cmd_up)

    p_down = sub.add_parser("down", help="Stop containers (keeps data volumes)")
    p_down.set_defaults(func=cmd_down)

    p_cleanup = sub.add_parser("cleanup", help="Stop containers, delete volumes and generated files")
    p_cleanup.set_defaults(func=cmd_cleanup)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
