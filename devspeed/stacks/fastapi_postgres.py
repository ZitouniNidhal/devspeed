NAME = "fastapi-postgres"
DESCRIPTION = "Python FastAPI API + Postgres"


def default_config(project_name: str) -> dict:
    return {
        "project": project_name,
        "stack": NAME,
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


def compose_yaml(config: dict) -> str:
    svc = config["services"]
    app = svc["app"]
    pg = svc["postgres"]
    project = config["project"]

    return f"""\
name: {project}

services:
  app:
    image: python:{app['python_version']}-slim
    working_dir: /app
    volumes:
      - ./:/app
    command: sh -c "pip install --no-cache-dir -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port {app['port']} --reload"
    ports:
      - "{app['port']}:{app['port']}"
    environment:
      - DATABASE_URL=postgresql://{pg['user']}:{pg['password']}@postgres:5432/{pg['db']}
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


def env_file(config: dict) -> str:
    svc = config["services"]
    pg = svc["postgres"]
    return f"""\
DATABASE_URL=postgresql://{pg['user']}:{pg['password']}@localhost:{pg['port']}/{pg['db']}
"""


def post_up_hints(config: dict) -> list[str]:
    app_port = config["services"]["app"]["port"]
    return [
        "App container installs from requirements.txt and runs uvicorn with --reload.",
        f"API should be reachable at http://localhost:{app_port} once dependencies finish installing.",
        "Make sure you have a main.py with a FastAPI 'app' instance at the project root.",
    ]
