---
baseline_commit: 437357da555b2c5bc681ee014b8e35087fbd425b
---

# Story 3.1: Establish an anonymous guest session

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an anonymous shopper,
I want the site to remember my cart without asking me to log in,
so that I can shop freely and keep my items across page loads.

## Acceptance Criteria

1. **Given** a first-time visitor with **no** guest token, **When** the client first needs a cart (`GET /cart`), **Then** the API issues an opaque `guestId` (UUID), creates an empty cart for it, and returns the cart **and** the `guestId` — echoed in an `X-Guest-Token` response header **and** in the body — so the client can store it (AD-2). Satisfies the "issue on first interaction" half of FR-7.
2. **Given** a returning request that **sends** `X-Guest-Token: <guestId>`, **When** it calls `GET /cart`, **Then** the API resolves the **same** cart for that `guestId` (get-or-create is idempotent) and echoes the same `guestId` back. Subsequent requests with the same token resolve to the same Cart — satisfies FR-7.
3. **Given** a request that sends a **malformed** `X-Guest-Token` (not a valid UUID), **When** it calls `GET /cart`, **Then** the API returns **400** with the `{error:{code,message}}` envelope (code `invalid_guest_token`) — never a 500 and never a silently-created cart under an arbitrary key.
4. **Given** AD-3, **Then** a `Carts` table keyed by `guestId` (PK) exists and **all** DynamoDB access to it is confined to a new `CartsRepository`; the service and HTTP layers hold no boto3.
5. **Given** AD-9 / NFR-1, **Then** the API holds no per-shopper state in memory (the cart lives only in DynamoDB keyed by `guestId`) and there is **no** login, account, password, or personal identity anywhere — the guest token is the only session concept.
6. **Given** the frontend, **Then** the typed client persists the `guestId` in `localStorage`, attaches it as `X-Guest-Token` on cart requests, and stores the token returned on the first response — so the cart survives reloads within the session (FR-8 groundwork).
7. **Given** this is the cart **foundation**, **Then** the cart returned is always **empty** here (`items: []`); adding line items is Story 3.2 and totals are Story 3.3 — do not implement them.

## Tasks / Subtasks

- [x] **Task 1 — Cart domain + API model (AC: 1, 7)** — `Cart(CamelModel)` in `models/cart.py`: `guest_id`, `items` (default `[]`; line-item type in 3.2). Serves as both domain + response model.
- [x] **Task 2 — CartsRepository (AC: 2, 4)** — `repositories/carts.py`: `ensure_table` (PK `guestId` S, PAY_PER_REQUEST, no GSI, wait for table_exists, idempotent), `get_cart` (GetItem → None on miss), `put_empty_cart` (PutItem), `_to_item`/`_from_item`; calls `dynamodb.get_dynamodb_client()` via the module.
- [x] **Task 3 — CartsService: resolve-or-create + token semantics (AC: 1, 2, 3, 5)** — `services/cart.py` `resolve_session(token)`: mint uuid4 when absent; validate `uuid.UUID` else `AppError invalid_guest_token` 400; get-or-create empty cart; return `(cart, guest_id)`.
- [x] **Task 4 — API route + token echo (AC: 1, 2, 3)** — `api/cart.py` `GET /cart` (X-Guest-Token header in, echo in response header + body); registered in `api/__init__.py`. Added `expose_headers=["X-Guest-Token"]` to CORS so the browser can read it.
- [x] **Task 5 — Local table provisioning (AC: 4)** — `scripts/provision.py` ensures Products + Carts (idempotent); `python -m scripts.provision`. No per-request table creation.
- [x] **Task 6 — Frontend guest session plumbing (AC: 6)** — `state/guestSession.ts` (guarded localStorage get/set, key `bmad_guest_token`); `client.ts` `Cart` type + `getCart()` (sends X-Guest-Token when present, persists the echoed token, preserves ApiError/timeout).
- [x] **Task 7 — Tests (AC: 1, 2, 3, 4)** — `test_carts_repository.py` (moto: PK guestId + no GSI, idempotent, None-on-miss, put/get roundtrip); `test_cart_api.py` (no token→UUID+header+items[]; same token→same cart; malformed→400).
- [x] **Task 8 — Verify (AC: all)** — backend `pytest -q` → 69 passed; frontend `tsc -b && vite build` clean; live (docker): provision created Carts; `/cart` issued a token, repeat resolved the same cart, malformed → 400, CORS expose-headers present.

