"""Next.js App Router and Postgres stack plugin."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin

from .common import lifecycle_command, postgres_service_yaml


class NextjsPostgresPlugin(StackPlugin):
    """Provide a Next.js App Router fullstack app with Postgres."""

    @property
    def name(self) -> str:
        return "nextjs-postgres"

    @property
    def description(self) -> str:
        return "Next.js App Router fullstack application and PostgreSQL"

    def default_config(self, project_name: str) -> dict[str, Any]:
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {
                "install": "npm install",
                "dev": "npm run dev",
            },
            "services": {
                "app": {"port": 3000, "node_version": "22"},
                "postgres": {
                    "port": 5432,
                    "db": project_name.replace("-", "_"),
                    "user": "devspeed",
                    "password": "devspeed",
                },
            },
        }

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        pkg_json = {
            "name": config["project"],
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
            },
            "dependencies": {
                "next": "^14.2.0",
                "react": "^18.3.0",
                "react-dom": "^18.3.0",
                "pg": "^8.11.0",
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^18.3.0",
                "@types/react-dom": "^18.3.0",
                "typescript": "^5.4.0",
            },
        }

        page_tsx = (
            "export default function Home() {\n"
            "  return (\n"
            "    <main style={{ padding: '2rem', fontFamily: 'sans-serif' }}>\n"
            f"      <h1>⚡ Welcome to {config['project']}</h1>\n"
            "      <p>Powered by Next.js & PostgreSQL via <code>devspeed</code>.</p>\n"
            "    </main>\n"
            "  );\n"
            "}\n"
        )

        next_config = (
            "/** @type {import('next').NextConfig} */\n"
            "const nextConfig = {\n"
            "  reactStrictMode: true,\n"
            "};\n\n"
            "module.exports = nextConfig;\n"
        )

        return {
            "package.json": json.dumps(pkg_json, indent=2) + "\n",
            "app/page.tsx": page_tsx,
            "next.config.js": next_config,
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        project = config["project"]
        app_command = lifecycle_command(
            config,
            "npm install",
            "npm run dev",
        )
        postgres_yaml = postgres_service_yaml(postgres, project, database_url=False)

        return f"""\
name: {project}

services:
  app:
    image: node:{app.get('node_version', '22')}-alpine
    working_dir: /app
    volumes:
      - ./:/app
    command: {app_command}
    ports:
      - "{app['port']}:3000"
    environment:
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
            "Next.js App Router running at http://localhost:" + str(app_port),
            "PostgreSQL listening on 127.0.0.1:" + str(config["services"]["postgres"]["port"]),
            "Local environment variables loaded from .env.devspeed",
        ]


plugin = NextjsPostgresPlugin()
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
