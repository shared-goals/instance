# Shared Goals Instance

Shared Goals platform instance: FastAPI backend, SQLite persistence, read-only web UI later, and JSON REST API for agents.

The PRD source of truth lives in `shared-goals/prd`. Start implementation from the acceptance scenarios and backend contract there.

## Development

Use the Makefile targets for the local development flow:

```bash
make acceptance
make lint
make test
make check
```

For a focused TDD loop, pass a specific file or test:

```bash
make test TEST=tests/acceptance/test_agent_goal_flow.py
```

Run the local API:

```bash
make dev
```

TDD flow: write or update the HTTP acceptance test first, run the focused target and see it fail, implement the smallest behavior, rerun the same target, then run `make check` before committing. Use `make format` for mechanical Python formatting.

## MVP Scope

The first implementation slice supports agent-facing goal creation and simple catalog search under `/api/v1`. Additional behavior should land through HTTP-level acceptance tests first.
