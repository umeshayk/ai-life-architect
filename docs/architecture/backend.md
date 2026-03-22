# Backend Architecture

## Layering

- `app/main.py`: FastAPI application factory, middleware, CORS, router registration, and lifecycle hooks
- `app/api/v1`: API composition layer
- `app/modules/health`: thin route handlers for health concerns
- `app/services`: business/service logic, including health evaluation and future seed hooks
- `app/db`: SQLAlchemy base, engine, and session management
- `app/models`: relational entities and future domain models
- `app/schemas`: request/response contracts
- `app/workers`: Celery bootstrap and future asynchronous jobs
- `app/core`: config, logging, middleware, and exception handling

## Health Strategy

The health module exposes:

- `GET /api/v1/health/live`: process-level liveness
- `GET /api/v1/health/ready`: dependency-aware readiness with HTTP 503 on required dependency failure
- `GET /api/v1/health/details`: detailed structured status for operational visibility

Readiness currently validates:

- API boot success
- database connectivity
- worker configuration state
- Ollama provider metadata presence as non-fatal detail

## Persistence Foundation

- SQLAlchemy 2.x declarative base
- Alembic baseline migration
- PostgreSQL default connection via `DATABASE_URL`
- pgvector extension enabled during migration baseline

## Cross-Cutting Concerns

- Pydantic Settings for startup validation
- JSON structured logging
- Correlation ID and response-time middleware
- Standard API success and error response shapes
