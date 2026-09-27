## Summary

<!-- What does this pull request change, and why? -->

## Related issue

<!-- Link an issue with `Fixes #123`, `Closes #123`, or `Related to #123`. -->

## User impact

<!-- Describe the behavior before and after this change. Include CLI or config
     examples when the change is user-facing. -->

## Implementation notes

<!-- Call out important design choices, compatibility considerations, and
     anything reviewers should inspect carefully. -->

## Tests added or updated

- [ ] Unit tests
- [ ] Plugin contract tests
- [ ] CLI integration tests with Docker mocked
- [ ] Docker-backed integration tests, if applicable
- [ ] Manual verification on Linux
- [ ] Manual verification on macOS
- [ ] Manual verification on Windows

Test commands run:

```text
python -m unittest discover -s tests -v
python -m black --check devspeed tests
python -m ruff check devspeed tests
python -m mypy devspeed --ignore-missing-imports
```

## Documentation

- [ ] README updated
- [ ] CLI reference updated
- [ ] Troubleshooting guidance updated
- [ ] Contributor or plugin documentation updated
- [ ] No documentation change is needed

## Breaking changes

- [ ] This pull request changes a public CLI command, option, configuration key, plugin API, or generated file.
- [ ] Migration instructions are included below.
- [ ] This pull request is backward compatible.

Migration notes:

```text
Describe required migration steps, or write "None".
```

## Security and privacy

- [ ] No credentials, tokens, generated environment files, or private data are included.
- [ ] New network, filesystem, Docker, or subprocess behavior is documented and tested.
- [ ] Security-sensitive behavior has been reviewed.

## Checklist

- [ ] The change is focused and does not include unrelated refactoring.
- [ ] I added tests for new behavior and failure modes.
- [ ] I ran the local quality checks listed above.
- [ ] I reviewed the complete diff for generated files and secrets.
- [ ] I am ready for maintainer review.
