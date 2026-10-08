# NestJS (API) + PostgreSQL

Only what differs from defaults. General rules: `../engineering.md`.

## Layout
```
src/
  modules/<feature>/
    <feature>.module.ts
    controllers/            HTTP only: DTO in, call service, DTO out
    dto/                    request/response DTOs (class-validator + Swagger decorators)
    services/               use cases / business rules
    repositories/           data access (TypeORM), the only place that touches the DB
    entities/               TypeORM entities of this feature
    mappers/                entity ↔ DTO
  common/  exceptions/ filters/ guards/ interceptors/ decorators/ dto/
  config/  env.validation.ts, typed config
db/migrations/
```
Feature modules export only what other modules need (services, not repositories).

## Defaults
- `strict: true` in tsconfig (including `noImplicitAny`); no `any`.
- Global `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })`.
- Errors: domain exceptions (`BusinessException`, `ResourceNotFoundException`, each with a stable `code`) → one
  `GlobalExceptionFilter` maps them to HTTP. Controllers don't try/catch to build responses.
- Config via `@nestjs/config` with validation at startup; documented `.env.example`.
- DB: PostgreSQL + TypeORM (or Prisma if the project uses it). `synchronize: false` always; every schema change is
  a migration. Transactions for multi-step writes. Index foreign keys and frequent filters.
- Pagination on every list endpoint; never return unbounded collections.
- Auth via guards; authorization checks in the service (business rule), not only in the controller.
- Structured logging (one logger), no `console.log`.
- OpenAPI/Swagger generated from DTOs.

## Testing
Jest. Unit-test services with fake repositories; integration-test each module's endpoints against a real test
Postgres (docker) — few, focused on the important paths and error cases.

## Verify
`npm run verify` = `lint && typecheck && test && build`.
