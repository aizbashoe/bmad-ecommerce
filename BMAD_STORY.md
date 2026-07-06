# BMAD Story Implementation Guide

How a single story goes from a line in `epics.md` to reviewed, tested, committed code —
what each step reads, what generates the code, and the exact commands.

See the whole lifecycle in [BMAD_DIAGRAM.md](BMAD_DIAGRAM.md); this doc zooms into **Phase 4 · the story cycle**.

---

## 0. Where the requirements come from

A story is never authored from scratch — it is **derived** from the planning artifacts produced in Phases 1–3. Each input feeds a specific part of the story:

| Input | Path | What the story pulls from it |
|-------|------|------------------------------|
| **Epics & Stories** | `_bmad-output/planning-artifacts/epics.md` | The story's title, user story (As a / I want / so that), acceptance criteria, and which FRs it covers |
| **PRD** | `…/prds/prd-bmad-ecommerce-*/prd.md` | The underlying functional requirement (FR-N) + non-functional constraints (NFRs) |
| **Architecture spine** | `…/architecture/…/ARCHITECTURE-SPINE.md` | The **ADs** (invariants) the code MUST obey — layering, key schemas, contracts, money format |
| **Sprint status** | `_bmad-output/implementation-artifacts/sprint-status.yaml` | Which story is next, and each story's state (`backlog → ready-for-dev → in-progress → review → done`) |
| **Previous story files** | `…/implementation-artifacts/<epic>-<n>-*.md` | Patterns, learnings, gotchas, files already created (so the new story reuses, not reinvents) |
| **The running code** | `backend/`, `frontend/` | Ground truth — the dev agent reads the actual files it will extend |

> **The flow of truth:** brief → PRD (FRs) → architecture (ADs) → epics (stories) → **story file** → code.
> Every acceptance criterion traces back to an FR; every technical rule traces back to an AD.

---

## 1. Create the story context — `bmad-create-story` (CS)

**What generates it:** the create-story skill reads the epic + PRD + architecture + the previous story, then writes a single **context-rich story file** — the dev agent's complete brief. It does NOT copy the epic; it enriches it with the exact ADs, file paths, versions, test approach, and "don't do this" boundaries so the dev agent can't drift.

**Invoke (in Claude Code):**
```
Run bmad-create-story for the next story
# or target one explicitly:
Run bmad-create-story for Story 1.3
```

**Reads:** `epics.md`, `prd.md`, `ARCHITECTURE-SPINE.md`, `sprint-status.yaml`, the prior story file.
**Writes:** `_bmad-output/implementation-artifacts/<story-key>.md` with sections: Story, Acceptance Criteria, **Tasks/Subtasks**, **Dev Notes** (architecture rules + prior-story learnings + gotchas), Dev Agent Record.
**Status:** `backlog → ready-for-dev`.

---

## 2. Implement — `bmad-dev-story` (DS)

**What generates the code:** the dev-story skill acts as the developer ("Amelia"). It follows the story file's **Tasks/Subtasks in order**, obeys the **Dev Notes / ADs**, and writes real code into `backend/` and `frontend/` using a **red-green-refactor** loop (write a failing test → minimal code to pass → refactor). It never invents scope outside the story's tasks.

**Invoke:**
```
Run bmad-dev-story for Story 1.3
```

**On start it records a `baseline_commit`** in the story frontmatter (the commit the work builds on) and flips status `ready-for-dev → in-progress`.
**Reads:** the story file (authoritative), the architecture spine, the existing code it extends.
**Writes:** source under `backend/` / `frontend/`, plus tests; updates the story's Tasks (checked off), File List, Dev Agent Record, Change Log.
**Status:** `in-progress → review` when all tasks pass their tests.

### The commands dev-story (and you) run to build + test

Backend (Python 3.13 venv already at `backend/.venv`):
```bash
cd backend
uv pip install --python .venv -e ".[dev]"      # install/refresh deps (adds moto, etc.)
.venv/Scripts/python -m pytest -q               # run the test suite (red → green)
```
Frontend (Node 22 / Vite 8):
```bash
cd frontend
npm install
npm run build                                    # tsc typecheck + vite build
```
DynamoDB-backed tests use **moto** (`mock_aws`) — no real AWS, no local DynamoDB needed for unit tests.

---

## 3. Test & verify live

Unit tests run inside dev-story (above). For stories with a runtime surface, also verify **end-to-end** against the real local stack:

```bash
docker compose up -d --build            # api + dynamodb-local + frontend
docker compose exec api python -m scripts.seed   # (once) load the 240-product catalog

# exercise the feature, e.g. Story 1.3:
curl 'http://localhost:8000/health/deep'         # {"dynamodb":"reachable","tableCount":1}
curl 'http://localhost:8000/products?limit=5'    # a page of products + nextCursor
# open the UI:
#   http://localhost:8000/docs      (API contract)
#   http://localhost:5173           (storefront PLP)
```

If Docker isn't available, unit tests + `npm run build` still validate the code; the live run is deferred (as it was for Story 1.1 until WSL/Docker was installed).

---

## 4. Review — `bmad-code-review` (CR)

**What it does:** runs **three adversarial review layers in parallel** — Blind Hunter (general defects), Edge Case Hunter (boundary conditions), Acceptance Auditor (ACs + AD compliance) — then **triages** every finding into `patch` / `defer` / `dismiss` with a severity you can act on.

