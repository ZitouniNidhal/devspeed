"""
Stack template registry.

Each stack module exposes:
  - NAME: str
  - DESCRIPTION: str
  - default_config(project_name: str) -> dict
  - compose_yaml(config: dict) -> str
  - env_file(config: dict) -> str
  - post_up_hints(config: dict) -> list[str]
    - starter_files(config: dict) -> dict[str, str]
"""

from . import django_postgres, fastapi_postgres, flask_postgres, node_postgres_redis

STACKS = {
    node_postgres_redis.NAME: node_postgres_redis,
    fastapi_postgres.NAME: fastapi_postgres,
    django_postgres.NAME: django_postgres,
    flask_postgres.NAME: flask_postgres,
}


def get_stack(name: str):
    if name not in STACKS:
        available = ", ".join(sorted(STACKS.keys()))
        raise KeyError(f"Unknown stack '{name}'. Available stacks: {available}")
    return STACKS[name]


def list_stacks() -> list[tuple[str, str]]:
    return [(mod.NAME, mod.DESCRIPTION) for mod in STACKS.values()]
