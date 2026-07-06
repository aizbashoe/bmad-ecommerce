# Project Documentation Index — bmad-ecommerce

**Generated:** 2026-07-06 · Deep scan · This is the primary entry point for AI-assisted development.

## Project Overview

- **Type:** multi-part monorepo (2 parts)
- **Purpose:** anonymous-user e-commerce storefront (learning/POC) — browse, PDP, cart, guest checkout
- **Repository:** github.com/aizbashoe/bmad-ecommerce

## Quick Reference by part

### Backend API (`backend/`)
- **Type:** backend (REST API)
- **Stack:** Python 3.13, FastAPI 0.139, boto3, Pydantic v2, Uvicorn
- **Entry point:** `backend/app/main.py`
- **Pattern:** ports-and-adapters (`api → services → repositories`), stateless, 12-factor

### Frontend SPA (`frontend/`)
- **Type:** web (SPA)
- **Stack:** React 19.2, TypeScript 5, Vite 8, Node 22
- **Entry point:** `frontend/src/main.tsx`
- **Pattern:** component SPA with a single typed API client

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Backend Architecture](./architecture-backend.md)
- [Frontend Architecture](./architecture-frontend.md)
- [API Contracts — Backend](./api-contracts-backend.md)
- [Data Models — Backend](./data-models-backend.md)
- [Development Guide](./development-guide.md)
- [Deployment Guide](./deployment-guide.md)
- [Integration Architecture](./integration-architecture.md)
- [Project Parts (metadata)](./project-parts.json)

## Related BMAD docs

- [README.md](../README.md) — BMAD project guide
- [bmad/command-log.md](bmad/command-log.md) — command log / runbook + skills-per-phase
- [bmad/lifecycle.md](bmad/lifecycle.md) — lifecycle diagram + per-skill reference
- [bmad/story-guide.md](bmad/story-guide.md) — how to implement a story
- [bmad/execution-report.md](bmad/execution-report.md) — steps → output-files manifest
- [bmad/brownfield-guide.md](bmad/brownfield-guide.md) — adopting BMAD on an existing codebase
- Planning artifacts: `_bmad-output/planning-artifacts/` (brief, PRD, architecture spine, epics)

## Getting Started

```bash
docker compose up -d --build
docker compose exec api python -m scripts.seed
# API http://localhost:8000/docs  ·  Storefront http://localhost:5173
```
Backend tests: `cd backend && .venv/Scripts/python -m pytest -q`. See the
[Development Guide](./development-guide.md) for details.

## Implementation status (at scan time)

Epic 1 in progress — **1.1** scaffold ✅, **1.2** Products table + seed ✅, **1.3** paginated PLP ✅.
Remaining: 1.4 search, 1.5 category facet, 1.6 sort; then Epic 2 (PDP), 3 (cart), 4 (checkout).

## Using this for a brownfield PRD

When planning new features, point the PRD workflow at this `index.md` as the codebase context.
