# AI Life Architect

AI Life Architect is a local MVP for saving personal knowledge, generating summaries and embeddings, searching semantically, and asking grounded questions against your own saved notes, links, and files.

## Prerequisites

- Windows 10 or 11
- PostgreSQL 15+ with `pgvector`
- Python 3.11+
- Node.js 20+
- Ollama installed locally

## PostgreSQL Setup

1. Open `psql` as a PostgreSQL superuser.
2. Create the database:

```sql
CREATE DATABASE ai_life_architect;
```

3. Connect to it:

```sql
\c ai_life_architect
```

4. Enable `pgvector` and create the tables by running `setup.sql`.

Default connection values in the sample environment file assume:

- user: `postgres`
- password: `root`
- host: `localhost`
- port: `5432`

## pgvector Extension Setup

Install pgvector in PostgreSQL if it is not already available. On Windows this is usually done through:

- Stack Builder for your PostgreSQL installation, if it includes pgvector
- A pgvector package/build that matches your PostgreSQL version

After installation, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Python Virtual Environment

From the project root:

```powershell
cd ai-life-architect\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## pip Install

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Update `backend\.env` if your local PostgreSQL or Ollama setup differs.

## npm Install

```powershell
cd ..\frontend
npm install
```

## Ollama Install and Model Pull

Install Ollama for Windows, then pull the default model:

```powershell
ollama pull llama3.2
```

The backend calls Ollama at `http://localhost:11434/api/generate`.

## Backend Run

```powershell
cd "c:\projects\AI Life Architect\ai-life-architect\ai-life-architect\backend"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8001
```

## Frontend Run

```powershell
cd "c:\projects\AI Life Architect\ai-life-architect\ai-life-architect\frontend"
npm install
npm run dev
```

## Sample Local URLs

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8001`
- Health check: `http://localhost:8001/health`
- FastAPI docs: `http://localhost:8001/docs`

## Notes

- The backend creates tables on startup for MVP simplicity.
- File uploads support `.pdf` and `.txt`.
- Embeddings use `sentence-transformers/all-MiniLM-L6-v2`; if the model cannot load locally, the service falls back to deterministic embeddings so the app still runs.
- Ask AI retrieves the top 5 matches and sends them to Ollama as grounding context.
