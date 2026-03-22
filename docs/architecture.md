# Architecture Overview

## Phase 1 Scope

Phase 1 lays the product foundation required by `AGENTS.md`:

- clean multi-app structure
- FastAPI backend entrypoint
- standard API response envelope
- health and readiness endpoints
- React application shell
- semantic design token foundation
- responsive layout primitives
- baseline tests and docs

## Backend Foundation

- `backend/app/main.py` keeps routing thin and centralizes middleware plus validation handling.
- `backend/app/core/config.py` provides `.env`-driven settings for PostgreSQL, Redis, Ollama, and service ports.
- `backend/app/schemas/envelope.py` enforces the standard `success/data/error/meta` contract.
- `backend/app/api/v1/health.py` exposes health and readiness probes for operational checks.

## Frontend Foundation

- `frontend/src/layouts/AppShell.tsx` provides the shared enterprise shell with responsive navigation and sticky header.
- `frontend/src/store/theme-store.tsx` keeps UI-only theme preference state in Zustand.
- `frontend/src/services/api.ts` consumes the backend using the shared envelope contract.
- `frontend/src/pages/HealthPage.tsx` demonstrates real backend connectivity with loading, error, and empty-safe handling.

## Theme and Token Strategy

Phase 1 uses semantic CSS variables so future features inherit the same visual language without page-specific overrides. Current themes:

- `light`
- `dark`
- `ocean`
- `graphite`

Current tokens include:

- spacing
- radii
- shadows
- content widths
- surface layers
- text hierarchy
- border styling
- accent states
- focus treatment

## Next-Phase Readiness

This foundation leaves clear extension points for:

- SQLAlchemy models and Alembic migrations
- domain services and modules
- feature modules under `frontend/src/features`
- auth and RBAC
- background workers
- AI provider abstraction
