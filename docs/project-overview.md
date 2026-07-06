# Project Overview — bmad-ecommerce

**Generated:** 2026-07-06 · Deep scan · Repository type: **multi-part monorepo**

## Purpose

An anonymous-user e-commerce storefront (learning/POC) built with the BMAD method.
Shoppers browse a catalog, view products, build a cart, and check out as a guest —
no accounts, no authentication. Backend is a Python/FastAPI API over DynamoDB; frontend
is a React/TypeScript SPA. Runs locally end-to-end via Docker Compose.

> Product intent lives in `_bmad-output/planning-artifacts/` (brief, PRD, architecture spine,
> epics). **This `docs/` set describes the code as built.** As of this scan, Epic 1 stories
> 1.1–1.3 are implemented (scaffold, catalog table + seed, paginated PLP).

## Parts

| Part | Path | Type | Stack |
|------|------|------|-------|
| **backend** | `backend/` | backend API | Python 3.13, FastAPI 0.139, boto3, Pydantic v2, Uvicorn |
| **frontend** | `frontend/` | web SPA | React 19.2, TypeScript 5, Vite 8, Node 22 |
| **infra** | `infra/` | (placeholder) | AWS ECS/DynamoDB IaC — deferred |

## Tech stack summary

| Category | Technology | Version |
|----------|-----------|---------|
| API framework | FastAPI | 0.139.x |
| Language (API) | Python | 3.13 |
| ASGI server | Uvicorn | current |
| Validation | Pydantic (+ pydantic-settings) | v2 |
| AWS SDK | boto3 | current |
| Data store | DynamoDB (local: `amazon/dynamodb-local`) | — |
| UI framework | React | 19.2 |
| Language (UI) | TypeScript | 5.x |
| Build tool | Vite | 8.1 |
| Runtime (UI) | Node.js | 22 LTS |
| Orchestration | Docker Compose | — |
| Tests | pytest + moto (backend), Vitest-ready (frontend) | — |

## Architecture at a glance

- **Backend: ports-and-adapters (hexagonal-lite).** `api → services → repositories`; boto3 is confined to `repositories/`. Stateless; 12-factor config.
- **Frontend: component SPA** with a single typed API-client module; pages under `src/pages/`.
- **Contract:** REST/JSON; FastAPI OpenAPI is the source of truth; JSON is camelCase; errors use a `{error:{code,message}}` envelope; money is integer minor units (cents).
- **Anonymous identity:** an opaque guest token (planned for the cart epic); no auth anywhere.

## Documentation index

See **[index.md](./index.md)** for the full navigation hub. Key docs:
[Source Tree](./source-tree-analysis.md) · [Backend Architecture](./architecture-backend.md) · [Frontend Architecture](./architecture-frontend.md) · [API Contracts](./api-contracts-backend.md) · [Data Models](./data-models-backend.md) · [Development Guide](./development-guide.md) · [Deployment Guide](./deployment-guide.md) · [Integration Architecture](./integration-architecture.md)
