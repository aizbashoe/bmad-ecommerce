# Source Tree Analysis — bmad-ecommerce

**Generated:** 2026-07-06 · Deep scan

```text
TestBmad/
├── backend/                      # Part: backend — FastAPI API (Python 3.13)
│   ├── app/
│   │   ├── main.py               # ▶ ENTRY POINT — create_app(): CORS, routers, error handlers
│   │   ├── api/                  # HTTP layer (routers only; no business logic, no boto3)
│   │   │   ├── __init__.py       #   api_router — aggregates feature routers
│   │   │   ├── health.py         #   GET /health, /health/deep
│   │   │   └── products.py       #   GET /products (paginated listing)
│   │   ├── services/             # Domain logic (depends on repository ports)
│   │   │   └── catalog.py        #   CatalogService — maps domain → API models
│   │   ├── repositories/         # Adapters — the ONLY place boto3/DynamoDB lives
│   │   │   ├── dynamodb.py        #   get_dynamodb_client() factory + list_table_names()
│   │   │   └── products.py        #   ProductsRepository — table provisioning, writes, list query, cursor codec
│   │   ├── models/               # Pydantic models
│   │   │   ├── __init__.py        #   CamelModel base (camelCase JSON)
│   │   │   ├── product.py         #   Product (domain)
│   │   │   └── catalog.py         #   ProductSummary, ProductPage (API responses)
│   │   └── core/                 # Cross-cutting
│   │       ├── config.py          #   Settings (12-factor, pydantic-settings) + get_settings()
│   │       └── errors.py          #   {error:{code,message}} envelope + exception handlers
│   ├── scripts/
│   │   └── seed.py               # ▶ Idempotent synthetic catalog seeder (python -m scripts.seed)
│   ├── tests/                    # pytest + moto (6 modules, 28 tests)
│   ├── Dockerfile                # python:3.13-slim; uvicorn; HEALTHCHECK
│   ├── .dockerignore
│   └── pyproject.toml            # deps + pytest config
│
├── frontend/                     # Part: frontend — React/TS SPA (Vite 8)
│   ├── src/
│   │   ├── main.tsx              # ▶ ENTRY POINT — mounts <App/>
│   │   ├── App.tsx               #   renders ProductListPage (storefront home)
│   │   ├── api/
│   │   │   └── client.ts          #   Typed API client → calls backend (getHealth, listProducts, formatPrice)
│   │   ├── pages/
│   │   │   └── ProductListPage.tsx#   PLP grid with cursor load-more
│   │   └── state/                 #   (placeholder — cart/guest-token, Epic 3)
│   ├── index.html
│   ├── Dockerfile                # node:22; vite dev server
│   ├── vite.config.ts, tsconfig.json, package.json
│
├── infra/                        # (placeholder) AWS ECS + DynamoDB IaC — deferred
├── docker-compose.yml            # ▶ api + dynamodb-local + frontend
├── .env.example                  # documents every env var
├── README.md                     # BMAD project guide
├── BMAD.md / BMAD_DIAGRAM.md / BMAD_STORY.md   # BMAD process runbooks
└── docs/                         # ← this generated documentation set
```

## Critical directories

| Directory | Role | Entry / key files |
|-----------|------|-------------------|
| `backend/app/api/` | HTTP boundary — request/response only | `main.py` (app factory), `products.py`, `health.py` |
| `backend/app/services/` | Domain logic | `catalog.py` |
| `backend/app/repositories/` | Persistence adapters (boto3 quarantined here) | `dynamodb.py`, `products.py` |
| `backend/app/core/` | Config + errors (cross-cutting) | `config.py`, `errors.py` |
| `backend/scripts/` | One-shot admin tooling | `seed.py` |
| `frontend/src/api/` | Single network boundary | `client.ts` |
| `frontend/src/pages/` | Route-level views | `ProductListPage.tsx` |

## Entry points

- **API:** `backend/app/main.py::app` (run by Uvicorn) — `docker compose` runs `uvicorn app.main:app`.
- **UI:** `frontend/src/main.tsx` → `App.tsx`.
- **Seed:** `backend/scripts/seed.py::main` — `python -m scripts.seed`.
- **Whole stack:** `docker-compose.yml` — `docker compose up`.
