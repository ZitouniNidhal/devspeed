# Program roadmap

## Current status summary

- Phase 1 audit is complete for the current session: repo structure, CI config, tests, and core modules were reviewed without production-code changes.
- The codebase has a working baseline test suite (`52 passed`), but CI hygiene is not yet green because Black and mypy are failing in the current state.
- The strongest immediate priorities are repo hygiene, Python support policy, and CI/tooling cleanup before any larger feature work.
- The public `devspeed.yaml` contract is currently retained; no schema changes are proposed in this audit.
- The next gate is maintainer approval to move from audit to Phase 1 remediation.

## Phase status

| Phase | Status | Notes |
| --- | --- | --- |
| Phase 1 audit | Done | Full repo read, config review, baseline validation, and backlog creation completed. |
| Phase 1 foundation | Blocked | Requires approval before making repo hygiene and CI fixes. |
| Phase 2 config contract | Todo | Schema validation and `devspeed validate` work begins after hygiene and compatibility baseline. |
| Phase 3 roadmap features | Todo | Deferred until the core contract and toolchain are stabilized. |
| Phase 4 DX and profiles | Todo | Deferred until after reliability and config work. |
| Phase 5 production release | Todo | Not in scope for the current audit. |

## Phase 1 gate (planned)

- Adopt a supported Python floor and document it.
- Remove generated artifacts from version control and tighten `.gitignore`.
- Restore green ruff/Black/mypy/pytest in CI.
- Keep `devspeed.yaml` backward-compatible and version-aware for any future schema changes.

## Planned next actions

1. Fix repository hygiene (ignore caches and generated artifacts; remove committed `devspeed.egg-info` from version control).
2. Set the Python support policy to 3.10+ and update metadata/docs accordingly.
3. Make lint/format/type checks pass in the project baseline.
4. Re-run CI-focused checks and lock the metrics baseline.
5. Only then start Phase 1 implementation work.
