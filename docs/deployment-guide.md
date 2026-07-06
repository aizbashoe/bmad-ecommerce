# Deployment Guide — bmad-ecommerce

**Generated:** 2026-07-06

## Current: local-first (the definition of "done" for v1)

The whole stack runs locally via Docker Compose. This is the supported deployment today.

```bash
docker compose up -d --build
docker compose exec api python -m scripts.seed
```

### `docker-compose.yml` services

| Service | Image / build | Host port | Notes |
|---------|---------------|-----------|-------|
| `dynamodb-local` | `amazon/dynamodb-local` | 8001 → 8000 | runs as `user: root` so it can persist to the named volume `dynamodb-data`; `-sharedDb -dbPath /data` |
| `api` | build `./backend` | 8000 | env-configured; `depends_on: dynamodb-local`; HEALTHCHECK on `/health` |
| `frontend` | build `./frontend` | 5173 | Vite dev server; `depends_on: api`; `VITE_API_BASE_URL=http://localhost:8000` |

Inside the compose network the API reaches DynamoDB at `http://dynamodb-local:8000`.

### Environment

Config is 12-factor (see `.env.example`). Compose sets: `DYNAMODB_ENDPOINT`, `AWS_REGION`,
dummy `AWS_ACCESS_KEY_ID`/`SECRET`, table names, `FLAT_SHIPPING`, `CORS_ORIGINS`, `VITE_API_BASE_URL`.

## Future: AWS ECS/Fargate + DynamoDB (deferred enhancement)

The architecture is designed so this is additive, not a rewrite:

- **API:** the `backend/` container image runs unchanged on ECS/Fargate. Leave `DYNAMODB_ENDPOINT`
  empty so boto3 uses the real regional endpoint and the ECS **task-role** credential chain
  (do not set static AWS keys). Set `CORS_ORIGINS` to the deployed frontend origin.
- **DynamoDB:** create the `Products` table + `gsi_category`/`gsi_listing` (and later Carts/Orders)
  in the target region; run the seed once as a task.
- **Frontend:** replace the dev-server container with a `vite build` + static host/CDN, and set
  `VITE_API_BASE_URL` to the deployed API URL.
- **IaC:** the `infra/` directory is a placeholder for CDK/Terraform — not yet written.

### Deferred hardening (from code reviews)

- Gate `/docs` + `/openapi.json` behind config before any non-local deploy.
- Serve a production frontend build instead of the Vite dev server.
- See `_bmad-output/implementation-artifacts/deferred-work.md` for the full list.
