"""Flask and Postgres stack plugin."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin

from .common import lifecycle_command, postgres_service_yaml


class FlaskPostgresPlugin(StackPlugin):
    """Provide a hot-reloading Flask application with Postgres."""

    @property
    def name(self) -> str:
        """Return the stable configuration identifier."""
        return "flask-postgres"

    @property
    def description(self) -> str:
        """Return the stack description shown by the CLI."""
        return "Python Flask API + Postgres"

    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return defaults for a Flask project."""
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {
                "install": "pip install --no-cache-dir -r requirements.txt",
                "dev": "flask --app app run --host 0.0.0.0 --port 5000 --debug",
            },
            "services": {
                "app": {"port": 5000, "python_version": "3.12"},
                "postgres": {
                    "port": 5432,
                    "db": project_name.replace("-", "_"),
                    "user": "devspeed",
                    "password": "devspeed",
                },
            },
        }

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        """Return a minimal Flask application for a new project."""
        return {
            "requirements.txt": "Flask>=3.1,<4\npsycopg[binary]>=3.2,<4\n",
            "app.py": """from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def read_root():
    return jsonify(message="Your DevSpeed app is running")
""",
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render the Flask and Postgres Compose services."""
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        project = config["project"]
        command = lifecycle_command(
            config,
            "pip install --no-cache-dir -r requirements.txt",
            f"flask --app app run --host 0.0.0.0 --port {app['port']} --debug",
        )
        postgres_yaml = postgres_service_yaml(postgres, project)
        return f"""\
name: {project}

services:
  app:
    image: python:{app['python_version']}-slim
    working_dir: /app
    volumes:
      - ./:/app
    command: {command}
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
        return (
            f"DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}"
            f"@localhost:{postgres['port']}/{postgres['db']}\n"
        )

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return startup notes for the generated Flask environment."""
        port = config["services"]["app"]["port"]
        return [
            "App container installs requirements.txt and runs Flask in debug mode.",
            f"API should be reachable at http://localhost:{port} once dependencies finish installing.",
            "Make sure app.py exposes a Flask app named 'app'.",
        ]


plugin = FlaskPostgresPlugin()
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
