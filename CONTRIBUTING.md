# Contributing to devspeed

Thank you for helping make local development easier to reproduce. DevSpeed is a
small tool with a deliberately readable core, so contributions should improve
clarity for both first-time users and people maintaining a project at scale.

## Development setup

### 1. Clone the repository

```bash
git clone https://github.com/OWNER/devspeed.git
cd devspeed
```

Replace `OWNER` with the canonical GitHub organization or user once the public
repository is created.

### 2. Create an isolated Python environment

Python 3.9 through 3.12 are supported in CI.

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install the project and development tools

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The development extra contains the formatter, linter, and type checker used by
continuous integration.

### 4. Run the test suite

```bash
python -m unittest discover -s tests -v
```

Tests should pass without Docker. Docker-dependent behavior is mocked in the
unit suite; integration tests that require a running daemon must be clearly
marked and documented when they are added.

### 5. Run quality checks

```bash
python -m black --check devspeed tests
python -m ruff check devspeed tests
python -m mypy devspeed --ignore-missing-imports
python -m compileall -q devspeed
```

Before committing a formatting change, run:

```bash
python -m black devspeed tests
```

## Coding standards

### Formatting

- Use Black with the repository configuration.
- Keep lines within the configured 100-character limit where practical.
- Use four spaces and UTF-8 source files.
- Avoid unrelated formatting churn in a focused pull request.

### Type hints

- Add type hints to public functions, methods, and meaningful internal helpers.
- Prefer precise collection types such as `dict[str, Any]`, `Mapping[str, Any]`,
  and `list[str]`.
- Keep Python 3.9 compatibility; use `Optional` and `Union` where required by
  the supported interpreter range.
- Do not silence type errors broadly. If a narrow ignore is necessary, explain
  why beside the ignore.

### Docstrings

Public classes and functions should have concise Google-style docstrings that
explain purpose, arguments, return values, raised exceptions, and non-obvious
side effects. Do not add documentation that merely repeats a variable name.

### Behavior and compatibility

- Preserve existing CLI commands and configuration keys unless a breaking
  change is explicitly approved.
- Prefer actionable errors over raw tracebacks for user-facing paths.
- Keep generated files deterministic so changes can be reviewed and tested.
- Never overwrite a user's application file silently.
- Avoid network access in unit tests; mock external services and subprocesses.
- Do not commit generated Compose files, local environment files, credentials,
  virtual environments, or tool caches.

## How to add a new stack

A stack is a module in `devspeed/stacks/` that follows the existing public
shape:

- `NAME: str`
- `DESCRIPTION: str`
- `default_config(project_name: str) -> dict`
- `starter_files(config: dict) -> dict[str, str]`
- `compose_yaml(config: dict) -> str`
- `env_file(config: dict) -> str`
- `post_up_hints(config: dict) -> list[str]`

Newer stacks should implement the `StackPlugin` class in
`devspeed/plugins/base.py` and export a module-level `plugin` instance. The
module-level functions below are retained as compatibility wrappers for older
stack integrations.

### Example: `flask-postgres`

