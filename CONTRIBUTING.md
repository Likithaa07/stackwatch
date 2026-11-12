# Contributing

## Workflow
1. Pick a ticket from the project board and move it to **In Progress**.
2. Branch from `main`, named after the ticket: `SW-<number>-<short-name>` (e.g. `SW-6-simulator-runner`).
3. Commit in small steps. Message format: `type: what changed (SW-<number>)`,
   where type is `feat`, `fix`, `test`, `docs`, `ci` or `chore`.
4. Open a PR using the template, move the ticket to **In review**.
5. Merge only when CI is green and the [Definition of Done](docs/definition-of-done.md) is met.

## Local setup

    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

## Before every push

    ruff check . && ruff format --check .
    python -m pytest -q --cov=simulator --cov=scripts --cov-fail-under=85

## Secrets
Settings live in `.env` (git-ignored). Commit only `.env.example` with fake values.
