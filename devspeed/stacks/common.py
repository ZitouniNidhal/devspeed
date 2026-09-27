"""Shared rendering helpers for stack templates."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


def postgres_service_yaml(
    postgres: Mapping[str, Any],
    project: str,
    *,
    database_url: bool = False,
) -> str:
    """Render the common Postgres service and named volume block."""
    database_line = ""
    if database_url:
        database_line = (
            f"      - DATABASE_URL=postgres://{postgres['user']}:{postgres['password']}"
            f"@postgres:5432/{postgres['db']}\n"
        )
    return f"""\
  postgres:
    image: postgres:16-alpine
    ports:
      - \"{postgres['port']}:5432\"
    environment:
      - POSTGRES_DB={postgres['db']}
      - POSTGRES_USER={postgres['user']}
      - POSTGRES_PASSWORD={postgres['password']}
{database_line}    volumes:
      - {project}_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: [\"CMD-SHELL\", \"pg_isready -U {postgres['user']}\"]
      interval: 3s
      timeout: 3s
      retries: 10

  
volumes:
  {project}_pgdata:
"""


def env_example(env_text: str) -> str:
    """Mask common local credentials while preserving useful connection examples."""
    masked = re.sub(r"(://[^:]+:)[^@]+@", r"\1<password>@", env_text)
    return re.sub(r"(?m)^(POSTGRES_PASSWORD=).*$", r"\1<password>", masked)


def lifecycle_command(
    config: Mapping[str, Any],
    default_install: str,
    default_dev: str,
) -> str:
    """Build the app command, allowing config to override lifecycle steps."""
    lifecycle = config.get("lifecycle", {})
    if not isinstance(lifecycle, Mapping):
        lifecycle = {}
    install = lifecycle.get("install", default_install)
    dev = lifecycle.get("dev", default_dev)
    if not isinstance(install, str) or not isinstance(dev, str):
        raise TypeError("lifecycle.install and lifecycle.dev must be strings")
    return f'sh -c "{install} && {dev}"'
