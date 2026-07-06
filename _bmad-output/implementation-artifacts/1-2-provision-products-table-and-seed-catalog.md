---
baseline_commit: 72711c3d5c6cfc94d0df0b746fc13a36345677e0
---

# Story 1.2: Provision the Products table and seed a synthetic catalog

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the builder,
I want a Products table with its search indexes and a repeatable seed of sample products,
so that the storefront has realistic content to browse, search, filter, and sort.

## Acceptance Criteria

1. **Products table + GSIs provisioned (AD-3, AD-4).** A `Products` table exists with `PK = productId` (S), plus two global secondary indexes: `gsi_category` (`PK = category` (S), `SK = price` (N)) and `gsi_listing` (`PK = listingPk` (S, constant `"PRODUCT"`), `SK = price` (N)). Both GSIs project ALL attributes.
2. **Idempotent provisioning (FR-16).** Running provisioning when the table already exists is a safe no-op (no error, no duplicate); running it fresh creates the table + GSIs and waits until they're ACTIVE.
3. **Synthetic catalog seeded (FR-16).** A seed loads ~100–500 Products across several categories (at least 4), each with: `productId`, `name`, `description`, `price` (integer minor units / cents per AD-6), `category`, `imageUrl`, `available` (bool), and the `listingPk="PRODUCT"` attribute. Prices and names vary enough to exercise search, the category facet, and price sort.
4. **Idempotent seed (FR-16).** Product ids are deterministic, so re-running the seed overwrites existing items (PutItem) rather than creating duplicates; the item count is stable across repeated runs.
5. **Ownership boundary (AD-1, AD-3).** All Products DynamoDB access — table creation and writes — lives in a single `ProductsRepository` in `app/repositories/`. boto3 is not imported outside `app/repositories/`. The seed entrypoint calls the repository; it does not touch boto3 directly.
6. **Runnable locally.** A documented command provisions + seeds against `dynamodb-local` (e.g. `python -m scripts.seed` or `docker compose exec api python -m scripts.seed`). After it runs, `GET /health/deep` reports `tableCount ≥ 1`.
7. **Tested.** Unit tests (using `moto` to mock DynamoDB) verify: provisioning creates the table with both GSIs; provisioning twice is a no-op; the seed inserts the expected count and is idempotent (count stable on re-run); items carry all required attributes incl. `listingPk` and integer `price`.

## Tasks / Subtasks

