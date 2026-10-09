# NestJS (API) + PostgreSQL

Only what differs from defaults. General rules: `../engineering.md` (layers, cross-feature contract, API contract).

## Layout
```
src/
  main.ts  app.module.ts
  modules/<feature>/
    <feature>.module.ts
    index.ts                public API: the module, the facade, event types. Nothing else.
    # small feature: flat files
    <feature>.controller.ts  dto/  <feature>.service.ts  <feature>.facade.ts  <feature>.repository.ts  <x>.entity.ts
    # grown feature: same files, moved into layer folders
    presentation/           controllers only (HTTP: DTO in, call service, DTO out)
    application/            services (use cases), the facade other features call, dto/, entity → DTO mappers
    domain/                 pure classes and rules, domain errors, events (only when there are real invariants)
    infrastructure/         repositories (the only DB access), TypeORM entities, external clients
  common/  errors/ filters/ guards/ interceptors/ database/ pagination/ idempotency/
  config/  env.validation.ts, typed config
db/migrations/
```
- Another feature is reached only through its `index.ts`: import its module, inject its facade. A feature's module
  `exports` only the facade, never repositories.
- Services inject concrete repositories; an interface only for a real second implementation.
- Services never import `typeorm`: multi-step writes go through a repository method or the transaction helper in
  `common/database/`.
- Enforced by `templates/arch/nestjs/` (dependency-cruiser + ESLint), see `../engineering.md` §9.

## Defaults
- `strict: true` in tsconfig (including `noImplicitAny`); no `any`.
- Global `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })`.
- Routes under `/v1` (`app.setGlobalPrefix('v1')` or URI versioning).
- Errors: services and domain throw domain errors from `common/errors` (`NotFoundError`, `ConflictError`, …, each
  with a stable UPPER_SNAKE `code`), never `HttpException`. One global filter maps them to problem+json with the
  `request_id`; unknown errors → 500 logged. Controllers don't try/catch to build responses.
- Pagination: a shared `PageQueryDto` (`cursor`, `limit` clamped to the max) and `Page<T>` response
  (`items`, `next_cursor`) in `common/pagination/`.
- Idempotency: an interceptor in `common/idempotency/` on side-effect POSTs, backed by an idempotency table.
- Background work: no un-awaited promises for work that matters. Retries/long/money/LLM cost → BullMQ or a DB
  job table polled by a worker, with a status endpoint. Events after a write: outbox row in the same transaction.
- Config via `@nestjs/config` with validation at startup; documented `.env.example`.
- DB: PostgreSQL + TypeORM (or Prisma if the project uses it). `synchronize: false` and `migrationsRun: false`;
  migrations run as a deploy step. A `NamingStrategy` gives explicit constraint names and snake_case columns.
  Index foreign keys and frequent filters.
- Auth via guards; authorization checks in the service (business rule), not only in the controller.
- Structured logging (one logger, JSON to stdout), no `console.log`. Graceful shutdown (`enableShutdownHooks`).
- OpenAPI/Swagger generated from DTOs.

## Testing
Jest. Unit-test services with fake repositories; integration-test each module's endpoints against a real test
Postgres (docker), cleaned per test — few, focused on the important paths and error cases (including the
problem+json shape and pagination limits).

## Verify
`npm run verify` = `lint && typecheck && arch && test && build`, with
`"arch": "depcruise src --config .dependency-cruiser.cjs"`.
