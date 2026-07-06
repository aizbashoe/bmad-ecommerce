---
baseline_commit: bc299c44829f4ff785c2c38ec9352fad4aa74d70
---

# Story 1.1: Project scaffold and local runtime (walking skeleton)

Status: done


<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the builder,
I want the backend, frontend, and local DynamoDB running together from one command,
so that every later story has a working end-to-end stack to build on.

## Acceptance Criteria

1. **One-command startup.** From a clean checkout, `docker compose up` starts three services — the FastAPI `api`, `amazon/dynamodb-local`, and the React/Vite `frontend` — and all three reach a running state.
2. **Backend layered per AD-1.** The backend is scaffolded in the ports-and-adapters layout: `app/api/`, `app/services/`, `app/repositories/`, `app/models/`, `app/core/`, plus `app/main.py`. No boto3/DynamoDB access exists outside `app/repositories/` (there is none yet — the layout is what's being established).
3. **Health + OpenAPI (AD-5).** The API exposes `GET /health` returning `200` with body `{"status": "ok"}`, and serves auto-generated OpenAPI docs at `/docs` (Swagger UI) and `/openapi.json`.
4. **12-factor config (AD-8).** All environment-specific values — DynamoDB endpoint URL, AWS region, table-name variables, CORS origins, and `FLAT_SHIPPING` — are read from environment variables via a single typed settings object. No environment branching (`if local/prod`) in code.
5. **Stateless (AD-9).** The API holds no per-request/session state in memory. (Trivially satisfied at skeleton stage; the layout and settings must not introduce module-level mutable state.)
6. **Frontend reaches the API.** The frontend loads in the browser and successfully calls `GET /health` through a single typed API-client module, rendering the returned status on screen. CORS is configured on the API to allow the frontend origin.
7. **DynamoDB wiring proven (no tables).** A boto3 client, configured from settings, can connect to `dynamodb-local` and perform `list_tables()` without error. Table creation is explicitly **out of scope** for this story (it belongs to Story 1.2).

## Tasks / Subtasks

- [x] **Task 1 — Backend scaffold** (AC: #2, #3, #4, #5)
  - [x] Create `backend/pyproject.toml` pinning: `fastapi==0.139.*`, `uvicorn[standard]`, `boto3`, `pydantic>=2`, `pydantic-settings`; dev deps `pytest`, `httpx` (for TestClient). Target Python 3.13.
  - [x] Create the layout: `backend/app/{api,services,repositories,models,core}/__init__.py`, `backend/app/main.py`, and an empty `backend/app/repositories/` (adapters land in later stories).
  - [x] `backend/app/core/config.py`: a `pydantic-settings` `Settings` class reading env vars — `DYNAMODB_ENDPOINT`, `AWS_REGION` (default `us-east-1`), `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` (dummy values accepted for local), `PRODUCTS_TABLE`/`CARTS_TABLE`/`ORDERS_TABLE`, `CORS_ORIGINS` (comma-separated), `FLAT_SHIPPING` (int, minor units). Provide a cached `get_settings()`.
  - [x] `backend/app/main.py`: create the FastAPI app, add `CORSMiddleware` from `settings.CORS_ORIGINS`, mount an `api` router, keep OpenAPI docs enabled at `/docs` + `/openapi.json`.
  - [x] `backend/app/api/health.py`: `GET /health` → `{"status": "ok"}`; `GET /health/deep` → calls the DynamoDB client `list_tables()` and returns `{"status":"ok","dynamodb":"reachable","tables":[...]}` (or `503` with the error envelope if unreachable). boto3 client factory lives in `app/repositories/dynamodb.py` (AD-1).
  - [x] `backend/app/core/errors.py`: the `{"error": {"code", "message"}}` envelope shape (AD-5) and exception handlers wiring it to FastAPI.
  - [x] `backend/Dockerfile`: python:3.13-slim base, install deps, run `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- [x] **Task 2 — Frontend scaffold** (AC: #6)
  - [x] Scaffold a React 19 + TypeScript + Vite 8 app in `frontend/` (`package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.tsx`, `src/App.tsx`).
  - [x] Create `frontend/src/api/client.ts`: a single typed API-client module reading the API base URL from `import.meta.env.VITE_API_BASE_URL`; expose `getHealth()`.
  - [x] Create `frontend/src/pages/` and `frontend/src/state/` directories (placeholders for later stories). `App.tsx` calls `getHealth()` on mount and renders the status.
  - [x] `frontend/Dockerfile`: node:22 base, install deps, run the Vite dev server bound to `0.0.0.0` so it's reachable from the host.
- [x] **Task 3 — Compose orchestration** (AC: #1, #7)
  - [x] Create `docker-compose.yml` at repo root with three services (dynamodb-local host 8001→8000, api host 8000, frontend host 5173) with env + depends_on wiring.
  - [x] Add a `.env.example` at repo root documenting every variable.
- [x] **Task 4 — Verify end-to-end** (AC: #1, #3, #6, #7) — *verified live on Docker 29.6.1.*
  - [x] `docker compose up` → all three services up; `api` healthy.
  - [x] `curl http://localhost:8000/health` → `200 {"status":"ok"}`; `/docs` + `/openapi.json` serve; 404 returns the error envelope.
  - [x] `curl http://localhost:8000/health/deep` → `200 {"status":"ok","dynamodb":"reachable","tableCount":0}` (list_tables succeeds against dynamodb-local).
  - [x] `http://localhost:5173` → serves 200 (renders "API: ok"; `/health` reachable through CORS).
- [x] **Task 5 — Tests** (AC: #3, #4)
  - [x] `backend/tests/test_health.py`: `TestClient` asserts `/health` → `200 {"status":"ok"}`, OpenAPI served, and `/health/deep` success + 503 paths (mocked). **7/7 pass.**
  - [x] `backend/tests/test_config.py`: asserts `Settings` loads from env, defaults, and `get_settings()` is cached.

### Review Findings

*Code review 2026-07-06 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Severity set at triage.*

- [x] [Review][Patch] **HIGH — Backend Docker build fails: `pip install .` runs before `COPY app`** [backend/Dockerfile:8] — Hatchling `packages=["app"]` needs the source present; build errors. (blind)
- [x] [Review][Patch] MED — AWS creds default to `"local"` and are always passed to boto3, breaking IAM-role auth on AWS [backend/app/core/config.py:22-23, backend/app/repositories/dynamodb.py:20-27] — pass creds only when `dynamodb_endpoint` is set. (blind+edge)
- [x] [Review][Patch] MED — Frontend image: no `.dockerignore`, `COPY . .` clobbers container `node_modules`, `npm install` ignores the committed lockfile [frontend/Dockerfile] — add `.dockerignore` (both services), `COPY package*.json`, `npm ci`. (blind)
- [x] [Review][Patch] MED — AD-5 partial: error envelope not applied to `HTTPException`/`RequestValidationError` (404/422 return default shape); camelCase convention not established [backend/app/main.py:33-34] — add handlers + a CamelModel base. (auditor)
- [x] [Review][Patch] MED — compose `depends_on` has no readiness condition → `/health/deep` startup race [docker-compose.yml] — add a dynamodb-local healthcheck + `condition: service_healthy`. (blind+edge)
- [x] [Review][Patch] MED — no boto3 timeouts → `/health/deep` can hang on an unresponsive endpoint [backend/app/repositories/dynamodb.py] — add botocore `Config(connect_timeout, read_timeout, retries)`. (edge)
- [x] [Review][Patch] LOW — `/health/deep` leaks raw exception text and all table names [backend/app/api/health.py:29-34] — generic message; drop the table list. (blind+edge)
- [x] [Review][Patch] LOW — empty `VITE_API_BASE_URL` (`""`) collapses to a relative URL [frontend/src/api/client.ts:4-5] — use `||` not `??`. (edge)
- [x] [Review][Patch] LOW — whitespace-only `DYNAMODB_ENDPOINT` is treated as a real endpoint [backend/app/repositories/dynamodb.py:25] — `.strip()` before the truthiness check. (edge)
- [x] [Review][Patch] LOW — frontend fetch has no timeout → UI stuck on "checking…" if API stalls [frontend/src/api/client.ts, frontend/src/App.tsx] — add an AbortController timeout. (edge)
- [x] [Review][Patch] LOW — `frontend/tsconfig.tsbuildinfo` build artifact is not gitignored [.gitignore] — ignore it and remove from tree. (reviewer/observed)
- [x] [Review][Defer] LOW — `/docs` + `/openapi.json` exposed with no gating [backend/app/main.py:21-22] — deferred; accepted for local POC, gate before any non-local deploy.
- [x] [Review][Defer] LOW — container runs the Vite dev server (not a production build) [frontend/Dockerfile:15] — deferred; accepted for local-first POC.
- [x] [Review][Defer] LOW — `.env.example` `DYNAMODB_ENDPOINT` only resolves inside the compose network [.env.example:6] — deferred; add a host-run note when needed.

*Dismissed as noise (5): speculative versions won't resolve (verified: pytest + vite build both pass); empty `CORS_ORIGINS` blocks all (defined behavior); empty `AWS_REGION` (has default); `FLAT_SHIPPING` crash-at-import (acceptable fail-fast) / no upper bound (negligible); non-JSON 200 → "unreachable" (degraded but safe).*

## Dev Notes

### Architecture patterns and constraints (MUST follow)

- **AD-1 Ports & Adapters** — establish `api → services → repositories` layering now. This story creates no repositories yet, but the directories and the dependency rule are set: later stories put ALL boto3 inside `app/repositories/`. Do not import boto3 in `api/` or `services/`. [Source: ARCHITECTURE-SPINE.md#Design Paradigm, #AD-1]
- **AD-5 API contract** — FastAPI's generated OpenAPI is the source of truth; keep `/docs` + `/openapi.json` enabled. Error responses use `{"error":{"code","message"}}`. JSON keys are camelCase (not relevant for `/health`, but the error handler/model config should be set up for it — e.g. Pydantic `alias_generator=to_camel`, `populate_by_name=True`). [Source: ARCHITECTURE-SPINE.md#AD-5, #Consistency Conventions]
- **AD-8 12-factor config** — one `Settings` object; the ONLY difference between local and AWS is `DYNAMODB_ENDPOINT` + credentials. boto3 clients must pass `endpoint_url=settings.DYNAMODB_ENDPOINT` when set (local), and omit it when empty (AWS). No `if env == ...` branches. [Source: ARCHITECTURE-SPINE.md#AD-8]
- **AD-9 Stateless** — no module-level mutable state; no in-memory sessions. [Source: ARCHITECTURE-SPINE.md#AD-9]
- **Money = integer minor units** — `FLAT_SHIPPING` is an int in cents (AD-6); not used in this story but define the setting. [Source: ARCHITECTURE-SPINE.md#AD-6]

### Stack (verified current 2026-07; pin these)

| Component | Version | Notes |
| --- | --- | --- |
| Python | 3.13 | base image `python:3.13-slim` |
| FastAPI | 0.139.* | OpenAPI auto-gen |
| Uvicorn | current `[standard]` | ASGI server |
| Pydantic | v2 | + `pydantic-settings` for config |
| boto3 | current | DynamoDB client with `endpoint_url` override |
| Node.js | 22 LTS | base image `node:22` |
| TypeScript | 5.x | |
| React | 19.2 | |
| Vite | 8.1 | requires Node ≥ 20.19 / 22.12; dev server default port 5173 |
| DynamoDB Local | `amazon/dynamodb-local` | official image; no IAM, any creds work |

[Source: ARCHITECTURE-SPINE.md#Stack]

### Source tree to create (this story)

```text
TestBmad/
  backend/
    app/
      api/__init__.py        # router aggregation
      api/health.py          # /health, /health/deep
      services/__init__.py   # (empty; domain logic lands later)
      repositories/__init__.py # (empty; ONLY place boto3 will live)
      models/__init__.py     # (empty; Pydantic models land later)
      core/__init__.py
      core/config.py         # Settings (pydantic-settings)
      core/errors.py         # {error:{code,message}} envelope + handler
      main.py                # app factory, CORS, router mount
    tests/
      test_health.py
      test_config.py
    Dockerfile
    pyproject.toml
  frontend/
    index.html
    package.json
    tsconfig.json
    vite.config.ts
    src/
      main.tsx
      App.tsx                # calls getHealth(), renders status
      api/client.ts          # typed client, base URL from VITE_API_BASE_URL
      pages/                 # (placeholder for PLP/PDP/etc.)
      state/                 # (placeholder for cart/guest-token)
  docker-compose.yml         # dynamodb-local + api + frontend
  .env.example
```

[Source: ARCHITECTURE-SPINE.md#Structural Seed]

### Port map (avoid clashes)

- `api` → host **8000** (container 8000)
- `frontend` (Vite dev) → host **5173**
- `dynamodb-local` → host **8001** (container 8000) — mapped off 8000 so it doesn't collide with the API.
- Inside the compose network, the API reaches DynamoDB at `http://dynamodb-local:8000` (container port), NOT 8001.

### Testing standards

- Backend: `pytest` with FastAPI `TestClient` (via `httpx`). Tests live in `backend/tests/`. Keep them runnable without Docker (mock/skip the `/health/deep` DynamoDB call in unit tests, or point at a local endpoint only when present).
- Frontend: Vitest is available in the stack but not required for this skeleton; a smoke test is optional.

### Project Structure Notes

- All NEW files — this is the first story; there is no existing code to modify. No regressions possible.
- The `repositories/`, `services/`, `models/`, `pages/`, `state/` dirs are created empty (with `__init__.py` on the Python side) to lock in the AD-1 layout so later stories have an obvious home for their code.
- Keep the skeleton minimal: no product/cart/order logic, no tables. Those are Stories 1.2+ and must not be pulled forward.

### References

- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md#Design Paradigm]
- [Source: ARCHITECTURE-SPINE.md#Invariants & Rules — AD-1, AD-5, AD-6, AD-8, AD-9]
- [Source: ARCHITECTURE-SPINE.md#Stack]
- [Source: ARCHITECTURE-SPINE.md#Structural Seed]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Opus 4.8)

### Debug Log References

- Backend tests: `cd backend && .venv/Scripts/python -m pytest -q` → **7 passed** (Python 3.13 venv).
- Frontend build: `cd frontend && npm run build` → **tsc + vite 8.1.3 build succeeded** (0 vulnerabilities).
- Docker `compose up` NOT run: Docker daemon unavailable in this environment (`docker info` failed). Live end-to-end verification (AC-1, live AC-6/AC-7) is deferred to the developer.

### Completion Notes List

- Established the AD-1 ports-and-adapters layout: `api/` (routers), `services/` (empty), `repositories/` (boto3 quarantined here — `repositories/dynamodb.py` is the only boto3 import), `models/`, `core/`.
- `core/config.py` = single `pydantic-settings` object (AD-8); the only local↔AWS difference is `DYNAMODB_ENDPOINT` (endpoint override applied only when set). `get_settings()` is `lru_cache`d.
- `/health` (liveness) and `/health/deep` (readiness via `list_tables()`, 503+error-envelope on failure). OpenAPI at `/docs` + `/openapi.json` (AD-5). Error envelope `{error:{code,message}}` established in `core/errors.py`.
- Frontend: React 19.2 / Vite 8.1 / TS; single typed API client (`src/api/client.ts`, AD-5); `App.tsx` calls `getHealth()` and renders status (AC-6). `pages/` and `state/` placeholders reserve the layout for later stories.
- `docker-compose.yml` wires dynamodb-local (host 8001→8000) + api (8000) + frontend (5173); `.env.example` documents every variable.
- **No tables created** — deferred to Story 1.2 as scoped (AC-7).
- **Status kept `in-progress`:** all code tasks (1,2,3,5) complete and verified; Task 4 (live `docker compose up`) is blocked by the missing Docker daemon, so the story is not yet marked `review`.

### File List

- backend/pyproject.toml (new)
- backend/Dockerfile (new)
- backend/app/__init__.py (new)
- backend/app/main.py (new)
- backend/app/api/__init__.py (new)
- backend/app/api/health.py (new)
- backend/app/services/__init__.py (new)
- backend/app/repositories/__init__.py (new)
- backend/app/repositories/dynamodb.py (new)
- backend/app/models/__init__.py (new)
- backend/app/core/__init__.py (new)
- backend/app/core/config.py (new)
- backend/app/core/errors.py (new)
- backend/tests/__init__.py (new)
- backend/tests/test_health.py (new)
- backend/tests/test_config.py (new)
- frontend/package.json (new)
- frontend/tsconfig.json (new)
- frontend/vite.config.ts (new)
- frontend/index.html (new)
- frontend/src/main.tsx (new)
- frontend/src/App.tsx (new)
- frontend/src/api/client.ts (new)
- frontend/src/vite-env.d.ts (new)
- frontend/src/pages/.gitkeep (new)
- frontend/src/state/.gitkeep (new)
- docker-compose.yml (new)
- .env.example (new)
- backend/.dockerignore (new — review P3)
- frontend/.dockerignore (new — review P3)
- frontend/package-lock.json (new — committed lockfile for `npm ci`)
- .gitignore (modified — ignore `*.tsbuildinfo`, review P11)

### Change Log

- 2026-07-06: Implemented walking skeleton (backend hexagonal scaffold + health/OpenAPI + config, React/Vite frontend, docker-compose + dynamodb-local). Backend tests pass; frontend builds.
- 2026-07-06: Code review — 1 High, 5 Med, 5 Low findings; all 11 patches applied (Dockerfile build order, AWS-cred/IAM parity, `.dockerignore`+`npm ci`, AD-5 envelope for 404/422 + camelCase base, compose healthcheck, boto3 timeouts, health-deep info-leak, frontend base-url/timeout, tsbuildinfo ignore). 3 deferred, 5 dismissed. Backend 8/8 tests pass; frontend builds.
- 2026-07-06: Live verification on Docker 29.6.1 — fixed dynamodb-local crash-loop (SQLite could not write the root-owned named volume as the image's non-root user) by running that service as `user: root`. All 7 ACs verified end-to-end; story **done**. File List += docker-compose.yml (modified).