## Dev Notes

### What this story is (and is not)
- **Is:** the cart *foundation* — the guest-session lifecycle (issue/resolve the opaque `guestId`), the `Carts` table + `CartsRepository`, a get-or-create empty cart, and the client-side token plumbing (store + send).
- **Is not:** line items (Story 3.2 — that's what wires the PDP's disabled Add-to-cart), totals (3.3), quantity/remove (3.4/3.5), or a cart **page** UI (3.3). The cart is always empty here.

### Token issuance / echo semantics (the crux — AD-2)
- `GET /cart` does **get-or-create**: **no** `X-Guest-Token` → mint a new UUID `guestId`, create an empty cart, return it; **with** a token → treat it as authoritative and resolve (or lazily create) that guest's cart. Always echo the resolved `guestId` in the `X-Guest-Token` **response header** (and body) so a first-contact client can capture it.
- **Validate** a provided token as a UUID and reject malformed input as `400 invalid_guest_token` — an opaque token the API minted is a UUID; this prevents arbitrary/injected partition keys (same "unbounded client input → clean 4xx, not 500" discipline as the 2.1 `product_id` cap). [Source: ARCHITECTURE-SPINE.md AD-2]
- Stateless (AD-9): no in-memory session map — the cart *is* the DynamoDB item keyed by `guestId`. Any instance serves any request.

### Backend patterns to reuse (read these first)
- `backend/app/repositories/dynamodb.py` — `get_dynamodb_client()` cached factory; call it **via the module** (`from app.repositories import dynamodb; dynamodb.get_dynamodb_client()`) so the moto monkeypatch in tests is honored (the Story 1.2 lesson).
- `backend/app/repositories/products.py` — `ensure_table` shape (create → wait; idempotent describe-then-return), `_to_item`/`_from_item`, `ClientError` handling. Carts is simpler: **no GSIs**, so drop `_wait_gsis_active`.
- `backend/app/core/config.py` — `carts_table` already defined (`CARTS_TABLE`, default `Carts`). Do not add config.
- `backend/app/core/errors.py` — `AppError` (+ `NotFoundError`); raise `AppError(code="invalid_guest_token", status_code=400)`. The envelope handler is already registered in `main.py`.
- `backend/app/api/__init__.py` — `api_router` aggregates routers; add `cart` alongside `health`, `products`.
- `backend/app/api/products.py` — router + `Depends(get_*_service)` + `Header`/`Response` param patterns.

### Frontend
- `frontend/src/api/client.ts` already has `get<T>` + `ApiError` + `API_BASE_URL`. `getCart` needs to **send and read a header**, which `get<T>` doesn't expose — add a small dedicated fetch in `getCart` (preserve the abort-timeout + `ApiError` envelope behavior) rather than overloading `get<T>`.
- `frontend/src/state/` is the spine's home for cart + guestId (localStorage). Guard `localStorage` access (may be unavailable) so a failure degrades to an in-memory/no-persistence path rather than throwing.
- No cart UI in this story; the exported `getCart`/`guestSession` are consumed by 3.2/3.3 (exported API, not dead code). Do not wire them into a page yet.

### Data model (Carts)
- `Carts`: PK `guestId` (S), `PAY_PER_REQUEST`, no GSI, no sort key. Item: `{ guestId: S, items: L (empty here) }`. Matches the spine ER (`CART { string guestId PK }`). Carts/Orders were called out as planned in `data-models-backend.md`; this implements Carts.

