# Metrics baseline

## Observed at audit time

- Test count: 52 passed (`pytest -q`)
- Coverage: not measured; no coverage configuration is present yet
- CLI startup time: 362 ms (`devspeed --help` from the project venv)
- Ruff status: passed (`python -m ruff check .`)
- Black status: fails with 4 files needing reformat
- Mypy status: fails with 12 errors, including missing `yaml` stubs and Liskov override mismatches
- Stack count: 7 built-in stacks
- Supported platforms: Linux, macOS, Windows (as declared by CI matrix)
- Supported Python versions in CI: 3.10, 3.11, 3.12

## Current interpretation

The project has a good baseline test suite, but it is not yet operating under a full and consistent quality gate. In particular, formatting and static typing are currently red even though the functional tests pass. The next phase should lock a formal support floor and restore a green CI baseline before feature work resumes.
