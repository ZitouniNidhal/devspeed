from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.stacks.common import lifecycle_command, postgres_service_yaml


class SpringBootPostgresStack:
    """Spring Boot application with a PostgreSQL database."""
    name = "spring-boot-postgres"
    description = "Spring Boot application and PostgreSQL"

    def default_config(self, project: str) -> Mapping[str, Any]:
        return {
            "project": project,
            "stack": self.name,
            "services": {
                "app": {
                    "port": 8080,
                    "java_version": "21",
                },
                "postgres": {
                    "port": 5432,
                    "db": "springdb",
                    "user": "springuser",
                    "password": "springpassword",
                },
            },
            "lifecycle": {
                "install": "./mvnw install -DskipTests",
                "dev": "./mvnw spring-boot:run",
            },
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        project = config["project"]
        app = config["services"]["app"]
        postgres = config["services"]["postgres"]

        return f"""
version: "3.8"
services:
  app:
    image: eclipse-temurin:21-jdk-alpine
    ports:
      - "{app['port']}:8080"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/{postgres['db']}
      - SPRING_DATASOURCE_USERNAME={postgres['user']}
      - SPRING_DATASOURCE_PASSWORD={postgres['password']}
    depends_on:
      postgres:
        condition: service_healthy
    command: {lifecycle_command(config, "./mvnw install -DskipTests", "./mvnw spring-boot:run")}

{postgres_service_yaml(postgres, project, database_url=True)}
"""

    def env_file(self, config: Mapping[str, Any]) -> str:
        postgres = config["services"]["postgres"]
        return (
            f"SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/{postgres['db']}\n"
            f"SPRING_DATASOURCE_USERNAME={postgres['user']}\n"
            f"SPRING_DATASOURCE_PASSWORD={postgres['password']}\n"
        )

    def starter_files(self, config: Mapping[str, Any]) -> Mapping[str, str]:
        return {}

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        return [
            "Access your app at http://localhost:8080",
            "Database is available at localhost:5432",
            "Check logs with 'devspeed logs app'",
        ]
