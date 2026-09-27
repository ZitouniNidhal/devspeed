from typing import Any

from .common import lifecycle_command

NAME = "node-postgres-redis"
DESCRIPTION = "Node.js/Express API + Postgres + Redis"


def default_config(project_name: str) -> dict[str, Any]:
    return {
        "project": project_name,
        "stack": NAME,
        "lifecycle": {"install": "npm install", "dev": "npm run dev"},
        "services": {
            "app": {
                "port": 3000,
                "node_version": "22",
            },
            "postgres": {
                "port": 5432,
                "db": project_name.replace("-", "_"),
                "user": "devspeed",
                "password": "devspeed",
            },
            "redis": {
                "port": 6379,
            },
        },
    }


def starter_files(_config: dict[str, Any]) -> dict[str, str]:
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


def compose_yaml(config: dict[str, Any]) -> str:
    svc = config["services"]
    app = svc["app"]
    pg = svc["postgres"]
    redis = svc["redis"]
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
      - DATABASE_URL=postgres://{pg['user']}:{pg['password']}@postgres:5432/{pg['db']}
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

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

  redis:
    image: redis:7-alpine
    ports:
      - "{redis['port']}:6379"

volumes:
  {project}_pgdata:
"""


def env_file(config: dict[str, Any]) -> str:
    svc = config["services"]
    pg = svc["postgres"]
    app = svc["app"]
    return f"""\
PORT={app['port']}
DATABASE_URL=postgres://{pg['user']}:{pg['password']}@localhost:{pg['port']}/{pg['db']}
REDIS_URL=redis://localhost:{svc['redis']['port']}
"""


def post_up_hints(config: dict[str, Any]) -> list[str]:
    app_port = config["services"]["app"]["port"]
    return [
        "App container will run 'npm install && npm run dev' — make sure package.json has a 'dev' script.",
        f"API should be reachable at http://localhost:{app_port} once dependencies finish installing.",
        "Postgres and Redis are exposed on localhost too, so you can connect with any GUI client.",
    ]