### Testing standards
- `pytest` + `moto` `mock_aws` for the repo (pin `AWS_DEFAULT_REGION=us-east-1`, monkeypatch `dynamodb.get_dynamodb_client`); FastAPI `TestClient` + `app.dependency_overrides[get_cart_service]` with a fake repo for the endpoint. No frontend test runner (deferred) — verify via build + the live docker check.

### Project Structure Notes
- New backend: `models/cart.py`, `repositories/carts.py`, `services/cart.py`, `api/cart.py`, `scripts/provision.py`, `tests/test_carts_repository.py`, `tests/test_cart_api.py`; edit `api/__init__.py`.
- New frontend: `state/guestSession.ts`; edit `api/client.ts`. No new deps. No backend change to Products/PDP. AD-3 preserved (new table + new repo).

### References
- [Source: epics.md → Epic 3 / Story 3.1] — FR-7, AD-2/AD-3/AD-9, ACs.
- [Source: ARCHITECTURE-SPINE.md] — AD-2 (opaque guestId via X-Guest-Token, localStorage), AD-3 (one table/one repo), AD-9 (stateless), Carts ER (`guestId` PK), source-tree (`core/ guest-token`, frontend `state/`).
- [Source: ux-designs/…/EXPERIENCE.md] — account-free identity constraint; cart persistence keyed by the guest token (FR-8); no login prompt ever.
- Code to reuse: `repositories/dynamodb.py`, `repositories/products.py`, `core/config.py`, `core/errors.py`, `api/__init__.py`, `api/products.py`, `frontend/src/api/client.ts`.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8

### Debug Log References

- `pytest -q` → 69 passed (62 prior + 7 new: 4 carts repo, 3 cart api).
- `npm run build` (`tsc -b && vite build`) → clean.
- Live (docker, rebuilt api): `python -m scripts.provision` → "Provisioned tables: Products, Carts"; `GET /cart` (no token) → 200 `{guestId:<uuid>, items:[]}` + `X-Guest-Token` header; repeat with that token → same guestId; `X-Guest-Token: not-a-uuid` → 400 `invalid_guest_token`; `Access-Control-Expose-Headers: X-Guest-Token` present for the `:5173` origin.

### Completion Notes List

- Cart foundation only: guest-session lifecycle + `Carts` table + `CartsRepository` + get-or-create empty cart + client token plumbing. **Scope fences held:** cart is always `items: []`; no line items (3.2), no totals (3.3), no cart page (3.3); Products/PDP untouched.
- **Token semantics (AD-2):** `GET /cart` get-or-creates — no header mints a new UUID; a provided token is validated as a UUID (malformed → 400 `invalid_guest_token`, not an arbitrary partition key) and resolved; the resolved id is echoed in the `X-Guest-Token` response header + body.
- **Cross-origin fix:** added `expose_headers=["X-Guest-Token"]` to the CORS middleware — without it the browser (`:5173`→`:8000`) cannot read the issued token. Verified live.
- Stateless (AD-9): cart is only the DynamoDB item keyed by `guestId`; no in-memory session. Table creation is a one-time `scripts.provision` step (not per-request).
- Frontend `getCart`/`guestSession` are exported plumbing consumed by 3.2/3.3 (not wired into UI yet — no cart page in this story).

### File List

- `backend/app/models/cart.py` (A) — `Cart` model.
- `backend/app/repositories/carts.py` (A) — `CartsRepository`.
- `backend/app/services/cart.py` (A) — `CartsService.resolve_session`.
- `backend/app/api/cart.py` (A) — `GET /cart` route.
- `backend/app/api/__init__.py` (M) — register cart router.
- `backend/app/main.py` (M) — CORS `expose_headers=["X-Guest-Token"]`.
- `backend/scripts/provision.py` (A) — ensure Products + Carts tables.
- `backend/tests/test_carts_repository.py` (A) — repo tests.
- `backend/tests/test_cart_api.py` (A) — endpoint tests.
- `frontend/src/state/guestSession.ts` (A) — localStorage token store.
- `frontend/src/api/client.ts` (M) — `Cart` type + `getCart()`; guestSession import.

