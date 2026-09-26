# devspeed

A single CLI that spins up a local dev environment (app + databases) from one
config file, backed by Docker Compose so nothing touches your machine's global
installs.

```bash
pip install -e .
devspeed list
devspeed init node-postgres-redis --name myapp
devspeed up
# ...work...
devspeed down       # stop, keep data
devspeed cleanup    # stop, wipe volumes + generated files
```

## How it works

- `devspeed init <stack>` writes a `devspeed.yaml` describing your project
  (ports, service names, credentials) for the chosen stack.
- `devspeed up` reads that file, generates a `docker-compose.devspeed.yml` and
  `.env.devspeed`, and runs `docker compose up -d`.
- `devspeed down` / `devspeed cleanup` tear things down.

Generated files (`docker-compose.devspeed.yml`, `.env.devspeed`) are meant to
be gitignored — `devspeed.yaml` is the thing you commit and share with your
team.

## Available stacks (MVP)

- `node-postgres-redis` — Node/Express + Postgres + Redis
- `fastapi-postgres` — Python FastAPI + Postgres

## Adding a new stack

Add a module to `devspeed/stacks/` exposing `NAME`, `DESCRIPTION`,
`default_config()`, `compose_yaml()`, `env_file()`, and `post_up_hints()`,
then register it in `devspeed/stacks/__init__.py`. See
`node_postgres_redis.py` for the shape.

## What's deliberately NOT in this MVP

- No bare-metal (non-Docker) install path yet — this version is
  container-only. A local-install mode is a bigger, riskier piece of work
  (cross-platform package managers, PATH management) and shouldn't block
  getting the container path in front of users first.
- No interactive wizard — `init` takes a stack name directly.
- No auto-detection of "what stack is this repo" — you say what you want.

## Requirements

- Python 3.9+
- Docker with Compose v2 (`docker compose ...`, not the old `docker-compose`)