Create `devspeed/stacks/flask_postgres.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from devspeed.plugins.base import StackPlugin
from .common import lifecycle_command, postgres_service_yaml


class FlaskPostgresPlugin(StackPlugin):
    """Provide a hot-reloading Flask application with PostgreSQL."""

    @property
    def name(self) -> str:
        """Return the stable configuration identifier."""
        return "flask-postgres"

    @property
    def description(self) -> str:
        """Return the description shown by ``devspeed list``."""
        return "Python Flask API + Postgres"

    def default_config(self, project_name: str) -> dict[str, Any]:
        """Return reproducible defaults for a Flask project."""
        return {
            "project": project_name,
            "stack": self.name,
            "lifecycle": {
                "install": "pip install --no-cache-dir -r requirements.txt",
                "dev": "flask --app app run --host 0.0.0.0 --port 5000 --debug",
            },
            "services": {
                "app": {"port": 5000, "python_version": "3.12"},
                "postgres": {
                    "port": 5432,
                    "db": project_name.replace("-", "_"),
                    "user": "devspeed",
                    "password": "devspeed",
                },
            },
        }

    def starter_files(self, config: Mapping[str, Any]) -> dict[str, str]:
        """Return starter files for a minimal Flask API."""
        return {
            "requirements.txt": "Flask>=3.1,<4\npsycopg[binary]>=3.2,<4\n",
            "app.py": '''from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def read_root():
    return jsonify(message="Your DevSpeed app is running")
''',
        }

    def compose_yaml(self, config: Mapping[str, Any]) -> str:
        """Render the application and PostgreSQL Compose services."""
        services = config["services"]
        app = services["app"]
        postgres = services["postgres"]
        project = config["project"]
        command = lifecycle_command(
            config,
            "pip install --no-cache-dir -r requirements.txt",
            f"flask --app app run --host 0.0.0.0 --port {app['port']} --debug",
        )
        return f"""\
name: {project}

services:
  app:
    image: python:{app['python_version']}-slim
    working_dir: /app
    volumes:
      - ./:/app
    command: {command}
    ports:
      - "{app['port']}:{app['port']}"
    environment:
      - DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}@postgres:5432/{postgres['db']}
    depends_on:
      postgres:
        condition: service_healthy

{postgres_service_yaml(postgres, project)}
"""

    def env_file(self, config: Mapping[str, Any]) -> str:
        """Return the host-side PostgreSQL connection URL."""
        postgres = config["services"]["postgres"]
        return (
            f"DATABASE_URL=postgresql://{postgres['user']}:{postgres['password']}"
            f"@localhost:{postgres['port']}/{postgres['db']}\n"
        )

    def post_up_hints(self, config: Mapping[str, Any]) -> list[str]:
        """Return useful notes after the stack starts."""
        port = config["services"]["app"]["port"]
        return [
            "App container installs requirements.txt and runs Flask in debug mode.",
            f"API should be reachable at http://localhost:{port} once dependencies finish installing.",
            "Make sure app.py exposes a Flask app named 'app'.",
        ]


plugin = FlaskPostgresPlugin()
```

Register the plugin in `devspeed/stacks/__init__.py` if it is a built-in stack,
then add it to the entry-point table in `pyproject.toml` when the project is
packaged:

```toml
[project.entry-points."devspeed.stacks"]
flask-postgres = "devspeed.stacks.flask_postgres:plugin"
```

### Stack checklist

Before opening a pull request for a stack:

- Use a stable lowercase `NAME` with hyphens.
- Provide safe, documented default ports and versions.
- Include health checks for stateful dependencies.
- Include restart policies through the shared generator path.
- Include hot reload where the framework supports it.
- Make starter files runnable from a clean temporary directory.
- Ensure existing project files are never overwritten.
- Add tests for default configuration, Compose rendering, environment output,
  starter files, and invalid configuration.
- Add the stack to the README catalog and roadmap if appropriate.

## Pull request guidelines

Keep pull requests small and focused. A good PR should explain the user problem,
the chosen solution, and how it was verified.

Before opening a PR:

1. Rebase or update from the current default branch.
2. Run the full test suite.
3. Run Black, Ruff, mypy, and compile checks locally.
4. Review the diff for generated files, credentials, and unrelated changes.
5. Update documentation when user-visible behavior changes.
6. Add a migration note for breaking CLI or configuration changes.

Every behavior change should include tests. Documentation-only changes may omit
unit tests but should include a clear manual verification note.

CI runs on every push and pull request across Python 3.9 through 3.12 and
Ubuntu, Windows, and macOS. It installs the package, checks formatting, runs
Ruff, runs mypy, compiles the package, and executes the test suite.

## Issue triage and labels

Maintainers review new issues regularly and apply labels based on scope:

- `bug`: confirmed incorrect behavior.
- `documentation`: missing, misleading, or unclear documentation.
- `enhancement`: improvement to existing behavior.
- `new-stack`: request or work for a stack template.
- `plugin`: extension API or third-party integration.
- `good first issue`: scoped work suitable for a new contributor.
- `help wanted`: useful work where community assistance is welcome.
- `needs-reproduction`: not enough information to reproduce the report.
- `blocked`: dependent on an external decision or upstream change.

Triage normally follows this sequence:

1. Confirm that the report applies to the current default branch.
2. Request a minimal reproduction when behavior cannot be reproduced.
3. Identify severity, affected platforms, and whether data can be lost.
4. Assign labels and a milestone when the scope is understood.
5. Link duplicate issues and close them with a pointer to the canonical issue.
6. Convert accepted roadmap work into a focused issue with acceptance criteria.

Security vulnerabilities should not be posted publicly. Use the repository's
private security reporting channel when it is enabled, or contact the
maintainers through the address published in the GitHub security policy.

## Code review expectations

Reviewers focus on correctness, compatibility, tests, security, and user
clarity. Review comments should be specific and explain the reason for a
requested change. Contributors are encouraged to ask questions and revise
incrementally; a review is a collaboration, not a gatekeeping exercise.

## License

By contributing, you agree that your contribution will be licensed under the
MIT License used by this project.
