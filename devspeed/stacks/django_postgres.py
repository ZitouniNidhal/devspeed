"""Django and Postgres stack plugin."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin

from .common import lifecycle_command, postgres_service_yaml


class DjangoPostgresPlugin(StackPlugin):
    """Provide a hot-reloading Django application with Postgres."""

    @property
    def name(self) -> str:
        """Return the stable configuration identifier."""
        return "django-postgres"

    @property
    def description(self) -> str:
        """Return the stack description shown by the CLI."""
        return "Django web app + Postgres"

    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return defaults for a Django project."""
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {
                "install": "pip install --no-cache-dir -r requirements.txt",
                "dev": "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000",
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
        """Return a minimal Django project for a new project."""
        return {
            "requirements.txt": "Django>=5.1,<6\npsycopg[binary]>=3.2,<4\n",
            "manage.py": """import os
import sys


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
""",
            "config/__init__.py": "",
            "config/settings.py": """import os

SECRET_KEY = "devspeed-local-only"
DEBUG = True
ROOT_URLCONF = "config.urls"
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = ["django.contrib.contenttypes"]
MIDDLEWARE = []
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.getenv("POSTGRES_DB", "devspeed"),
    "USER": os.getenv("POSTGRES_USER", "devspeed"),
    "PASSWORD": os.getenv("POSTGRES_PASSWORD", "devspeed"),
    "HOST": os.getenv("POSTGRES_HOST", "postgres"),
    "PORT": "5432",
}}
""",
            "config/urls.py": """from django.http import JsonResponse
from django.urls import path


urlpatterns = [path("", lambda request: JsonResponse({"message": "Your DevSpeed app is running"}))]
""",
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render the Django and Postgres Compose services."""
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        project = config["project"]
        app_command = lifecycle_command(
            config,
            "pip install --no-cache-dir -r requirements.txt",
            f"python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:{app['port']}",
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
      - DATABASE_URL=postgres://{postgres['user']}:{postgres['password']}@postgres:5432/{postgres['db']}
      - POSTGRES_DB={postgres['db']}
      - POSTGRES_USER={postgres['user']}
      - POSTGRES_PASSWORD={postgres['password']}
      - POSTGRES_HOST=postgres
    depends_on:
      postgres:
        condition: service_healthy

{postgres_yaml}
"""

    def env_file(self, config: Mapping[str, Any]) -> str:
        """Render the host Postgres connection variable."""
        postgres = config["services"]["postgres"]
        return (
            f"DATABASE_URL=postgres://{postgres['user']}:{postgres['password']}"
            f"@localhost:{postgres['port']}/{postgres['db']}\n"
        )

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return startup notes for the generated Django environment."""
        app_port = config["services"]["app"]["port"]
        return [
            "App container installs requirements.txt and runs Django's development server.",
            f"Django should be reachable at http://localhost:{app_port} once dependencies finish installing.",
            "Make sure manage.py and requirements.txt are present at the project root.",
        ]


plugin = DjangoPostgresPlugin()
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
