"""Go Gin API and PostgreSQL stack plugin."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin

from .common import lifecycle_command, postgres_service_yaml


class GoGinPostgresPlugin(StackPlugin):
    """Provide a Go Gin web framework application with Postgres."""

    @property
    def name(self) -> str:
        return "go-gin-postgres"

    @property
    def description(self) -> str:
        return "Go Gin REST API + PostgreSQL database"

    def default_config(self, project_name: str) -> dict[str, Any]:
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {
                "install": "go mod tidy",
                "dev": "go run main.go",
            },
            "services": {
                "app": {"port": 8080, "go_version": "1.22"},
                "postgres": {
                    "port": 5432,
                    "db": project_name.replace("-", "_"),
                    "user": "devspeed",
                    "password": "devspeed",
                },
            },
        }

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        project_name = config["project"]

        go_mod = f"""module {project_name}

go 1.22

require github.com/gin-gonic/gin v1.9.1
"""

        main_go = f"""package main

import (
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

func main() {{
	r := gin.Default()

	r.GET("/", func(c *gin.Context) {{
		c.JSON(http.StatusOK, gin.H{{
			"message": "⚡ Welcome to {project_name} API",
			"status":  "running",
		}})
	}})

	r.GET("/health", func(c *gin.Context) {{
		c.JSON(http.StatusOK, gin.H{{"status": "ok"}})
	}})

	port := os.Getenv("PORT")
	if port == "" {{
		port = "8080"
	}}

	r.Run(":" + port)
}}
"""

        return {
            "go.mod": go_mod,
            "main.go": main_go,
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        project = config["project"]
        app_command = lifecycle_command(
            config,
            "go mod tidy",
            "go run main.go",
        )
        postgres_yaml = postgres_service_yaml(postgres, project, database_url=False)

        return f"""\
name: {project}

services:
  app:
    image: golang:{app.get('go_version', '1.22')}-alpine
    working_dir: /app
    volumes:
      - ./:/app
    command: {app_command}
    ports:
      - "{app['port']}:8080"
    environment:
      - PORT=8080
      - DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}@postgres:5432/{postgres['db']}
    depends_on:
      postgres:
        condition: service_healthy

{postgres_yaml}
"""

    def env_file(self, config: Mapping[str, Any]) -> str:
        postgres = config["services"]["postgres"]
        return f"""\
DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}@localhost:{postgres['port']}/{postgres['db']}
"""

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        app_port = config["services"]["app"]["port"]
        return [
            f"Go Gin API server listening at http://localhost:{app_port}",
            f"PostgreSQL database accessible on 127.0.0.1:{config['services']['postgres']['port']}",
            "Local environment configuration written to .env.devspeed",
        ]


plugin = GoGinPostgresPlugin()
NAME = plugin.name
DESCRIPTION = plugin.description


def default_config(project_name: str) -> dict[str, Any]:
    return plugin.default_config(project_name)


def starter_files(config: Mapping[str, Any]) -> dict[str, str]:
    return plugin.starter_files(config)


def compose_yaml(config: Mapping[str, Any]) -> str:
    return plugin.compose_yaml(config)


def env_file(config: Mapping[str, Any]) -> str:
    return plugin.env_file(config)


def post_up_hints(config: Mapping[str, Any]) -> list[str]:
    return plugin.post_up_hints(config)
