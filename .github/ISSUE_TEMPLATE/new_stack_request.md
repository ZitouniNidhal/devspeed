---
name: New stack request
about: Request a framework, database, or service stack
title: "[Stack]: "
labels: [new-stack]
assignees: []
---

## Stack overview

- Proposed stack name:
- Primary framework or runtime:
- Language and version:
- Database or storage:
- Additional services:
- Suggested Docker images:

## Use case

<!-- What type of application would this stack help someone build? -->

## Why is it needed?

<!-- Explain the audience, current pain, and why an existing stack is not enough. -->

## Expected development workflow

<!-- Describe install, development, test, and reload commands. -->

```text
Install command:
Development command:
Test command:
Reload behavior:
```

## Configuration proposal

```yaml
# Show the devspeed.yaml settings you expect users to configure.
project: example
stack: proposed-stack
services: {}
```

## Service requirements

### Health checks

<!-- Explain how each dependency should be considered ready. -->

### Seed data

<!-- Describe useful starter data or initialization scripts. -->

### Host ports

<!-- List expected ports and whether they must be configurable. -->

## Starter files

<!-- List the files a fresh `devspeed init` should create. -->

## Existing alternatives

<!-- Link to existing stacks, plugins, or related tools. -->

## Checklist

- [ ] I searched existing stacks and issues for duplicates.
- [ ] I described the framework, database, and use case.
- [ ] I identified development and reload commands.
- [ ] I considered health checks and port configuration.
- [ ] I can help test the stack on at least one supported operating system.
