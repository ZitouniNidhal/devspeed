# Backlog

Priority order reflects the current audit findings and the Phase 1 gate.

| ID | Severity | Effort | Status | Summary |
| --- | --- | --- | --- | --- |
| DEV-001 | High | S | Todo | Fix repository hygiene: `.gitignore` omissions, remove committed `devspeed.egg-info/`, and stop tracking cache/build artifacts. |
| DEV-002 | High | S | Todo | Establish Python support policy: support Python 3.10+ and update metadata/CI to match. |
| DEV-003 | High | M | Todo | Restore CI quality gate health: Black formatting, mypy configuration, and typed YAML stubs. |
| DEV-004 | High | M | Todo | Make `devspeed.yaml` validation contract explicit and backward-compatible; add a clear versioning strategy. |
| DEV-005 | Medium | M | Todo | Add coverage capture and a real baseline in CI so metrics are recorded and tracked over time. |
| DEV-006 | Medium | S | Todo | Clarify public docs and examples around generated files, `.env.example`, and safe local-only credentials. |
| DEV-007 | Medium | M | Todo | Create a maintained release + security posture baseline (CONTRIBUTING, SECURITY, release docs, workflow review). |
| DEV-008 | Low | S | Todo | Review integration test coverage beyond current mocked CLI path and add stack conformance checks. |
| DEV-009 | Low | S | Done | Add stronger CI/CD actions: coverage uploads, packaging/build checks, and dependency-audit stages to the primary workflow. |
| DEV-010 | Low | S | Todo | Merge or retire redundant workflow files (`lint.yml`, `test.yml`, `publish.yml`, `nightly.yml`) once the main pipeline is accepted and the repo hygiene baseline is fixed. |
