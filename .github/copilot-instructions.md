# Shared Goals Instance Agent Instructions

This repository implements the Shared Goals platform instance. The PRD repository remains the source of truth for product scope, acceptance criteria, and implementation contract.

## Source Documents

- PRD: https://github.com/shared-goals/prd/blob/main/README.md
- Acceptance spec: https://github.com/shared-goals/prd/blob/main/ACCEPTANCE.md
- Backend contract: https://github.com/shared-goals/prd/blob/main/IMPLEMENTATION.md

## Development Principles

- Follow KISS, DRY, and YAGNI.
- Use TDD: write or update HTTP-level acceptance tests before implementation.
- Use Makefile targets for validation and local runs. Prefer `make test TEST=...` for the focused red/green loop, `make acceptance` for HTTP acceptance coverage, `make lint` for Ruff checks, `make check` before commit, and `make dev` for the local API server.
- Keep MVP behavior agent-first and JSON REST-first under `/api/v1`.
- Do not add messenger-specific flows, proactive Goal Discovery, leaderboards, streaks, reminders, or transactional consumer UI unless the PRD/acceptance spec changes first.

## Hindsight Memory Workflow

For Shared Goals development tasks, use Hindsight memory when configured and available.

Before acting:
- Recall project memory with tags `project:sg` and `scope:dev`.
- Verify recalled facts against repository files before changing behavior.

After accepted decisions or status changes:
- Retain one concise durable memory with tags `project:sg` and `scope:dev`.
- Put kind, phase, status, source file, commit hash, PR link, and rationale in memory content or context, not tags.

Never retain secrets, credentials, raw private notes, routine logs, telemetry, or noisy terminal output.