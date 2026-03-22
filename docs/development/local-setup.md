# Local Setup

This document provides detailed local execution steps without Docker for AI Life Architect.

## Prerequisites

- Python 3.12 or newer
- Node.js 20 or newer
- PostgreSQL 16 or newer
- Redis 7 or newer
- Optional: Ollama for local AI connectivity

## PostgreSQL

1. Install PostgreSQL.
2. Ensure the `postgres` user password is `root`, or create an equivalent user with that password.
3. Create the database:

```sql
CREATE DATABASE ai_life_architect;
```

4. Confirm connectivity on `localhost:5432`.

## Redis

1. Install Redis.
2. Start Redis on `localhost:6379`.
3. Confirm connectivity with `redis-cli ping`.

## Backend

1. Open a terminal in `/backend`.
2. Create a virtual environment:

```bash
py -3.12 -m venv .venv
```

3. Activate it:

```bash
.venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -e .[dev]
```

5. Create the environment file:

```bash
copy .env.example .env
```

6. Apply migrations:

```bash
alembic upgrade head
```

7. Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

8. Verify health:

```bash
curl http://localhost:8004/api/v1/health/live
curl http://localhost:8004/api/v1/health/ready
```

## Worker

1. Open another terminal in `/backend`.
2. Activate the same virtual environment.
3. Start Celery:

```bash
celery -A app.workers.celery_app:celery_app worker --loglevel=INFO
```

## Frontend

1. Open a terminal in `/frontend`.
2. Install dependencies:

```bash
npm install
```

3. Create the frontend environment file:

```bash
copy .env.example .env
```

4. Start the development server:

```bash
npm run dev -- --host 0.0.0.0 --port 5176
```

5. Open `http://localhost:5176`.

## Validation Commands

### Root

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

### Backend

```bash
ruff check .
mypy app
pytest
```

### Frontend

```bash
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run build
```

## Docker Alternative

If you want a containerized workflow later, return to the repository root and run:

```bash
docker compose up --build
```
