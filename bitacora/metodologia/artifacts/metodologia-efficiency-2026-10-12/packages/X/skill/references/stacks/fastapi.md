# FastAPI (Python, AI products)

Only what differs from defaults. General rules: `../engineering.md` (layers, cross-feature contract, API contract).

## Layout
```
app/
  main.py                   app factory, routers, middleware, exception handlers
  core/                     config (pydantic-settings), db (engine, session, Base), errors, logging, security
  features/<feature>/
    __init__.py             public API: the facade functions/classes, listed in __all__
    router.py               presentation: HTTP only (prefix /v1/...)
    dependencies.py         wiring: Depends() providers (session → repository), Annotated aliases for routers
    service.py              application: use cases
    schemas.py              application: pydantic request/response models (DTOs)
    domain.py               domain: pure rules and domain errors (only when there are real invariants)
    repository.py           infrastructure: the only DB queries
    models.py               infrastructure: SQLAlchemy 2.0 models
  ai/                       LLM clients, prompts, tools, evals — isolated behind small interfaces
tests/
migrations/                 Alembic
```
- A grown feature turns a module into a package with the same name (`service.py` → `service/`); the rules hold.
- Routers get repositories and sessions only through `dependencies.py` (they may import services directly);
  services and schemas never import SQLAlchemy; services, repositories and `ai/` never import FastAPI.
- `core/` sits below features, so it never reaches into one: `core/security` only verifies the token and returns
  a principal (id, roles), with no DB access; loading the user goes through the users feature's facade.
- `core/errors.py` imports only the standard library (domain code imports it); the problem+json model lives with
  the exception handlers.
- Another feature is reached only through its `__init__.py` facade; each allowed edge is listed, with its reason,
  in the import-linter independence contract.
- Enforced by `templates/arch/fastapi/importlinter.toml` (import-linter), see `../engineering.md` §9.

## Defaults
- Python ≥ 3.12, type hints everywhere; `uv` for dependencies; ruff (format + lint) and pyright/mypy.
- Pydantic v2 models at every boundary; settings via `pydantic-settings`, validated at startup.
- `async def` only when every call inside is non-blocking (async DB driver, httpx, async SDK). A blocking SDK or
  CPU-bound work goes in plain `def` (threadpool) or a worker process. Never `time.sleep` or `requests` in async code.
- SQLAlchemy 2.0 + Alembic on PostgreSQL (pgvector for embeddings). `MetaData(naming_convention=...)` on `Base`
  for explicit constraint names; Alembic `file_template` gives date + slug file names; downgrades implemented;
  `alembic upgrade head` is a deploy step, never run at startup.
- One transaction per request in the session dependency (`core/db.py`); repositories receive the session.
- Errors: domain exceptions with a stable UPPER_SNAKE `code` (`core/errors.py`); exception handlers in `main.py`
  map them to problem+json with the `request_id`. Services never raise `HTTPException`.
- Pagination: shared `Page[T]` schema (`items`, `next_cursor`) and a `limit` query param clamped to the max.
- Idempotency: a dependency reading `Idempotency-Key` on side-effect POSTs, backed by an idempotency table.
- `BackgroundTasks` only for work you can lose (a log, a cache warm-up). Retries, long jobs, money or LLM cost → a
  queue (Arq/Celery/RQ) or a DB job table with a status endpoint.
- OpenAPI docs disabled outside allowed environments.
- AI layer:
  - Prompts as versioned files/templates, not strings scattered in code.
  - Model IDs and parameters in config. Default to the latest capable Claude models.
  - Every LLM call: timeout, retries with backoff, structured output validated with pydantic, token/cost logging.
  - LLM jobs run in the queue/job table with a status endpoint; stream responses to the UI when useful.
  - A small eval set (input → expected properties) for each prompt that matters; run it when prompts change.
- Never send secrets or unnecessary personal data to model providers.

## Testing
pytest with an async client (httpx `ASGITransport`) and `app.dependency_overrides`, not monkeypatching
internals. Unit-test services and AI post-processing with fake clients; integration tests against a test Postgres
cleaned per test; eval sets for prompts instead of brittle exact-output tests.

## Verify
`ruff check && ruff format --check && pyright && lint-imports && pytest`.
