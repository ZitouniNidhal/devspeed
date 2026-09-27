import argparse
import pathlib
import shutil
import subprocess
import sys
from typing import Any, Mapping, Optional, Sequence

from devspeed import config as cfg
from devspeed.stacks.common import env_example
from devspeed.stacks import get_stack, list_stacks

GENERATED_COMPOSE = "docker-compose.devspeed.yml"
GENERATED_ENV = ".env.devspeed"
GENERATED_ENV_EXAMPLE = ".env.example"


def cmd_list(_args: argparse.Namespace) -> None:
    print("\ndevspeed stacks\n")
    for name, description in list_stacks():
        print(f"  {name:<24} {description}")
    print("\nStart one with: devspeed init <stack>")


def cmd_init(args: argparse.Namespace) -> None:
    project_name = args.project_name or pathlib.Path.cwd().name
    _create_config(args.stack, project_name, args.force, args.dry_run)


def _create_config(
    stack_name: str, project_name: str, force: bool = False, dry_run: bool = False
) -> None:
    try:
        stack = get_stack(stack_name)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    path = cfg.config_path()
    if path.exists() and not force:
        print(f"{cfg.CONFIG_FILENAME} already exists. Use --force to overwrite.")
        sys.exit(1)

    config = stack.default_config(project_name)
    if dry_run:
        print(f"[dry-run] would write {cfg.CONFIG_FILENAME}")
    else:
        cfg.save_config(config)
    created_files = []
    for filename, contents in stack.starter_files(config).items():
        starter_path = pathlib.Path(filename)
        if not starter_path.exists():
            if not dry_run:
                starter_path.parent.mkdir(parents=True, exist_ok=True)
                starter_path.write_text(contents, encoding="utf-8")
            created_files.append(filename)
    example_path = pathlib.Path(GENERATED_ENV_EXAMPLE)
    if not example_path.exists():
        if not dry_run:
            example_path.write_text(env_example(stack.env_file(config)), encoding="utf-8")
        created_files.append(GENERATED_ENV_EXAMPLE)
    if dry_run:
        print("[dry-run] no files were written")
    print(f"\nCreated {cfg.CONFIG_FILENAME}")
    print(f"  stack   {stack.NAME}")
    print(f"  project {project_name}")
    if created_files:
        print(f"  starter {', '.join(created_files)}")
    print("\nNext steps:")
    print("  1. devspeed doctor   # check Docker and your config")
    print("  2. devspeed up       # start the environment")


def cmd_create(args: argparse.Namespace) -> None:
    print("\ndevspeed create\n")
    print("Choose a stack:")
    stacks = list_stacks()
    for index, (_, description) in enumerate(stacks, start=1):
        print(f"  {index}. {description}")

    try:
        selection = input("\nStack [1]: ").strip() or "1"
        stack_index = int(selection) - 1
        stack_name = stacks[stack_index][0]
    except (ValueError, EOFError, IndexError):
        print("Please choose one of the numbered stacks.")
        sys.exit(1)

    default_name = pathlib.Path.cwd().name
    try:
        project_name = input(f"Project name [{default_name}]: ").strip() or default_name
    except EOFError:
        project_name = default_name
    _create_config(stack_name, args.project_name or project_name, args.force, args.dry_run)


def _require_docker() -> None:
    if shutil.which("docker") is None:
        print(
            "Docker not detected. Install Docker Desktop from "
            "https://www.docker.com/products/docker-desktop/ and make sure "
            "'docker compose' works, then try again."
        )
        sys.exit(1)


def cmd_doctor(_args: argparse.Namespace) -> None:
    """Check the local prerequisites before a potentially noisy `up`."""
    checks = []
    try:
        config = cfg.load_config()
        get_stack(config["stack"])
        checks.append((True, f"{cfg.CONFIG_FILENAME} is valid ({config['stack']})"))
    except (SystemExit, KeyError):
        checks.append((False, f"{cfg.CONFIG_FILENAME} is missing or invalid"))

    docker_path = shutil.which("docker")
    if not docker_path:
        checks.append((False, "Docker CLI is not installed or not on PATH"))
    else:
        result = subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        checks.append((result.returncode == 0, "Docker Compose v2 is available"))

    print("\ndevspeed doctor\n")
    for passed, message in checks:
        print(f"  [{'OK' if passed else '!!'}] {message}")
    if not all(passed for passed, _ in checks):
        print("\nFix the items marked !!, then run devspeed doctor again.")
        sys.exit(1)
    print("\nReady. Run devspeed up to start your environment.")


def _generate_files(config: Mapping[str, Any], write: bool = True):
    stack = get_stack(config["stack"])
    compose_text = stack.compose_yaml(config)
    env_text = stack.env_file(config)

    files = {
        GENERATED_COMPOSE: compose_text,
        GENERATED_ENV: env_text,
        GENERATED_ENV_EXAMPLE: env_example(env_text),
    }
    if write:
        for filename, contents in files.items():
            pathlib.Path(filename).write_text(contents, encoding="utf-8")
    else:
        print("[dry-run] generated files:")
        for filename, contents in files.items():
            print(f"\n--- {filename} ---\n{contents}", end="")
    return stack