**Invoke (ideally a fresh session / different model):**
```
Run bmad-code-review on Story 1.3
```

**Reads:** the working-tree diff since `baseline_commit`, the story file (as the spec), the architecture spine.
**Writes the summary to:** a **`### Review Findings`** section inside the **story file**, plus deferred items in `_bmad-output/implementation-artifacts/deferred-work.md`. (No standalone report file — the story file is the record.)
**You then choose:** apply all patches / a subset / leave as action items. Applied patches are re-tested.
**Status:** `review → done` once patches are resolved and no High/Medium remain.

---

## 5. Commit (fine-grained)

Commit policy for this repo (see `BMAD.md`):

- **Fine-grained** — roughly one commit per FR or logical part, **not** one big commit per story.
- **Review/verification fixes get their own `fix(...)` commit** (separate from the feature).
- Only app code + `README.md` / `BMAD*.md` are tracked; `_bmad/`, `.claude/`, `_bmad-output/` are gitignored.
- Claude **proposes each commit and waits for your OK** before running it.

```bash
git add backend/app/models/catalog.py backend/app/services/catalog.py backend/app/api/products.py
git commit -m "feat(backend): paginated GET /products via gsi_listing (FR-1)"
git add backend/tests/test_products_listing.py
git commit -m "test(backend): pagination + cursor round-trip tests"
git add frontend/src/pages/ProductListPage.tsx frontend/src/api/client.ts frontend/src/App.tsx
git commit -m "feat(frontend): PLP grid with load-more pagination"
git push origin main
```

---

## 6. Status lifecycle — how the status actually changes

Status lives in one file, `_bmad-output/implementation-artifacts/sprint-status.yaml`, under
`development_status:` as a flat map of `<story-key>: <status>` (plus `epic-N:` and
`epic-N-retrospective:` entries). **The skills edit this file** — each transition is a skill
rewriting one line (and bumping `last_updated`). The story file's own `Status:` header is kept
in lock-step.

```
                      bmad-create-story        bmad-dev-story         bmad-dev-story        bmad-code-review
                     (writes story file)     (starts implementing)   (all tasks pass)      (patches resolved)
   backlog ───────────▶ ready-for-dev ───────────▶ in-progress ───────────▶ review ───────────▶ done
                                                        ▲                        │
                                                        └──── code-review ◀───────┘
                                                         (issues → back to dev)
```

### Who sets what, and when

| Transition | Set by | Trigger / mechanism |
|------------|--------|---------------------|
| `backlog → ready-for-dev` | **bmad-create-story** | after it writes the story file; also flips `epic-N: backlog → in-progress` if it's the epic's first story |
| `ready-for-dev → in-progress` | **bmad-dev-story** | at start of implementation; also stamps `baseline_commit` into the story frontmatter |
| `in-progress → review` | **bmad-dev-story** | when every Task/Subtask is checked off and its tests pass (Definition-of-Done gate) |
| `review → in-progress` | **bmad-code-review** (or you) | if review raises issues that go back to the dev loop |
| `review → done` | **bmad-code-review** | when all patch/decision findings are resolved and no High/Medium remain |
| `epic-N: in-progress → done` | **you / manually** | when all of the epic's stories are `done` |
| `optional ↔ done` (retrospective) | **bmad-retrospective** | at epic end (optional) |

### Rules the skills enforce

- **No skips, no downgrades** — a skill verifies the *expected* current status before advancing (e.g. dev-story expects `ready-for-dev` or `in-progress`; code-review expects `review`). It won't silently move `done` back to `review`.
- **Comments + structure preserved** — the STATUS DEFINITIONS block and ordering in `sprint-status.yaml` are kept intact on every edit.
- **Two sources kept in sync** — `sprint-status.yaml` (the tracker) and the story file's `Status:` header always match; if only one can be updated, the skill warns.

### Check / drive status

```
Run bmad-sprint-status          # summarize where every story/epic stands, surface risks
Run bmad-sprint-planning        # regenerate/refresh the tracker from epics.md (re-detects statuses, never downgrades)
```
You can also just open `sprint-status.yaml` — it's human-readable and safe to eyeball.

**This project's current tracker (Epic 1):** `1-1 done`, `1-2 done`, `1-3 ready-for-dev`, rest `backlog`.

---

## 7. One-screen cheat sheet

```
# pick / prep the next story
Run bmad-create-story for the next story          # -> story file, ready-for-dev

# implement it
Run bmad-dev-story for Story <n>                   # -> code + tests, review
cd backend && .venv/Scripts/python -m pytest -q    # backend tests
cd frontend && npm run build                       # frontend typecheck+build

# verify live
docker compose up -d --build
docker compose exec api python -m scripts.seed
curl localhost:8000/products?limit=5 ; open http://localhost:5173

# review
Run bmad-code-review on Story <n>                  # -> findings in the story file
# (apply patches, re-run pytest)

# commit (after your OK), fine-grained
git add <files> && git commit -m "feat(...): ..."  ; git push origin main

# check progress
Run bmad-sprint-status
```

---

*Skills are invoked by name in Claude Code (they're installed under `.claude/skills/`). The model reads the story file + architecture spine as context and writes the code — you review and approve. Each phase's exact commands for THIS project are logged in [BMAD.md](BMAD.md).*
