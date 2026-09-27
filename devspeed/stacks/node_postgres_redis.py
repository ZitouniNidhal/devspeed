"""Node.js, Postgres, and Redis stack plugin."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin

from .common import lifecycle_command


class NodePostgresRedisPlugin(StackPlugin):
    """Provide a hot-reloading Node.js/Express API with Postgres and Redis."""

    @property
    def name(self) -> str:
        """Return the stable configuration identifier."""
        return "node-postgres-redis"

    @property
    def description(self) -> str:
        """Return the stack description shown by the CLI."""
        return "Node.js/Express API + Postgres + Redis"

    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return defaults for a Node.js project."""
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {"install": "npm install", "dev": "npm run dev"},
            "services": {
                "app": {"port": 3000, "node_version": "22"},
                "postgres": {
                    "port": 5432,
                    "db": project_name.replace("-", "_"),
                    "user": "devspeed",
                    "password": "devspeed",
                },
                "redis": {"port": 6379},
            },
        }

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        """Return a minimal Express application for a new project."""
        return {
            "package.json": """{
  "name": "devspeed-node-app",
  "private": true,
  "scripts": {"dev": "node server.js"},
  "dependencies": {"express": "^5.1.0"}
}
""",
            "server.js": """const express = require("express");

const app = express();
const port = process.env.PORT || 3000;

app.get("/", (_request, response) => {
  response.json({ message: "Your DevSpeed app is running", database: process.env.DATABASE_URL });
});

app.listen(port, "0.0.0.0", () => console.log(`API listening on ${port}`));
""",
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render the Node.js, Postgres, and Redis Compose services."""
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        redis = services["redis"]
        project = config["project"]
        app_command = lifecycle_command(config, "npm install", "npm run dev")

        return f"""\
name: {project}

services:
  app:
    image: node:{app['node_version']}-alpine
    working_dir: /app
    volumes:
      - ./:/app
    command: {app_command}
    ports:
      - "{app['port']}:{app['port']}"
    environment:
      - PORT={app['port']}
      - DATABASE_URL=postgres://{postgres['user']}:{postgres['password']}@postgres:5432/{postgres['db']}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:16-alpine
    ports:
      - "{postgres['port']}:5432"
    environment:
      - POSTGRES_DB={postgres['db']}
      - POSTGRES_USER={postgres['user']}
      - POSTGRES_PASSWORD={postgres['password']}
    volumes:
      - {project}_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {postgres['user']}"]
      interval: 3s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7-alpine
    ports:
      - "{redis['port']}:6379"

volumes:
  {project}_pgdata:
"""

    def env_file(self, config: Mapping[str, Any]) -> str:
        """Render host connection variables for Node.js development."""
        services = config["services"]
        postgres = services["postgres"]
        app = services["app"]
        return f"""\
PORT={app['port']}
DATABASE_URL=postgres://{postgres['user']}:{postgres['password']}@localhost:{postgres['port']}/{postgres['db']}
REDIS_URL=redis://localhost:{services['redis']['port']}
"""

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return startup notes for the generated Node.js environment."""
        app_port = config["services"]["app"]["port"]
        return [
            "App container will run 'npm install && npm run dev' — make sure package.json has a 'dev' script.",
            f"API should be reachable at http://localhost:{app_port} once dependencies finish installing.",
            "Postgres and Redis are exposed on localhost too, so you can connect with any GUI client.",
        ]


plugin = NodePostgresRedisPlugin()
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
