"""FastAPI and Postgres stack plugin."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin

from .common import lifecycle_command, postgres_service_yaml


class FastAPIPostgresPlugin(StackPlugin):
    """Provide a hot-reloading FastAPI application with Postgres."""

    @property
    def name(self) -> str:
        """Return the stable configuration identifier."""
        return "fastapi-postgres"

    @property
    def description(self) -> str:
        """Return the stack description shown by the CLI."""
        return "Python FastAPI API + Postgres"

    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return defaults for a FastAPI project."""
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {
                "install": "pip install --no-cache-dir -r requirements.txt",
                "dev": "uvicorn main:app --host 0.0.0.0 --port 8000 --reload",
            },
            "services": {
                "app": {"port": 8000, "python_version": "3.12"},
                "postgres": {
                    "port": 5432,
                    "db": project_name.replace("-", "_"),
                    "user": "devspeed",
                    "password": "devspeed",
                },
            },
        }

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        """Return a minimal FastAPI application for a new project."""
        return {
            "requirements.txt": "fastapi>=0.115,<1\nuvicorn[standard]>=0.34,<1\n",
            "main.py": """from fastapi import FastAPI

app = FastAPI(title="DevSpeed API")


@app.get("/")
def read_root():
    return {"message": "Your DevSpeed app is running"}
""",
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render the FastAPI and Postgres Compose services."""
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        project = config["project"]
        app_command = lifecycle_command(
            config,
            "pip install --no-cache-dir -r requirements.txt",
            f"uvicorn main:app --host 0.0.0.0 --port {app['port']} --reload",
        )
        postgres_yaml = postgres_service_yaml(postgres, project, database_url=False)

        return f"""\
name: {project}

services:
  app:
    image: python:{app['python_version']}-slim
    working_dir: /app
    volumes:
      - ./:/app
    command: {app_command}
    ports:
      - "{app['port']}:{app['port']}"
    environment:
      - DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}@postgres:5432/{postgres['db']}
    depends_on:
      postgres:
        condition: service_healthy

{postgres_yaml}
"""

    def env_file(self, config: Mapping[str, Any]) -> str:
        """Render the host Postgres connection variable."""
        postgres = config["services"]["postgres"]
        return f"""\
DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}@localhost:{postgres['port']}/{postgres['db']}
"""

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return startup notes for the generated FastAPI environment."""
        app_port = config["services"]["app"]["port"]
        return [
            "App container installs from requirements.txt and runs uvicorn with --reload.",
            f"API should be reachable at http://localhost:{app_port} once dependencies finish installing.",
            "Make sure you have a main.py with a FastAPI 'app' instance at the project root.",
        ]


plugin = FastAPIPostgresPlugin()
NAME = plugin.name
DESCRIPTION = plugin.description


def default_config(project_name: str) -> dict[str, Any]:
    """Backward-compatible wrapper for the plugin method."""
    return plugin.default_config(project_name)


def starter_files(config: Mapping[str, Any]) -> dict[str, str]:
    """Backward-compatible wrapper for the plugin method."""
    return plugin.starter_files(config)


def compose_yaml(config: Mapping[str, Any]) -> str:
    """Backward-compatible wrapper for the plugin method."""
    return plugin.compose_yaml(config)


def env_file(config: Mapping[str, Any]) -> str:
    """Backward-compatible wrapper for the plugin method."""
    return plugin.env_file(config)


def post_up_hints(config: Mapping[str, Any]) -> list[str]:
    """Backward-compatible wrapper for the plugin method."""
    return plugin.post_up_hints(config)
