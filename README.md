# AI Life Architect

AI Life Architect is an enterprise-grade personal intelligence operating system built with FastAPI, React, PostgreSQL, Redis, Celery, and Ollama-ready AI abstractions. This foundation implements Section 8.1 of the product specification with a production-quality monorepo structure, health checks, responsive frontend app shell, local and Docker workflows, testing, and architecture documentation.

## Stack

- Frontend: React, TypeScript, Vite, React Router, TanStack Query, Zustand, React Hook Form, Zod, Vitest, Testing Library
- Backend: FastAPI, SQLAlchemy 2.x, Alembic, Pydantic Settings, PostgreSQL, pgvector-ready bootstrap, Redis, Celery, Pytest
- Infrastructure: Docker Compose, `.env`-driven configuration, Ruff, Mypy, ESLint, TypeScript, Playwright

## Project Structure

```text
backend/
  app/
    api/v1
    core
    db
    models
    modules
    schemas
    services
    tests
    utils
    workers
frontend/
  src/
    app
    components
    features
    layouts
    pages
    routes
    services
    store
    styles
docs/
  architecture
  development
```

## Environment Files

1. Copy `backend/.env.example` to `backend/.env`
2. Copy `frontend/.env.example` to `frontend/.env`
3. Keep these required values:
   - PostgreSQL password: `root`
   - Database name: `ai_life_architect`
   - Backend port: `8004`
   - Frontend port: `5176`
   - `OLLAMA_MODEL=phi3:mini`

## Run With Docker

```bash
docker compose up --build
```

Important endpoints:

- Frontend: `http://localhost:5176`
- Backend API: `http://localhost:8004`
- API docs: `http://localhost:8004/docs`
- Liveness: `http://localhost:8004/api/v1/health/live`
- Readiness: `http://localhost:8004/api/v1/health/ready`

## Run Locally Without Docker

Detailed step-by-step instructions are also documented in [docs/development/local-setup.md](/c:/projects/ai-life-architect/docs/development/local-setup.md).

### 1. Install prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- Ollama installed locally if you want live model availability

### 2. Create the PostgreSQL database

```sql
CREATE DATABASE ai_life_architect;
```

Ensure the PostgreSQL superuser or application user password is `root`.

### 3. Backend setup

```bash
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### 4. Worker setup

In a second terminal:

```bash
cd backend
.venv\Scripts\activate
celery -A app.workers.celery_app:celery_app worker --loglevel=INFO
```

### 5. Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev -- --host 0.0.0.0 --port 5176
```

## Database and Migration Commands

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "message"
alembic downgrade -1
```

## Quality Commands

### Root shortcuts

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

`npm run test` executes frontend unit tests, the Playwright smoke e2e path, and backend pytest health checks.

### Backend only

```bash
cd backend
ruff check .
mypy app
pytest
```

### Frontend only

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run build
```

## Seed and Demo Hooks

The repository includes `backend/app/services/seed_service.py` as a controlled seed entry point for future local demo data. It currently bootstraps system metadata only and intentionally avoids fake business-domain records.

## Documentation

- [Architecture Overview](/c:/projects/ai-life-architect/docs/architecture/overview.md)
- [Backend Architecture](/c:/projects/ai-life-architect/docs/architecture/backend.md)
- [Frontend Architecture](/c:/projects/ai-life-architect/docs/architecture/frontend.md)
- [Local Setup](/c:/projects/ai-life-architect/docs/development/local-setup.md)