### Change Log

- 2026-07-07: Implemented story 3.1 (anonymous guest session) — `GET /cart` issues/resolves an opaque `guestId` via `X-Guest-Token`, `Carts` table + `CartsRepository` (get-or-create empty cart), stateless + account-free, CORS expose-header, frontend token plumbing. Status → review.
- 2026-07-07: Code review (3-lens adversarial) — Approve-with-patches. 2 patches (UUID canonicalization; client clears rejected token) + test hardening. Tests 71 passed. Status → done.

### Review Findings

*Code review 2026-07-07 (Blind Hunter + Edge Case Hunter + Acceptance Auditor). Approve-with-patches. All 7 ACs + AD-1/2/3/5/9 satisfied. Severity at triage; reviewer in parens.*

- [x] [Review][Patch] **HIGH — client never clears a rejected guest token** [frontend/src/api/client.ts, frontend/src/state/guestSession.ts] — a bad token in `localStorage` (tampered, truncated, or from a re-seeded backend) wedges the session in a permanent `400 invalid_guest_token` with no self-recovery. Fix: add `clearGuestToken()` and call it on `invalid_guest_token` so the next call re-establishes a fresh session. (edge; blind)
- [x] [Review][Patch] **MED — guest token not canonicalized before use as the partition key** [backend/app/services/cart.py] — `guest_id = token` keyed on the raw string; `uuid.UUID()` accepts equivalent forms (uppercase, braces, `urn:uuid:`, dashless) → distinct partition keys for the same logical id, breaking FR-7 "same token → same cart", and echoed client input verbatim. Fix: `guest_id = str(uuid.UUID(token))` (validate + canonicalize); narrowed `except` to `ValueError`. Verified live (uppercase & dashless → same canonical id). (blind + edge + auditor)
- [x] [Review][Patch] LOW — test hardening [backend/tests/test_cart_api.py] — added an equivalent-form-UUID test (→ same `guestId`) and a first-contact-with-valid-token test; the malformed-token test now asserts `error.message` too. (auditor + blind)
- [x] [Review][Defer] LOW — `put_empty_cart` unconditional put = get-or-create race [backend/app/repositories/carts.py] — benign in 3.1 (empty carts are identical); becomes a cart-overwrite / line-item-loss race in 3.2. Action for 3.2: put with `ConditionExpression="attribute_not_exists(guestId)"` + re-read on conflict. (blind + edge)
- [x] [Review][Defer] LOW — `_from_item` discards stored `items` [backend/app/repositories/carts.py] — hard-codes `items=[]`; correct for 3.1, but Story 3.2 must parse the `L` list (+ a non-empty round-trip test). (blind)
- [x] [Review][Defer] LOW — no issuance enforcement / rate-limit on client-supplied UUIDs [backend/app/services/cart.py] — any valid UUID get-or-creates a cart (unbounded empty-cart writes); POC-acceptable (UUID4 entropy prevents cross-guest access); production wants a server-issued signed token and/or rate-limit. (blind)
- [x] [Review][Defer] LOW — `getCart` duplicates `get<T>`'s error-envelope/abort logic [frontend/src/api/client.ts] — ~15 copied lines; factor a shared `parseError(res)`/`request` helper so the envelope contract can't drift. (blind)
- [x] [Review][Defer] LOW — `ResourceNotFoundException` (unprovisioned Carts table) not distinguished from a generic 500 [backend/app/repositories/carts.py] — a `ClientError` is enveloped as `internal_error` 500 by the global handler (not a raw crash), but table-missing looks generic. Add specific handling if provisioning is ever skipped in a shared env. (edge)

*Dismissed (2): DynamoDB `ClientError` → already returns a well-formed 500 envelope via the global handler (differentiating throttling/not-found is the deferred item above, not a defect); a 2xx `/cart` response missing the `X-Guest-Token` header → the `expose_headers` CORS setting is present and verified live, so a stripped header is an environment misconfiguration, not a code path to handle.*
