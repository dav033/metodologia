# FastAPI (Python, AI products)

Only what differs from defaults. General rules: `../engineering.md`.

## Layout
```
app/
  main.py                   app factory, routers, middleware, exception handlers
  core/                     config (pydantic-settings), logging, errors, security
  features/<feature>/
    router.py               HTTP only
    schemas.py              pydantic request/response models
    service.py              use cases / business rules
    repository.py           DB access
    models.py               ORM models (SQLAlchemy 2.0)
  ai/                       LLM clients, prompts, tools, evals — isolated behind small interfaces
tests/
migrations/                 Alembic
```

## Defaults
- Python ≥ 3.12, type hints everywhere; `uv` for dependencies; ruff (format + lint) and pyright/mypy.
- Pydantic v2 models at every boundary; settings via `pydantic-settings`, validated at startup.
- Async endpoints; SQLAlchemy 2.0 async + Alembic migrations on PostgreSQL (pgvector for embeddings).
- Dependency injection via `Depends` for DB sessions, clients, current user.
- Errors: domain exceptions with a `code` → registered exception handlers map them to HTTP.
- AI layer:
  - Prompts as versioned files/templates, not strings scattered in code.
  - Model IDs and parameters in config. Default to the latest capable Claude models.
  - Every LLM call: timeout, retries with backoff, structured output validated with pydantic, token/cost logging.
  - Long jobs → background tasks/queue with status endpoints; stream responses to the UI when useful.
  - A small eval set (input → expected properties) for each prompt that matters; run it when prompts change.
- Never send secrets or unnecessary personal data to model providers.

## Testing
pytest. Unit-test services and AI post-processing with fake clients; integration tests against a test Postgres;
eval sets for prompts instead of brittle exact-output tests.

## Verify
`ruff check && ruff format --check && pyright && pytest`.
