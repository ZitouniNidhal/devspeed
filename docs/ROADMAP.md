# DevSpeed Roadmap

This roadmap is versioned with the project. Estimates assume one maintainer plus
occasional community contributors and are deliberately rough.

## Phase 1: Foundation (4-6 weeks)

**Goal:** make the core extensible without breaking existing projects.

- Stabilize `StackPlugin` API version `1.0`.
- Discover installed plugins through the `devspeed.stacks` entry-point group.
- Keep built-in stacks behind the same registry and add plugin contract tests.
- Add plugin diagnostics, duplicate-name handling, and read-only PyPI catalog lookup.
- Establish semantic versioning, changelog automation, documentation scaffolding,
  and a CI matrix for supported Python versions.

**Exit criteria:** an independently packaged plugin can be installed, discovered,
listed, rendered, and tested without modifying DevSpeed source.

## Phase 2: Growth (2-4 months)

**Goal:** expand useful development workflows around the plugin contract.

- Add 15-20 maintained stacks, each with health checks, seed fixtures, and reload support.
- Add `devspeed dashboard` with a local API, service controls, resource summaries,
  and WebSocket log streaming.
- Generate OpenAPI/Postman artifacts and add `doctor --fix` for safe repairs.
- Add Docker-backed integration tests and cold-start benchmarks for every maintained stack.
- Add opt-in anonymized telemetry with a clear disable switch and no project data.

**Exit criteria:** stack additions are mostly plugin releases, not core changes.

## Phase 3: Ecosystem (3-6 months)

**Goal:** make DevSpeed useful for teams and third-party communities.

- Add signed/shareable environment snapshots and remote Docker host support.
- Add organization-approved stack catalogs and config synchronization.
- Publish PyPI releases, Homebrew/Scoop/WinGet manifests, standalone binaries,
  and a DevSpeed container image.
- Build the full documentation site, plugin catalog, governance process, and
  community contribution pipeline.

**Exit criteria:** teams can operate an approved catalog and plugin authors have
clear discoverability, compatibility, and support paths.

## Compatibility policy

The current function-based stack modules remain supported through an internal
adapter. Existing `devspeed.yaml` files continue to work. Plugin API major
versions are incompatible by policy; minor releases add backwards-compatible
hooks. A future major release may remove the module adapter only after a
published deprecation cycle.
