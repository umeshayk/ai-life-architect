# Architecture Overview

AI Life Architect uses a clean multi-app repository structure with strongly separated backend and frontend applications, plus shared documentation and infrastructure at the root. Section 8.1 establishes the long-lived platform baseline rather than a temporary scaffold.

## System Boundary

- `frontend/` contains the enterprise application shell, routing, theming, shared UI primitives, and server-state integrations.
- `backend/` contains the FastAPI application, configuration, API contracts, middleware, services, models, workers, and tests.
- `docs/` contains architecture, development, and future-operating documentation.
- `docker-compose.yml` coordinates local platform services including PostgreSQL, Redis, backend API, Celery worker, and frontend.

## Request Flow

1. Browser requests the React application from the Vite frontend.
2. React Router renders the shared `AppLayout` with sticky header, responsive navigation, and route content.
3. TanStack Query requests backend data from `/api/v1/*`.
4. FastAPI applies correlation and timing middleware, then routes through thin API handlers.
5. Handlers delegate health and future domain work to services.
6. Services use database and infrastructure adapters rather than embedding logic in route functions.
7. Responses return through a consistent success or error envelope.

## Foundation Guarantees

- Structured configuration via environment variables
- Structured logging and correlation IDs
- Health endpoints with readiness dependency reporting
- Alembic migration baseline with pgvector preparation
- Theme-token-driven frontend with light, dark, graphite, and ocean modes
- User-facing dashboard surfaces separated from admin-only operational visibility
- Testable frontend and backend entry points
