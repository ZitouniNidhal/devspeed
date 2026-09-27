from typing import Any

from .common import lifecycle_command

NAME = "django-postgres"
DESCRIPTION = "Django web app + Postgres"


def default_config(project_name: str) -> dict[str, Any]:
    return {
        "project": project_name,
        "stack": NAME,
        "lifecycle": {
            "install": "pip install --no-cache-dir -r requirements.txt",
            "dev": "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000",
        },
        "services": {
            "app": {
                "port": 8000,
                "python_version": "3.12",
            },
            "postgres": {
                "port": 5432,
                "db": project_name.replace("-", "_"),
                "user": "devspeed",
                "password": "devspeed",
            },
        },
    }


def starter_files(_config: dict[str, Any]) -> dict[str, str]:
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


def compose_yaml(config: dict[str, Any]) -> str:
    svc = config["services"]
    app = svc["app"]
    pg = svc["postgres"]
    project = config["project"]
    app_command = lifecycle_command(
        config,
        "pip install --no-cache-dir -r requirements.txt",
        f"python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:{app['port']}",
    )

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
      - DATABASE_URL=postgres://{pg['user']}:{pg['password']}@postgres:5432/{pg['db']}
      - POSTGRES_DB={pg['db']}
      - POSTGRES_USER={pg['user']}
      - POSTGRES_PASSWORD={pg['password']}
      - POSTGRES_HOST=postgres
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    ports:
      - "{pg['port']}:5432"
    environment:
      - POSTGRES_DB={pg['db']}
      - POSTGRES_USER={pg['user']}
      - POSTGRES_PASSWORD={pg['password']}
    volumes:
      - {project}_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {pg['user']}"]
      interval: 3s
      timeout: 3s
      retries: 10

volumes:
  {project}_pgdata:
"""


def env_file(config: dict[str, Any]) -> str:
    pg = config["services"]["postgres"]
    return (
        f"DATABASE_URL=postgres://{pg['user']}:{pg['password']}@localhost:{pg['port']}/{pg['db']}\n"
    )


def post_up_hints(config: dict[str, Any]) -> list[str]:
    app_port = config["services"]["app"]["port"]
    return [
        "App container installs requirements.txt and runs Django's development server.",
        f"Django should be reachable at http://localhost:{app_port} once dependencies finish installing.",
        "Make sure manage.py and requirements.txt are present at the project root.",
    ]
