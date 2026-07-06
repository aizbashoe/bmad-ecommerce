# Deferred Work

## Deferred from: code review of story 1-4-search-products-by-keyword (2026-07-06)

- **Cursor not bound to the search term** [backend `_encode_cursor`/`list_products`] — a cursor minted under `search=A` is structurally valid under `search=B` (encodes only the gsi_listing position). Practical trigger is removed by the frontend request-sequencing fix (cursor is always paired with the active term), but for robustness embed the filter (or a hash) in the opaque cursor and reject a mismatch.
- **Frontend discards the error envelope** [frontend/src/api/client.ts] — 400 `invalid_cursor` shows as a generic error and the bad cursor isn't reset. (Same as the Story 1.3 deferral.) Parse `{error:{code,message}}` and reset the cursor on `invalid_cursor`.
- **Search is substring, not token, and not Unicode-normalized** [backend searchText/contains] — `contains` matches contiguous substrings ("tee" ⊂ "canteen"; "red shirt" misses reordered text) and does no NFC/NFKC folding. Acceptable at POC scale; revisit with tokenization or a search engine (the AD-4 OpenSearch path) if search quality matters.

## Deferred from: code review of story 1-3-browse-catalog-with-pagination (2026-07-06)

- **`Limit` + `FilterExpression` under-fills pages** [backend/app/repositories/products.py] — DynamoDB applies `Limit` before a `FilterExpression`, so once Stories 1.4 (search) / 1.5 (category facet) add filters, a page can return fewer than `limit` matches (or zero) while more exist. Those stories must loop-to-fill (keep querying with the cursor until `limit` matches are accumulated) or filter above the repo. **Action for 1.4/1.5.**
- **`_from_item` bare `KeyError`** [backend/app/repositories/products.py] — an item missing a projected attribute raises an opaque KeyError. Unreachable now (repo owns all writes); harden with validation if external writers appear. (Same deferral as Story 1.2.)
- **Frontend discards the error envelope** [frontend/src/api/client.ts] — `get<T>` throws a generic message; the PLP can't distinguish a 400 stale/`invalid_cursor` from a network error. When the UI matures, parse `{error:{code,message}}` and reset the cursor on `invalid_cursor`.
- **Unbounded PLP item growth** [frontend/src/pages/ProductListPage.tsx] — "Load more" appends without a cap/virtualization; fine at the POC's ~240-item catalog, revisit for large catalogs.

## Deferred from: code review of story 1-2-provision-products-table-and-seed-catalog (2026-07-06)

- **`ensure_table` accepts an existing table with a mismatched schema** [backend/app/repositories/products.py] — describe-then-return does not compare KeySchema/GSIs. Fine for the POC; if the table schema ever evolves, add a schema-diff/migration check.
- **`_from_item` raises a bare `KeyError` on a partially-written item** [backend/app/repositories/products.py] — unreachable now (the repo owns all writes); harden with descriptive validation if external writers are ever introduced.
- **Runtime image ships the seed script** (`COPY scripts ./scripts`) [backend/Dockerfile] — deliberate so `docker compose exec api python -m scripts.seed` works; move the seed to a separate job/stage before any real deployment.


## Deferred from: code review of story 1-1-project-scaffold-and-local-runtime (2026-07-06)

- **`/docs` + `/openapi.json` exposed with no gating** [backend/app/main.py] — accepted for the local POC (docs are the contract source of truth). Before any shared/AWS deploy, gate docs behind config (e.g. disable when `dynamodb_endpoint` is empty / "prod").
- **Frontend container runs the Vite dev server** [frontend/Dockerfile] — fine for local-first walking skeleton. Add a `vite build` + static-serve stage before any real deployment.
- **`.env.example` `DYNAMODB_ENDPOINT` only valid inside the compose network** [.env.example] — `http://dynamodb-local:8000` doesn't resolve when running the backend directly on the host (that needs `http://localhost:8001`). Add a host-run variant/note if/when someone runs the API outside Docker.
