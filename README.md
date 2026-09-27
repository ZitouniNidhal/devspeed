# ⚡ devspeed

**Spin up a professional local development environment in seconds.**

[![Build](https://img.shields.io/github/actions/workflow/status/OWNER/devspeed/ci.yml?branch=main&label=build)](https://github.com/OWNER/devspeed/actions)
[![PyPI](https://img.shields.io/pypi/v/devspeed.svg)](https://pypi.org/project/devspeed/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/devspeed.svg)](https://pypi.org/project/devspeed/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

`devspeed` is a high-performance CLI tool that transforms a simple `devspeed.yaml` into a fully operational, reproducible Docker Compose environment. It eliminates the "it works on my machine" struggle by automating starter files, database wiring, and connection URL generation.

**Stop debugging your environment. Start building your app.**

```text
devspeed.yaml  ➔  devspeed up  ➔  🚀 Ready-to-code Stack
```

## ✨ Why devspeed?

Docker Compose is powerful, but the "last mile" of onboarding is always painful. Teams waste hours on ports, health checks, and manual `.env` updates. 

`devspeed` provides the **missing abstraction layer**:
- **Zero-Config Onboarding**: New developers run one command and get a working stack.
- **Standardized Contracts**: Commit a single YAML recipe that defines the team's infrastructure.
- **Smart Defaults**: Built-in templates for the most common stacks (FastAPI, Django, Node, etc.).
- **Editor Agnostic**: Works perfectly whether you use VS Code, PyCharm, Vim, or a plain terminal.

## 📊 devspeed vs. The Alternatives

| Capability | ⚡ devspeed | Plain Docker Compose | VS Code Dev Containers |
| :--- | :---: | :---: | :---: |
| **Instant Starters** | ✅ Built-in Templates | ❌ Manual Setup | ⚠️ Custom Definitions |
| **Team Sync** | ✅ Single YAML Contract | ⚠️ Compose + Wiki | ⚠️ `.devcontainer` |
| **Auto-Wiring** | ✅ Generated URLs/Env | ❌ Manual `.env` | ⚠️ Partial |
| **Editor Lock-in** | ❌ None | ❌ None | ✅ VS Code Optimized |
| **Onboarding** | 🚀 Seconds | 🐢 Hours | 🚶 Minutes |

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **Docker Desktop** (with Compose v2)

### Installation
```bash
pip install devspeed
```

### Get Running in 30 Seconds
```bash
# 1. Interactively choose a stack (e.g., FastAPI + Postgres)
devspeed create

# 2. Verify your system is ready
devspeed doctor

# 3. Launch the environment
devspeed up
```

### Pro Workflow (Scriptable)
```bash
devspeed init fastapi-postgres --name my-awesome-api
devspeed up
```

## 🛠️ Command Reference

| Command | Description |
| :--- | :--- |
| `devspeed list` | Show all available stack templates |
| `devspeed init <stack>` | Create a `devspeed.yaml` for a specific stack |
| `devspeed up` | Generate files and start containers |
| `devspeed doctor` | Health check for Docker and configuration |
| `devspeed down` | Stop containers (keeps data) |
| `devspeed cleanup` | Wipe everything (containers, volumes, generated files) |

## 🤝 Contributing

We love contributions! Whether it's a new stack template, a bug fix, or documentation improvement, please check out our [CONTRIBUTING.md](CONTRIBUTING.md).

---
*Built for developers who value their time.*
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
