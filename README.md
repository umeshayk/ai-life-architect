# AI Life Architect

AI Life Architect is an enterprise-grade personal intelligence operating system in progress. Phase 1 establishes the runnable foundation: FastAPI backend, React/Vite frontend, standard API envelope, responsive app shell, token-based theming, local environment configuration, and baseline tests.

## Phase 1 Deliverables

- FastAPI backend on `8004`
- React + Vite frontend on `5176`
- Standard `success/data/error/meta` API response contract
- Health and readiness endpoints
- Responsive enterprise app shell
- Light, dark, ocean, and graphite themes
- Local environment defaults for PostgreSQL, Redis, and Ollama
- Backend and frontend smoke tests

## Environment Defaults

- PostgreSQL user password: `root`
- PostgreSQL database: `ai_life_architect`
- Backend port: `8004`
- Frontend port: `5176`
- Ollama model: `phi3:mini`

## Local Setup Without Docker

### 1. Clone the repository

```powershell
git clone https://github.com/umeshayk/ai-life-architect.git
cd ai-life-architect
```

### 2. Install PostgreSQL and create the database

Use PostgreSQL 15+ locally. Ensure the `postgres` user password is `root` and create the requested database:

```sql
ALTER USER postgres WITH PASSWORD 'root';
CREATE DATABASE ai_life_architect;
```

Equivalent commands:

```powershell
psql -U postgres -h localhost -c "ALTER USER postgres WITH PASSWORD 'root';"
psql -U postgres -h localhost -c "CREATE DATABASE ai_life_architect;"
```

### 3. Install Redis locally

Run Redis at:

```text
redis://localhost:6379/0
```

### 4. Install Ollama and pull the configured model

```powershell
ollama pull phi3:mini
ollama run phi3:mini
```

Keep Ollama available at `http://localhost:11434`.

### 5. Configure the backend

```powershell
Copy-Item backend\.env.example backend\.env
```

The backend `.env` is already configured with:

```env
POSTGRES_PASSWORD=root
POSTGRES_DB=ai_life_architect
BACKEND_PORT=8004
OLLAMA_MODEL=phi3:mini
FRONTEND_ORIGIN=http://localhost:5176
```

### 6. Create the Python environment and install dependencies

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 7. Run backend tests

```powershell
python -m pytest -q
```

### 8. Start the backend

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

Useful URLs:

- `http://localhost:8004/docs`
- `http://localhost:8004/api/v1/health`
- `http://localhost:8004/api/v1/health/readiness`

### 9. Configure the frontend

Open a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm install
```

### 10. Run frontend tests

```powershell
npm test
```

### 11. Start the frontend

```powershell
npm run dev
```

Open `http://localhost:5176`.

### 12. Validate the Phase 1 foundation locally

1. Confirm `/api/v1/health` returns the standard success envelope.
2. Open the dashboard and the `Foundation Health` page.
3. Switch between `light`, `dark`, `ocean`, and `graphite` themes.
4. Verify responsive behavior at mobile, tablet, desktop, and wide desktop widths.
5. Confirm the health page shows loading, error, and empty-safe states.

## Commands

### Backend

```powershell
python -m pytest -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### Frontend

```powershell
npm test
npm run build
npm run dev
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Development Workflow](docs/development.md)