- [x] **Task 1 — Product model** (AC: #3, #4)
  - [x] Add `Product` to `app/models/` as a `CamelModel` subclass (AD-5 camelCase): `productId: str`, `name: str`, `description: str`, `price: int` (minor units, `ge=0`), `category: str`, `imageUrl: str`, `available: bool = True`. Keep it a pure domain model — no DynamoDB item shapes leak out of the repository (AD-1).
- [x] **Task 2 — ProductsRepository: provisioning** (AC: #1, #2, #4)
  - [x] Create `app/repositories/products.py` with a `ProductsRepository` using the shared `get_dynamodb_client()` (from `repositories/dynamodb.py`) and `settings.products_table`.
  - [x] `ensure_table()`: create the table if absent — `KeySchema` PK=`productId`; `AttributeDefinitions` for `productId` (S), `category` (S), `price` (N), `listingPk` (S); GSIs `gsi_category` (category HASH, price RANGE) and `gsi_listing` (listingPk HASH, price RANGE), both `Projection=ALL`; `BillingMode=PAY_PER_REQUEST`. If it already exists (`ResourceInUseException` / describe returns it), no-op. Wait for ACTIVE via waiter.
  - [x] Map domain `Product` ↔ DynamoDB item inside the repo; set `listingPk="PRODUCT"` on write. Use the low-level client consistently (types: `{"S":...}`/`{"N": str(price)}`) OR the resource/`TypeDeserializer` — pick one and keep it in the repo only.
- [x] **Task 3 — ProductsRepository: writes** (AC: #3, #4)
  - [x] `put_product(product)` (idempotent PutItem keyed by `productId`) and `batch_put(products)` (BatchWriteItem in chunks of 25, with unprocessed-items retry).
- [x] **Task 4 — Seed data + entrypoint** (AC: #3, #5)
  - [x] `backend/scripts/__init__.py` + `backend/scripts/seed.py`: generate ~100–500 deterministic synthetic Products (fixed seed / index-derived ids like `p-0001`) across ≥4 categories with varied names, descriptions, prices (cents), and image URLs (placeholder host is fine — `available` mostly true, some false). No `Math.random`-style nondeterminism; deterministic so re-runs overwrite.
  - [x] `seed.py` `main()`: call `ProductsRepository.ensure_table()` then `batch_put(products)`; print a summary (`seeded N products across M categories`). Runnable as `python -m scripts.seed`.
- [x] **Task 5 — Tests (moto)** (AC: #6)
  - [x] Add `moto` to `[project.optional-dependencies].dev` in `backend/pyproject.toml`.
  - [x] `backend/tests/test_products_repository.py`: under `moto`'s `mock_aws`, assert `ensure_table()` creates the table + both GSIs (describe), is a no-op on second call, `put_product`/`batch_put` write items with `listingPk` and integer `price`, and round-trips a `Product`.
  - [x] `backend/tests/test_seed.py`: run the seed against `mock_aws`, assert count is in range and stable after a second run (idempotent), and ≥4 distinct categories exist.
- [x] **Task 6 — Verify locally** (AC: #5)
  - [x] With the stack up (`docker compose up -d`), run the seed and confirm `GET /health/deep` → `tableCount ≥ 1`; spot-check an item via a repo scan or the AWS CLI against `http://localhost:8001`.

### Review Findings

*Code review 2026-07-06 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). All 7 ACs + AD-1/3/4/6 satisfied; no critical/data-loss bugs. Severity set at triage.*

- [x] [Review][Patch] MED — Test fixtures monkeypatch `ddb_module.get_dynamodb_client`, but `products.py` imported the name directly, so the patch is dead code; tests pass only via `mock_aws` + default region [backend/tests/test_products_repository.py, test_seed.py] — patch the name where used (or import the module) and set `AWS_DEFAULT_REGION` in the fixture. (blind)
- [x] [Review][Patch] MED — `ensure_table` waits on `table_exists` only, not GSI `IndexStatus`; docstring claims GSIs ACTIVE. PLP queries (1.3+) can race on real AWS [backend/app/repositories/products.py:74-75] — poll `describe_table` until both GSIs are ACTIVE. (blind+edge)
- [x] [Review][Patch] MED — `batch_put` UnprocessedItems retry loop has no cap/backoff → can hot-spin/loop forever under throttling [backend/app/repositories/products.py:123-126] — add max-retry cap + small backoff, raise if still unprocessed. (blind+edge)
- [x] [Review][Patch] MED — GSI test asserts only index *names*, not key schema/attr types (the point of this story); idempotency test can't prove no-op [backend/tests/test_products_repository.py] — assert price=N + both GSI KeySchemas; spy that `create_table` is called once across two `ensure_table()` calls. (blind+auditor)
- [x] [Review][Patch] LOW — `count()` scan is eventually consistent; seed's printed count can under-report on AWS [backend/app/repositories/products.py:137-148] — use `ConsistentRead=True`. (blind+edge)
- [x] [Review][Patch] LOW — seed comment drift ("500–19,900" vs actual max 19,999) + `_NOUNS[category]` unguarded lookup if `CATEGORIES` edited [backend/scripts/seed.py] — fix comment; guard the noun lookup. (blind+edge)
- [x] [Review][Defer] LOW — `ensure_table` accepts an existing table with a mismatched schema (no compare) [backend/app/repositories/products.py:36-38] — deferred; acceptable for POC, revisit if schemas evolve.
- [x] [Review][Defer] LOW — `_from_item` raises bare `KeyError` on an item missing an attribute [backend/app/repositories/products.py:101-111] — deferred; repo owns all writes so unreachable now.
- [x] [Review][Defer] LOW — runtime image ships the seed script (`COPY scripts`) [backend/Dockerfile:9] — deferred; deliberate so the documented `docker compose exec api python -m scripts.seed` works.

*Dismissed as noise (4): `get_dynamodb_client` lru_cache pins a client (by-design — settings are process-constant; tests clear the cache); DynamoDB Number precision / oversized price (prices are small cents, unreachable); `get_product("")` ValidationException (unreachable edge); "idempotency scoped to fixed catalog" (documented overwrite behavior).*

## Dev Notes

### Architecture patterns and constraints (MUST follow)

- **AD-4 catalog query strategy** — the whole point of this table is the two GSIs the PLP will use next: `gsi_category` (category facet + price sort + pagination) and `gsi_listing` (unfiltered listing + price sort). Every item MUST carry `category`, `price`, and a constant `listingPk="PRODUCT"` or it won't appear in the indexes. Get the key schema exactly right now — later stories query it. [Source: ARCHITECTURE-SPINE.md#AD-4]
- **AD-3 one aggregate, one table, one owner** — `ProductsRepository` is the sole owner of the `Products` table. No other module reads/writes it directly. [Source: ARCHITECTURE-SPINE.md#AD-3]
- **AD-1 ports & adapters** — boto3 stays inside `app/repositories/`. The seed script imports the repository, not boto3. The domain `Product` model has no DynamoDB-specific shapes. [Source: ARCHITECTURE-SPINE.md#AD-1]
- **AD-6 money as integer minor units** — `price` is an int in cents everywhere; never a float. In DynamoDB it's a Number attribute serialized as a string (`{"N": str(price)}`). [Source: ARCHITECTURE-SPINE.md#AD-6]
- **AD-8 config** — table name from `settings.products_table`; endpoint/creds already handled by `get_dynamodb_client()`. No new env branching. [Source: ARCHITECTURE-SPINE.md#AD-8]

### Building on Story 1.1 (previous story — done & verified)

- Reuse `app/repositories/dynamodb.py::get_dynamodb_client()` — it already applies the endpoint override + botocore timeouts. Do NOT construct a second boto3 client.
- `Settings` (in `app/core/config.py`) already has `products_table` (default `"Products"`). GSI names (`gsi_category`, `gsi_listing`) are conventions — hardcode them as repository constants.
- `CamelModel` base exists in `app/models/__init__.py` — subclass it for `Product`.
- **dynamodb-local gotcha (from 1.1 verification):** the container runs as `user: root` so it can persist to its volume; it's reachable at `http://dynamodb-local:8000` inside compose, `http://localhost:8001` from the host. `list_tables()` works (verified). Table creation waiters work against dynamodb-local.
- Backend deps are installed in `backend/.venv` (Python 3.13). Run tests with `.venv/Scripts/python -m pytest`.
- **Commit policy:** fine-grained — likely one commit for the repository+model, one for the seed, one for tests (or grouped sensibly); review/verification fixes as their own `fix(...)` commits. Propose and wait for approval before committing.

### Stack notes

- `moto` is the standard library for mocking AWS/DynamoDB in Python tests — add it to dev deps and use `@mock_aws` (moto ≥ 5 uses the unified `mock_aws` decorator/context manager). Tests then run with no real/local DynamoDB.
- BatchWriteItem caps at 25 items/request; chunk the seed and retry `UnprocessedItems`.
- Use the DynamoDB **waiter** `table_exists` after create so GSIs are ACTIVE before returning.

### Project Structure Notes

- New files: `app/models/product.py` (or extend `app/models/__init__.py`), `app/repositories/products.py`, `backend/scripts/__init__.py`, `backend/scripts/seed.py`, `backend/tests/test_products_repository.py`, `backend/tests/test_seed.py`. Modified: `backend/pyproject.toml` (add `moto`).
- No frontend changes in this story. No API endpoints yet — the PLP endpoints come in Stories 1.3–1.6 and will consume this repository.
- Do NOT pull PLP query logic (search/facet/sort/pagination) into this story — that's 1.3–1.6. This story only provisions + seeds.

### References

- [Source: _bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md#AD-3, #AD-4, #AD-6, #AD-1, #AD-8]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- [Source: _bmad-output/implementation-artifacts/1-1-project-scaffold-and-local-runtime.md — prior scaffold, config, dynamodb client]

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Claude Opus 4.8)

### Debug Log References

- `cd backend && .venv/Scripts/python -m pytest -q` → **15 passed** (8 from 1.1 + 7 new).
- Fixed a test-fixture teardown bug: `cache_clear()` was called on the monkeypatched lambda; now captures the original `get_dynamodb_client` before patching.
- Live: `docker compose up -d --build api` → `docker compose exec api python -m scripts.seed` → **240 products, 6 categories**. `/health/deep` → `tableCount 1`. Re-ran seed → still 240 (idempotent). `get_product('p-0001')` round-trips with integer price 637.

### Completion Notes List

- `Product` domain model (`CamelModel`, price `int` cents ≥ 0) — AD-5/AD-6.
- `ProductsRepository` is the sole owner of the Products table (AD-1/AD-3), reusing `get_dynamodb_client()`. `ensure_table()` creates PK=`productId` + `gsi_category` (category/price) + `gsi_listing` (listingPk="PRODUCT"/price), PAY_PER_REQUEST, ProjectionType ALL, and waits for ACTIVE; idempotent (describe-then-create, ResourceInUseException swallowed). Item mapping (incl. `listingPk`) lives only in the repo.
- `put_product` (idempotent upsert) + `batch_put` (25/req, retries UnprocessedItems); `get_product`/`count` read helpers.
- `scripts/seed.py` — deterministic catalog (240 products = 6 categories × 40, index-derived ids `p-NNNN`, spread prices, ~1/11 out of stock). Re-runnable → overwrites, count stable.
- Tests use `moto[dynamodb]` (`mock_aws`); added to dev deps.
- Backend Dockerfile now also `COPY scripts ./scripts` so `docker compose exec api python -m scripts.seed` works in-container.
- Scoped: no PLP query logic (that's Stories 1.3–1.6); no API endpoints, no frontend changes.

### File List

- backend/app/models/product.py (new)
- backend/app/repositories/products.py (new)
- backend/scripts/__init__.py (new)
- backend/scripts/seed.py (new)
- backend/tests/test_products_repository.py (new)
- backend/tests/test_seed.py (new)
- backend/pyproject.toml (modified — add moto[dynamodb] dev dep)
- backend/Dockerfile (modified — COPY scripts)

### Change Log

- 2026-07-06: Implemented Story 1.2 — Products table + gsi_category/gsi_listing (AD-4) via ProductsRepository, idempotent provisioning + deterministic synthetic seed of 240 products (FR-16), moto tests. Backend 15/15 tests pass. Verified end-to-end against dynamodb-local (seeded 240, tableCount 1, idempotent re-run).
- 2026-07-06: Code review — 0 critical, all 7 ACs + AD-1/3/4/6 satisfied. Applied 6 patches (test-isolation monkeypatch fixed to patch-where-used + region pin; ensure_table now waits for GSIs ACTIVE; batch_put capped-backoff retry; strengthened GSI key-schema + idempotency-no-op tests; count ConsistentRead; seed comment/guard). 3 deferred, 4 dismissed. Re-verified live (240 products, tableCount 1). Story **done**. File List += docker-compose unchanged; modified products.py, seed.py, both test files.
