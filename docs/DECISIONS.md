# Architecture decisions

## ADR-001: Python support floor is 3.10+

- Status: proposed for adoption
- Date: 2026-10-10

### Decision

Support Python 3.10 and newer, and stop claiming Python 3.9 compatibility.

### Why

- Python 3.9 is end-of-life and no longer a safe baseline for a tool intended for sustained team adoption.
- The repository's CI matrix already targets Python 3.10, 3.11, and 3.12, which indicates the project is already effectively running on 3.10+.
- A single supported lower bound reduces compatibility and testing drift without blocking the tool's practical use.

### Consequences

- The package metadata and docs must explicitly declare `>=3.10` rather than `>=3.9`.
- CI must be aligned to the same floor and validated on every supported version.
- Future changes can rely on modern Python capabilities without maintaining an EOL runtime.

## ADR-002: `devspeed.yaml` remains the public contract and must stay backward-compatible

- Status: accepted
- Date: 2026-10-10

### Decision

Any future schema change must be guarded by a `version` field, migration guidance, and explicit validation errors.

### Why

`devspeed.yaml` is a source-of-truth file that users commit to their repos; breaking it silently would be a high-risk maintenance decision.

### Consequences

- Existing configs should continue to work unless they intentionally opt into a later schema version.
- Future schema changes need docs, a migration path, and strong CLI-level validation.
- The tool should prefer clear errors over silent coercion when invalid config is detected.
