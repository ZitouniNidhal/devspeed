# devspeed roadmap

This roadmap is intentionally public and directional. It describes the work
that helps DevSpeed become a dependable open-source foundation for local
development environments while keeping the core CLI approachable.

Priorities can change as contributors and users teach us more. A roadmap item
is not a promise of a particular release date; an issue or pull request should
be treated as the source of truth for concrete implementation details.

## Now: make the foundation dependable

The current focus is reliability, contributor experience, and a stable plugin
boundary.

### Core quality

- Keep `list`, `init`, `create`, `doctor`, `up`, `down`, `status`, `logs`, and
  `cleanup` predictable across Windows, macOS, and Linux.
- Improve actionable errors for missing Docker, invalid YAML, unavailable ports,
  and failed Compose operations.
- Keep generated Compose and environment output deterministic and safe to inspect.
- Expand unit and mocked integration coverage for every command and supported stack.
- Maintain CI across Python 3.9 through 3.12 and all three major desktop platforms.

### Configuration and generated files

- Continue generating `.env.example` with credentials masked for safe sharing.
- Support configurable `lifecycle.install` and `lifecycle.dev` commands.
- Document the generated files and recommended `.gitignore` entries clearly.
- Add more validation for ports, service settings, and plugin-rendered Compose YAML.

### Plugin foundation

- Stabilize the `StackPlugin` API and compatibility policy.
- Discover built-in and third-party stacks through the `devspeed.stacks` entry-point group.
- Publish a plugin authoring guide and contract test examples.
- Keep legacy function-based stack modules working through compatibility wrappers.

### Contributor experience

- Keep contribution, conduct, issue, and pull request guidance current.
- Label newcomer-friendly work with `good first issue`.
- Prefer small, reviewable changes with tests and documentation.

## Next: expand practical development workflows

These initiatives are planned after the foundation is stable and contributors
have exercised the plugin API.

### More maintained stacks

Prioritize stacks with clear local development demand, strong Docker images, and
maintainable starter projects:

- Next.js with PostgreSQL
- Vue or Nuxt with PostgreSQL
- Rails with PostgreSQL and Redis
- Spring Boot with PostgreSQL
- Go with Gin and PostgreSQL
- Laravel with PostgreSQL and Redis
- .NET with PostgreSQL
- Jupyter with PostgreSQL and MinIO
- MongoDB application stacks
- RabbitMQ application stacks
- Elasticsearch and Kibana development stacks

Every maintained stack should provide configurable ports, health checks,
seed-data guidance, hot reload where supported, useful starter files, and
contract tests.

### Local dashboard

- Add a local `devspeed dashboard` command.
- Show service status, logs, port mappings, and basic resource usage.
- Provide restart and stop actions with confirmation for destructive operations.
- Stream logs over WebSockets without exposing the local Docker socket remotely.

### Developer productivity

- Generate OpenAPI stubs or Postman/Insomnia collections for API stacks.
- Add built-in seed fixtures where a stack can provide safe deterministic data.
- Add `devspeed doctor --fix` for safe repairs such as regenerating missing
  outputs or identifying stale Compose files.
- Add cold-start benchmarks so stack improvements can be measured rather than
  guessed.

### Local-install mode

Design an opt-in mode for teams that cannot use Docker:

- Reuse the same `devspeed.yaml` contract.
- Detect required host tools before changing files.
- Create isolated Python or Node environments where appropriate.
- Start only services that can be safely managed locally.
- Explain clearly when a dependency still requires Docker or an external service.

## Later: build the wider ecosystem

These are longer-term ideas that should follow real usage and strong security
boundaries.

### Team and remote environments

- Share a sanitized environment snapshot with explicit user confirmation.
- Connect to a remote Docker host or lightweight development VM.
- Sync approved stack templates from an organization-managed catalog.
- Support policy checks for permitted images, ports, and credentials.

### Distribution

- Publish signed semantic-versioned releases to PyPI.
- Automate changelogs and release notes.
- Provide Homebrew, Scoop, and WinGet manifests.
- Produce standalone binaries for users without Python.
- Publish a container image for CI and remote automation use cases.

### Documentation and governance

- Build a searchable documentation site with generated CLI reference pages.
- Publish architecture decision records for major design choices.
- Maintain a discoverable plugin catalog with compatibility metadata.
- Establish regular community discussions and a transparent release process.
- Define support expectations for core features versus community plugins.

### Observability and privacy

- Consider opt-in, anonymized usage telemetry only after governance is defined.
- Make collection visible, documented, and disabled by default.
- Never collect project source, credentials, environment values, or container logs.
- Provide a simple command to inspect and disable any telemetry configuration.

## How to participate

The best way to influence the roadmap is to open a focused issue with a user
story, proposed behavior, and acceptance criteria. Stack requests belong in the
new-stack issue template. Implementation work should include tests and docs.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and review expectations.
