# Development Guide — bmad-ecommerce

**Generated:** 2026-07-06

## Prerequisites

- Docker Desktop (with WSL2 on Windows) — for the full local stack
- Python 3.13 + [uv](https://docs.astral.sh/uv/) — backend dev/tests
- Node.js 22 LTS + npm — frontend dev/build
- AWS CLI (optional) — only for future AWS deployment

## Run the whole stack (recommended)

```bash
docker compose up -d --build          # api + dynamodb-local + frontend
docker compose exec api python -m scripts.seed   # seed 240 products (first run)
```
- API: http://localhost:8000  (docs: http://localhost:8000/docs)
- Frontend: http://localhost:5173
- DynamoDB Local: localhost:8001 (container port 8000)

Stop: `docker compose down` (add `-v` to also drop the DynamoDB volume).

## Backend (without Docker)

```bash
cd backend
uv venv --python 3.13 .venv
uv pip install --python .venv -e ".[dev]"
# point at a running DynamoDB Local:
DYNAMODB_ENDPOINT=http://localhost:8001 .venv/Scripts/python -m scripts.seed
DYNAMODB_ENDPOINT=http://localhost:8001 .venv/Scripts/python -m uvicorn app.main:app --reload
```

### Backend tests

```bash
cd backend
.venv/Scripts/python -m pytest -q      # 28 tests; moto mocks DynamoDB (no AWS/Docker needed)
```

## Frontend (without Docker)

```bash
cd frontend
npm install
npm run dev        # Vite dev server on :5173 (set VITE_API_BASE_URL if API not on :8000)
npm run build      # tsc typecheck + production build
```

## Configuration

All config is via environment variables (12-factor). `.env.example` documents every var;
`docker-compose.yml` sets them for the stack. The only local↔AWS difference is
`DYNAMODB_ENDPOINT` (+ credentials). Key vars: `DYNAMODB_ENDPOINT`, `AWS_REGION`,
`PRODUCTS_TABLE`/`CARTS_TABLE`/`ORDERS_TABLE`, `FLAT_SHIPPING` (cents), `CORS_ORIGINS`,
`VITE_API_BASE_URL`.

## Conventions

- **Backend layering:** never import boto3 outside `app/repositories/`; routers call services, services call repositories.
- **Money:** integer cents everywhere server-side; format to a string only in the frontend.
- **API JSON:** camelCase (via `CamelModel`); errors use `{error:{code,message}}`.
- **Tests:** backend uses pytest + moto; write a failing test first (red-green-refactor).

## BMAD workflow

This project is built with the BMAD method. Process runbooks live at the repo root:
[BMAD.md](../BMAD.md) (command log), [BMAD_DIAGRAM.md](../BMAD_DIAGRAM.md) (lifecycle + skills),
[BMAD_STORY.md](../BMAD_STORY.md) (how to implement a story). Planning artifacts are under
`_bmad-output/planning-artifacts/`.
