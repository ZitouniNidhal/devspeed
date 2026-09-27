# Plugin Authoring

A stack plugin is a Python package that exports a `StackPlugin` instance through
Python entry points.

## Minimal plugin

```python
from devspeed import StackPlugin


class AcmeStack(StackPlugin):
    name = "acme-postgres"
    description = "Acme service with Postgres"
    api_version = "1.0"

    def default_config(self, project_name):
        return {"project": project_name, "stack": self.name, "services": {}}

    def compose_yaml(self, config):
        return "services: {}"

    def env_file(self, config):
        return ""

    def post_up_hints(self, config):
        return []


plugin = AcmeStack()
```

## Packaging

Use a package name such as `devspeed-stack-acme` and declare the entry point in
`pyproject.toml`:

```toml
[project]
name = "devspeed-stack-acme"
dependencies = ["devspeed>=0.1,<2"]

[project.entry-points."devspeed.stacks"]
acme-postgres = "acme_devspeed:plugin"
```

After installation, `devspeed list` discovers the plugin without a source change.
The entry-point key is a distribution identifier; `StackPlugin.name` is the
stable value users put in `devspeed.yaml`. They should normally match.

## Compatibility rules

- Use the same major `api_version` as the supported DevSpeed release.
- Keep `name` stable once published; renaming it breaks existing config files.
- Return JSON/YAML-safe values from `default_config`.
- Never write outside the project directory from plugin rendering methods.
- Add contract tests for Compose parsing, starter files, and clean-directory setup.
