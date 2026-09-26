# devspeed

**The fastest way to make a local development environment reproducible.**

New project setup should take one minute, not one afternoon. `devspeed` turns a
small, shareable YAML file into a ready-to-run Docker Compose environment for
your app and its dependencies.

```text
devspeed.yaml  ->  devspeed up  ->  app + databases + useful connection URLs
```

No global installs. No copy-pasted Compose files. No "works on my machine"
setup ritual.

## Quick start

Requirements: Python 3.9+ and Docker Desktop with Compose v2.

```bash
pip install -e .
devspeed create
devspeed doctor
devspeed up
```

Prefer explicit, scriptable setup? Use `devspeed init <stack>` instead:

```bash
devspeed init node-postgres-redis --name my-api
```

Your project now has a `devspeed.yaml` that can be committed to git. Generated
runtime files are kept separate:

```bash
devspeed down       # stop services, keep database data
devspeed cleanup    # stop services, remove volumes and generated files
```

### Windows PowerShell

If PowerShell says `devspeed` is not recognized after installation, open a new
terminal so it reloads your Python Scripts path. You can also run the launcher
directly:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\devspeed.exe" list
```

Run `devspeed init <stack>` once in the project folder before `up`, `status`, or
`logs`; those commands read the generated `devspeed.yaml` and Compose file.

## What you get

- **One config file:** teammates get the same ports, services, and credentials.
- **Fast onboarding:** generate a stack in seconds and start it with one command.
- **Isolated dependencies:** databases and caches run in containers, not in a
  developer's global machine.
- **Useful defaults:** health checks, hot reload, volumes, and local connection
  URLs are generated for you.
- **Runnable starters:** a fresh `init` creates a tiny app when the expected
  entry files do not exist, without overwriting your work.
- **A clear escape hatch:** the generated Compose file is readable and can be
  inspected or extended when your project grows.

## Available stacks

| Stack | Includes |
| --- | --- |
| `node-postgres-redis` | Node.js / Express app, PostgreSQL, Redis |
| `fastapi-postgres` | FastAPI app, PostgreSQL |
| `django-postgres` | Django web app, PostgreSQL |

List templates from the CLI with `devspeed list`.

## The team workflow

```bash
# One developer creates the project recipe
devspeed init fastapi-postgres --name billing-api

# Everyone reviews and commits this file
git add devspeed.yaml && git commit -m "Add dev environment"

# A new teammate clones the repo and runs
devspeed doctor
devspeed up
devspeed status
```

`devspeed.yaml` is the source of truth. `docker-compose.devspeed.yml` and
`.env.devspeed` are generated locally and should normally be gitignored.

## Example config

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
```

The generated app container mounts your project directory, installs its
dependencies, and runs the stack's development command. Your application can
use the host URLs in `.env.devspeed`; containers use service names such as
`postgres` and `redis`.

Starter files are deliberately small and safe to replace. They give a new
project a working first request immediately, while existing files are always
left untouched.

## CLI reference

| Command | Purpose |
| --- | --- |
| `devspeed list` | Browse available stack templates |
| `devspeed init <stack>` | Create a shareable `devspeed.yaml` |
| `devspeed create` | Choose a stack with an interactive wizard |
| `devspeed doctor` | Check config and Docker before starting |
| `devspeed up` | Generate files and start services |
| `devspeed down` | Stop services without deleting data |
| `devspeed status` | See the status of every service |
| `devspeed logs [service]` | Inspect logs, optionally for one service |
| `devspeed cleanup` | Stop services and remove generated data |

## Roadmap

The first release is intentionally focused on a reliable container workflow.
Next up: more stack templates, configurable lifecycle commands, generated
`.env.example` files, and optional local-install support for teams that cannot
use Docker.

## Add a stack

Create a module in `devspeed/stacks/` exposing `NAME`, `DESCRIPTION`,
`default_config()`, `compose_yaml()`, `env_file()`, and `post_up_hints()`, then
register it in `devspeed/stacks/__init__.py`.

## Contributing

Small, practical improvements are welcome. Keep generated files out of commits,
make stack defaults safe for a fresh clone, and test the CLI from a clean
directory before opening a pull request.

## License

MIT
