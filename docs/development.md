# Development Workflow

## Standards

All work in this repository should follow `AGENTS.md`, especially:

- locked stack requirements
- shared API envelope
- token-driven theming
- responsive app shell patterns
- tests and documentation updates for meaningful changes

## Phase 1 Commands

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

### Frontend

```powershell
cd frontend
npm install
npm test
npm run build
npm run dev
```

## Validation Checklist

- backend tests pass
- frontend tests pass
- frontend build passes
- `/api/v1/health` returns the standard envelope
- app shell works at mobile, tablet, desktop, and wide desktop sizes
- theme switching works in light and dark at minimum, plus premium themes