def cmd_up(args: argparse.Namespace) -> None:
    _require_docker()
    config = cfg.load_config()
    stack = _generate_files(config, write=not args.dry_run)
    if args.dry_run:
        print("\n[dry-run] Docker Compose was not started.")
        return

    print(f"Starting '{config['project']}' ({config['stack']}) with Docker Compose...")
    print("  [1/2] Generated Compose and environment files")
    print("  [2/2] Starting containers")
    result = subprocess.run(
        ["docker", "compose", "-f", GENERATED_COMPOSE, "up", "-d"],
    )
    if result.returncode != 0:
        print("\nDocker Compose could not start the environment.")
        print("Check that Docker Desktop is running and that the configured host ports are free.")
        sys.exit(result.returncode)

    print(f"\nCopied service URLs into {GENERATED_ENV} — copy the values you need into your app's .env.")
    print("\nUp and running. A few notes:")
    for hint in stack.post_up_hints(config):
        print(f"  - {hint}")
    print("\nRun 'devspeed down' to stop, or 'devspeed cleanup' to also remove data volumes.")


def cmd_down(_args: argparse.Namespace) -> None:
    _require_docker()
    if not pathlib.Path(GENERATED_COMPOSE).exists():
        print("Nothing to stop — no generated compose file found. Did you run 'devspeed up'?")
        sys.exit(1)
    result = subprocess.run(["docker", "compose", "-f", GENERATED_COMPOSE, "down"])
    sys.exit(result.returncode)


def _require_compose_file() -> None:
    if not pathlib.Path(GENERATED_COMPOSE).exists():
        print("No generated Compose file found. Run 'devspeed up' first.")
        sys.exit(1)


def cmd_status(_args: argparse.Namespace) -> None:
    _require_docker()
    _require_compose_file()
    result = subprocess.run(["docker", "compose", "-f", GENERATED_COMPOSE, "ps"])
    sys.exit(result.returncode)


def cmd_logs(args: argparse.Namespace) -> None:
    _require_docker()
    _require_compose_file()
    command = ["docker", "compose", "-f", GENERATED_COMPOSE, "logs"]
    if args.follow:
        command.append("--follow")
    if args.service:
        command.append(args.service)
    result = subprocess.run(command)
    sys.exit(result.returncode)


def cmd_cleanup(_args: argparse.Namespace) -> None:
    _require_docker()
    if pathlib.Path(GENERATED_COMPOSE).exists():
        result = subprocess.run(["docker", "compose", "-f", GENERATED_COMPOSE, "down", "-v"])
        if result.returncode != 0:
            sys.exit(result.returncode)
        pathlib.Path(GENERATED_COMPOSE).unlink(missing_ok=True)
    pathlib.Path(GENERATED_ENV).unlink(missing_ok=True)
    pathlib.Path(GENERATED_ENV_EXAMPLE).unlink(missing_ok=True)
    print("Containers, volumes, and generated files removed. devspeed.yaml is left untouched.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="devspeed",
        description="Spin up a local dev environment from a single config file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List available stack templates")
    p_list.set_defaults(func=cmd_list)

    p_doctor = sub.add_parser("doctor", help="Check Docker and the current project config")
    p_doctor.set_defaults(func=cmd_doctor)

    p_init = sub.add_parser("init", help="Create a devspeed.yaml for a stack in this directory")
    p_init.add_argument("stack", help="Stack template name (see 'devspeed list')")
    p_init.add_argument("--name", dest="project_name", default=None, help="Project name (default: folder name)")
    p_init.add_argument("--force", action="store_true", help="Overwrite an existing devspeed.yaml")
    p_init.add_argument("--dry-run", action="store_true", help="Preview files without writing them")
    p_init.set_defaults(func=cmd_init)

    p_create = sub.add_parser("create", help="Interactively create a project environment")
    p_create.add_argument("--name", dest="project_name", default=None, help="Project name (default: folder name)")
    p_create.add_argument("--force", action="store_true", help="Overwrite an existing devspeed.yaml")
    p_create.add_argument("--dry-run", action="store_true", help="Preview files without writing them")
    p_create.set_defaults(func=cmd_create)

    p_up = sub.add_parser("up", help="Generate compose files from devspeed.yaml and start everything")
    p_up.add_argument("--dry-run", action="store_true", help="Preview generated files without starting Docker")
    p_up.set_defaults(func=cmd_up)

    p_down = sub.add_parser("down", help="Stop containers (keeps data volumes)")
    p_down.set_defaults(func=cmd_down)

    p_status = sub.add_parser("status", help="Show the status of running services")
    p_status.set_defaults(func=cmd_status)

    p_logs = sub.add_parser("logs", help="Show service logs")
    p_logs.add_argument("service", nargs="?", help="Optional service name, such as app or postgres")
    p_logs.add_argument("--follow", "-f", action="store_true", help="Keep streaming new log output")
    p_logs.set_defaults(func=cmd_logs)

    p_cleanup = sub.add_parser("cleanup", help="Stop containers, delete volumes and generated files")
    p_cleanup.set_defaults(func=cmd_cleanup)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
