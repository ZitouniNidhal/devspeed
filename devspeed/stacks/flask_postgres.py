"""Flask and Postgres stack template."""

from typing import Any

from .common import lifecycle_command, postgres_service_yaml

NAME = "flask-postgres"
DESCRIPTION = "Python Flask API + Postgres"


def default_config(project_name: str) -> dict[str, Any]:
    return {
        "project": project_name,
        "stack": NAME,
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


def starter_files(_config: dict[str, Any]) -> dict[str, str]:
    return {
        "requirements.txt": "Flask>=3.1,<4\npsycopg[binary]>=3.2,<4\n",
        "app.py": '''from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def read_root():
    return jsonify(message="Your DevSpeed app is running")
''',
    }


def compose_yaml(config: dict[str, Any]) -> str:
    services = config["services"]
    app = services["app"]
    postgres = services["postgres"]
    project = config["project"]
    command = lifecycle_command(
        config,
        "pip install --no-cache-dir -r requirements.txt",
        f"flask --app app run --host 0.0.0.0 --port {app['port']} --debug",
    )
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

{postgres_service_yaml(postgres, project)}
"""


def env_file(config: dict[str, Any]) -> str:
    postgres = config["services"]["postgres"]
    return (
        f"DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}"
        f"@localhost:{postgres['port']}/{postgres['db']}\n"
    )


def post_up_hints(config: dict[str, Any]) -> list[str]:
    port = config["services"]["app"]["port"]
    return [
        "App container installs requirements.txt and runs Flask in debug mode.",
        f"API should be reachable at http://localhost:{port} once dependencies finish installing.",
        "Make sure app.py exposes a Flask app named 'app'.",
    ]
