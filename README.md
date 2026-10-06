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

## � Available Stacks

| Stack | Includes |
| :--- | :--- |
| `node-postgres-redis` | Node.js / Express API, PostgreSQL, and Redis |
| `fastapi-postgres` | FastAPI application and PostgreSQL |
| `django-postgres` | Django web application and PostgreSQL |
| `flask-postgres` | Flask API and PostgreSQL |
| `nextjs-postgres` | Next.js App Router fullstack app and PostgreSQL |
| `go-gin-postgres` | Go Gin REST API and PostgreSQL |
| `spring-boot-postgres` | Spring Boot application and PostgreSQL |

## �🛠️ Command Reference

| Command | Description |
| :--- | :--- |
| `devspeed list` | Show all available stack templates |
| `devspeed init <stack>` | Create a `devspeed.yaml` for a specific stack |
| `devspeed create` | Interactively choose and initialize a stack |
| `devspeed up` | Generate files and start containers |
| `devspeed doctor` | Health check for Docker and configuration |
| `devspeed down` | Stop containers (keeps data) |
| `devspeed cleanup` | Wipe everything (containers, volumes, generated files) |

## 🧩 Advanced Capabilities

`devspeed` isn't just for starters; it's a framework for environment automation.

### 🔌 Plugin System
Want a custom stack for your company's internal architecture? You can distribute your own stacks as Python plugins. 
- **Custom Stacks:** Define your own services, volumes, and environment variables.
- **Lifecycle Hooks:** Automate setup tasks (like database migrations) via `lifecycle.install` and `lifecycle.dev`.
- **Extensibility:** Third-party stacks can be discovered automatically via Python entry points.

### ⚙️ Customization
The `devspeed.yaml` contract allows you to override defaults:
- **Port Mapping:** Change default ports to avoid conflicts.
- **Service Tuning:** Adjust resource limits or restart policies.
- **Environment Variables:** Inject project-specific secrets and configs.

## 🗺️ Roadmap & Future

We are building the future of local development. Check out our [ROADMAP.md](ROADMAP.md) for the full vision, including:
- **Local Dashboard:** A visual interface to manage your services, logs, and resource usage.
- **Seed Data:** Built-in fixtures to populate your DBs instantly.
- **Local-Install Mode:** Support for environments without Docker.
- **Expanded Stack Library:** Adding Spring Boot, .NET, and more.

## 🤝 Contributing

We love contributions! Whether it's a new stack template, a bug fix, or documentation improvement, please check out our [CONTRIBUTING.md](CONTRIBUTING.md).

**Ways to help:**
- 🌟 **Star the repo** to show your support.
- 🐛 **Report bugs** or request features in the Issues tab.
- 🛠️ **Build a plugin** and share your custom stack with the community.
- 📝 **Improve docs** to help other developers get started faster.

## 📖 Deep Dive & Guides

### Team Workflow
`devspeed.yaml` is the source of truth. Commit it to your repo so every teammate uses the same environment.

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

**Generated Files (Add to `.gitignore`):**
- `docker-compose.devspeed.yml`
- `.env.devspeed`
- `.env.example` (Can be committed as a safe template)

### Example Configuration
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
`lifecycle.install` and `lifecycle.dev` are optional. They replace the stack's default commands inside the app container.

### Full CLI Reference

| Command | Purpose |
| :--- | :--- |
| `devspeed version` | Show devspeed CLI version |
| `devspeed list` | Browse available stack templates |
| `devspeed init <stack>` | Create a shareable `devspeed.yaml` |
| `devspeed create` | Choose a stack with an interactive wizard |
| `devspeed validate` | Validate `devspeed.yaml` schema and stack configuration |
| `devspeed doctor` | Check configuration and Docker before starting |
| `devspeed doctor --fix` | Auto-repair safe missing setup items (e.g. `.env.example`) |
| `devspeed up` | Generate files and start services |
| `devspeed up --dry-run` | Preview generated files without starting Docker |
| `devspeed down` | Stop services without deleting data |
| `devspeed status` | Show the status of every service |
| `devspeed logs [service]` | Inspect logs, optionally for one service |
| `devspeed export` | Export standalone `docker-compose.yml` and `.env` files |
| `devspeed cleanup` | Stop services, remove volumes, and remove generated outputs |

## 🛠️ Troubleshooting

### Docker is not detected
Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), start it, and verify with `docker compose version`. Then run `devspeed doctor` again.

### A port is already in use
Change the affected host `port` in `devspeed.yaml`, stop any old process using the port, and run `devspeed up` again.

### YAML is invalid
Check indentation and quote values containing `:` or special characters. Run `devspeed doctor` to see the configuration area that needs attention.

### Containers start but the app is unhealthy
Run `devspeed logs app` and verify that your lifecycle commands and expected starter files match the selected stack.

---
*Built for developers who value their time.*

## License
`devspeed` is released under the MIT License. See [LICENSE](LICENSE).
