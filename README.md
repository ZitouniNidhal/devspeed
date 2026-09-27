# devspeed

**Reproducible local development environments in one command.**

[![Build](https://img.shields.io/github/actions/workflow/status/OWNER/devspeed/ci.yml?branch=main&label=build)](https://github.com/OWNER/devspeed/actions)
[![PyPI](https://img.shields.io/pypi/v/devspeed.svg)](https://pypi.org/project/devspeed/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/devspeed.svg)](https://pypi.org/project/devspeed/)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/OWNER/devspeed/main/.github/coverage.json)](https://github.com/OWNER/devspeed)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

`devspeed` turns a small, shareable `devspeed.yaml` file into a reproducible
Docker Compose development environment. It creates starter application files,
starts databases and caches with useful defaults, and prints the connection
values your application needs. New contributors get a working local stack
without copying a wiki page or debugging an afternoon of machine-specific setup.

```text
devspeed.yaml  ->  devspeed up  ->  app + dependencies + connection URLs
```

## Why devspeed?

Docker Compose is powerful but every team ends up rebuilding the same wiring:
ports, health checks, credentials, volumes, hot reload commands, and onboarding
documentation. Dev Containers provide a consistent editor environment, but they
are centered on the editor and often require a separate service definition.
`devspeed` focuses on the smallest useful team contract: commit one readable
YAML recipe, run one CLI command, and get a working application environment on
Linux, macOS, or Windows.

## devspeed compared

| Capability | devspeed | Plain Docker Compose | VS Code Dev Containers |
| --- | --- | --- | --- |
| Fast stack starter | Built-in templates and starter files | Build everything yourself | Usually requires a custom container definition |
| Team configuration | One shareable `devspeed.yaml` | Compose files plus documentation | `devcontainer.json` plus Compose or Dockerfile |
| Service dependencies | Generated databases, caches, health checks, and URLs | Manually maintained | Possible, but not the primary abstraction |
| Editor dependence | None | None | Optimized for VS Code |
| Customization | YAML lifecycle overrides and plugins | Full Compose flexibility | Full container flexibility |
| Best fit | Fast, repeatable local app environments | Mature custom infrastructure | Full editor/container standardization |

## Quick start

Requirements:

- Python 3.9 or newer
- Docker Desktop with Compose v2, or a Docker Engine with `docker compose`

```bash
pip install -e .
devspeed create
devspeed doctor
devspeed up
```

For explicit, scriptable setup:

```bash
devspeed init node-postgres-redis --name my-api
devspeed doctor
devspeed up
```

Inspect generated files without writing or starting Docker:

```bash
devspeed up --dry-run
```

Stop services while preserving database volumes:

```bash
devspeed down
```

Stop services and remove generated runtime files and volumes:

```bash
devspeed cleanup
```

### Windows PowerShell

If PowerShell says `devspeed` is not recognized after installation, open a new
terminal so it reloads your Python Scripts path. You can also invoke the launcher
directly:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\devspeed.exe" list
```

Run `devspeed init <stack>` in the project folder before `up`, `status`, or
`logs`. Those commands read the committed `devspeed.yaml` and generated Compose
file from the current directory.

## What you get

- **One configuration contract:** teammates review and commit the same YAML.
- **Fast onboarding:** create a stack in seconds instead of copying Compose files.
- **Isolated dependencies:** databases and caches run in containers.
- **Useful defaults:** health checks, hot reload, volumes, restart policies, and local URLs.
- **Safe starters:** missing starter files are created without overwriting existing work.
- **Dry runs:** inspect generated Compose and environment files before changing anything.
- **An extension point:** third-party stacks can be distributed as Python plugins.

## Available stacks

| Stack | Includes |
| --- | --- |
| `node-postgres-redis` | Node.js / Express API, PostgreSQL, and Redis |
| `fastapi-postgres` | FastAPI application and PostgreSQL |
| `django-postgres` | Django web application and PostgreSQL |
| `flask-postgres` | Flask API and PostgreSQL |

List templates from the CLI:

```bash
devspeed list
```

## Team workflow

```bash
# Create the project recipe once
devspeed init fastapi-postgres --name billing-api

# Review and commit the source-of-truth configuration
git add devspeed.yaml
git commit -m "Add local development environment"

# Every teammate uses the same workflow
devspeed doctor
devspeed up
devspeed status
devspeed logs app
```

`devspeed.yaml` is the source of truth. The following files are generated
locally and should normally be ignored by Git:

- `docker-compose.devspeed.yml`
- `.env.devspeed`
- `.env.example` can be committed when the team wants a safe template with masked credentials.

## Example configuration

```yaml
project: my-api
stack: node-postgres-redis
services:
  app:
    port: 3000
    node_version: "22"
  postgres:
    port: 5432
    db: my_api
    user: devspeed
    password: devspeed
  redis:
    port: 6379
lifecycle:
  install: npm install
  dev: npm run dev
```

`lifecycle.install` and `lifecycle.dev` are optional. They replace the stack's
default install and development commands inside the app container. Keep commands
short, deterministic, and safe to run repeatedly.

## CLI reference

| Command | Purpose |
| --- | --- |
| `devspeed list` | Browse available stack templates |
| `devspeed init <stack>` | Create a shareable `devspeed.yaml` |
| `devspeed create` | Choose a stack with an interactive wizard |
| `devspeed doctor` | Check configuration and Docker before starting |
| `devspeed up` | Generate files and start services |
| `devspeed up --dry-run` | Preview generated files without starting Docker |
| `devspeed down` | Stop services without deleting data |
| `devspeed status` | Show the status of every service |
| `devspeed logs [service]` | Inspect logs, optionally for one service |
| `devspeed cleanup` | Stop services, remove volumes, and remove generated outputs |

## Troubleshooting

### Docker is not detected

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/),
start it, and verify:

```bash
docker compose version
```

Then run `devspeed doctor` again.

### A port is already in use

Change the affected host `port` in `devspeed.yaml`, stop any old process using
the port, and run `devspeed up` again. The app and dependency ports are host
ports, so they must be unique on your machine.

### YAML is invalid

Check indentation and quote values containing `:` or special characters. Run
`devspeed doctor` to see the configuration area that needs attention.

### Containers start but the app is unhealthy

Run `devspeed logs app` and verify that your lifecycle commands and expected
starter files match the selected stack.

## Plugin ecosystem

Stacks are discovered through the `StackPlugin` API and the
`devspeed.stacks` Python entry-point group. A third-party package can publish a
name such as `devspeed-stack-acme`, export a `plugin` instance, and become
available without modifying DevSpeed source.

See [docs/plugin-authoring.md](docs/plugin-authoring.md) for the package layout
and compatibility rules. Built-in stacks use the same registry as external
plugins.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the public Now / Next / Later roadmap.

## Why contribute?

DevSpeed is intentionally practical: a small improvement to a stack template or
a troubleshooting note can save every new contributor time. Read
[CONTRIBUTING.md](CONTRIBUTING.md) and help by:

- Adding and maintaining a stack template.
- Improving documentation, examples, and onboarding instructions.
- Reporting reproducible bugs with logs and environment details.
- Reviewing pull requests and testing changes on another operating system.

## License

`devspeed` is released under the MIT License. See [LICENSE](LICENSE).
