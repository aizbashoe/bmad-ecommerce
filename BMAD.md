# BMAD Command Log & Runbook

A record of every command run to set up and drive BMAD in this repo, so the process is reproducible. Newest tasks are appended at the bottom.

- **BMAD version:** 6.10.0 (module `bmm`, tool `claude-code`)
- **Project root:** `c:\Work\TestRepo\TestBmad`
- **Output folder:** `_bmad-output/` (`planning-artifacts/`, `implementation-artifacts/`)
- **Shell:** Git Bash (POSIX). `uv` runs the Python helper scripts BMAD relies on.

## Skills used per phase / task

Which BMAD skill (Claude Code skill / menu code) drives each phase, and what it produced here:

| Phase / task | Skill | Menu code | Output artifact |
| --- | --- | --- | --- |
| Setup | `bmad-method install` (npm CLI, not a skill) | — | `_bmad/`, `.claude/skills/`, `_bmad-output/` |
| Menu / "what next" | `bmad-help` | `BH` | (guidance only) |
| 1 · Product Brief | `bmad-product-brief` | `CB` | `planning-artifacts/briefs/…/brief.md` |
| 2 · PRD | `bmad-prd` | `PRD` | `planning-artifacts/prds/…/prd.md` |
| (2 · UX — skipped) | `bmad-ux` | `CU` | *(not run — POC; review later)* |
| 3 · Architecture | `bmad-architecture` | `CA` | `planning-artifacts/architecture/…/ARCHITECTURE-SPINE.md` |
| 3 · Epics & Stories | `bmad-create-epics-and-stories` | `CE` | `planning-artifacts/epics.md` |
| 3 · Readiness check | `bmad-check-implementation-readiness` | `IR` | `planning-artifacts/implementation-readiness-report-*.md` |
| 4 · Sprint Planning | `bmad-sprint-planning` | `SP` | `implementation-artifacts/sprint-status.yaml` |
| 4 · Sprint Status | `bmad-sprint-status` | `SS` | (status summary) |
| 4 · Create Story | `bmad-create-story` | `CS` | `implementation-artifacts/{story-key}.md` |
| 4 · Validate Story | `bmad-create-story` (validate) | `VS` | story validation report |
| 4 · Dev Story | `bmad-dev-story` | `DS` | code in `backend/`, `frontend/`, etc. |
| 4 · Code Review | `bmad-code-review` | `CR` | review findings |
| 4 · QA E2E tests | `bmad-qa-generate-e2e-tests` | `QA` | test suite |
| 4 · Retrospective | `bmad-retrospective` | `ER` | retrospective notes |

Each `### Phase …` section below records the exact commands run for that phase, in order.

---

> Config note: `output_folder` must be bound at install time. A `--yes` install *without* `--output-folder` leaves the placeholder `{output_folder}` unresolved and creates a literal `{output_folder}/` directory — pass `--output-folder` explicitly (see setup step 3) to avoid it.

---

## 1. Setup / installation

```bash
# Explore installer options and valid IDE/tool IDs (informational)
npx --yes bmad-method install --help
npx --yes bmad-method install --list-tools

# Fresh non-interactive install (bmm module, Claude Code).
# NOTE: pass --directory AND --output-folder to avoid interactive prompts
# and the unresolved {output_folder} placeholder.
npx --yes bmad-method install --yes \
  --directory "C:\Work\TestRepo\TestBmad" \
  --modules bmm --tools claude-code \
  --user-name "artem" \
  --output-folder "_bmad-output" < /dev/null

# If you ran a fresh install without --output-folder and got a literal
# "{output_folder}" dir, re-run as an update to bind it, then remove the stray dir:
npx --yes bmad-method install --yes --action update \
  --directory "C:\Work\TestRepo\TestBmad" \
  --modules bmm --tools claude-code \
  --user-name "artem" \
  --output-folder "_bmad-output" < /dev/null
rm -rf "{output_folder}"

# Scaffold project source folders (created up front; Dev phase fills them in)
mkdir -p docs/stories backend frontend infra
```

Verify the install:

```bash
grep -in "output_folder" _bmad/bmm/config.yaml _bmad/core/config.yaml   # -> output_folder: _bmad-output
ls .claude/skills | wc -l                                               # -> 46 bmad-* skills
```

---

## 2. How to invoke BMAD (in Claude Code)

BMAD ships as Claude Code **skills** (`bmad-*`). Start any session with the menu:

```
Use the bmad-help skill
```

Then pick the next workflow by name or menu code. Phase spine:
`PRD` → `CU` (UX) → `CA` (architecture) → `CE` (epics/stories) → `IR` (readiness)
→ `SP` (sprint planning) → loop `CS → VS → DS → CR` per story.

---

## 3. Helper scripts used by skills

These are invoked automatically by skills, but recorded here for reference. Bind
`WS` to the current workflow's workspace folder first.

```bash
# Resolve a skill's customization/config block
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/<skill-name> --key workflow

# Memlog: canonical per-workflow memory / audit trail
uv run _bmad/scripts/memlog.py init   --workspace "$WS" --field topic="<topic>"
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type <decision|change|override|assumption|event> --text "<one-line gist + reason>"
```

---

## 4. Task log

### Phase 1 — Product Brief (skill: `bmad-product-brief`) — 2026-07-06

```bash
WS="_bmad-output/planning-artifacts/briefs/brief-bmad-ecommerce-2026-07-06"

uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-product-brief --key workflow

mkdir -p "$WS"
uv run _bmad/scripts/memlog.py init --workspace "$WS" \
  --field topic="Anonymous-user e-commerce storefront (PLP/PDP/cart/guest checkout/order summary)"

# Decisions captured (learning/POC, seed data, mock payment, full search+facets, no auth)
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Purpose: learning/POC to exercise BMAD + Python/AWS/TS stack. Keep ceremony low."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Catalog: seed/synthetic products in DynamoDB. No external PIM/integration for v1."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Payment: mock/simulated at checkout. No real gateway for v1."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "PLP: full search + facets + sorting IN scope (primary learning target). No accounts/auth."

# Assumptions resolved by user during review:
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "'Done' = runs locally (containerized API + local/emulated DynamoDB). AWS ECS deploy is a future enhancement, not v1."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Confirmed OUT of scope: promotions/discounts/tax/shipping calc (flat placeholder only), order history/returns/post-purchase, email/notifications."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Brief assumptions all resolved by user; brief ready to finalize."
```

**Output:** `_bmad-output/planning-artifacts/briefs/brief-bmad-ecommerce-2026-07-06/brief.md` (status: **complete**)

### Phase 2 — PRD (skill: `bmad-prd`) — 2026-07-06

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-prd --key workflow

WS="_bmad-output/planning-artifacts/prds/prd-bmad-ecommerce-2026-07-06"
mkdir -p "$WS"
uv run _bmad/scripts/memlog.py init --workspace "$WS" --field topic="PRD: Anonymous e-commerce storefront (learning/POC)"

# Decisions logged after drafting the PRD (Fast path from the brief)
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "PRD drafted from brief via Fast path. 16 FRs across 6 features (PLP/PDP/Cart/Checkout/Order Summary/Seed)."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Capabilities-only; tech choices deferred to Architecture. Cross-cutting NFRs: no-auth, local-first, stateless API, data minimization."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type assumption --text "14 assumptions indexed in PRD §10."

# After user review (facets=category only, payment success-only, etc.)
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "User confirmed: single-price products; category-only facet; success-only payment; no order-lookup; cart cleared after order."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type event --text "PRD finalized"
```

**Output:** `_bmad-output/planning-artifacts/prds/prd-bmad-ecommerce-2026-07-06/prd.md` (status: **final**)

### Phase 3 — Architecture (skill: `bmad-architecture`) — 2026-07-06

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-architecture --key workflow

WS="_bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06"
mkdir -p "$WS"
uv run _bmad/scripts/memlog.py init --workspace "$WS" \
  --field scope="Anonymous e-commerce storefront (PLP/PDP/cart/guest checkout/order summary)" \
  --field purpose="Build substrate for a learning/POC; feeds epics/stories" \
  --field altitude="initiative->features"

# Web-verified current stack versions (skill requires this; a finalize reviewer checks it):
#   Python 3.13, FastAPI 0.139.x, React 19.2, Vite 8.1, Node 22 LTS, amazon/dynamodb-local

# 10 decisions logged (paradigm, guest token, table strategy, catalog search, money,
# order immutability, API contract, config parity, versions, deployment envelope):
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Paradigm: Ports & Adapters (hexagonal-lite); DynamoDB only in repositories."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Guest identity: opaque guestId via X-Guest-Token; no auth."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Persistence: separate tables Products/Carts/Orders, one repo each."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Catalog search Option A: DynamoDB GSIs (category+listing) + FilterExpression text + cursor pagination."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Money = integer minor units; OrderTotal = Subtotal + flat shipping; no tax."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "Orders immutable; checkout clears cart atomically."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "API contract: OpenAPI source of truth; {error:{code,message}}; camelCase; opaque cursor."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "12-factor config; only local-vs-AWS diff is DynamoDB endpoint; stateless API."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type version --text "Python 3.13/FastAPI 0.139/boto3; Node 22/TS 5/React 19.2/Vite 8.1; amazon/dynamodb-local."
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type question --text "AWS ECS deploy deferred; docker-compose is v1 operational envelope."
```

# After user confirmed AD-4 = Option A (real DynamoDB GSIs):
uv run _bmad/scripts/memlog.py append --workspace "$WS" --type decision --text "AD-4 catalog search: user CONFIRMED Option A (real DynamoDB GSIs)."

# Deterministic spine lint (part of the Reviewer Gate) — 2 low false positives (REST path params):
uv run .claude/skills/bmad-architecture/scripts/lint_spine.py --workspace "$WS"

uv run _bmad/scripts/memlog.py append --workspace "$WS" --type event --text "spine finalized"
```

**Output:** `_bmad-output/planning-artifacts/architecture/architecture-bmad-ecommerce-2026-07-06/ARCHITECTURE-SPINE.md` (status: **final**)

### Phase 3b — Epics & Stories (skill: `bmad-create-epics-and-stories`) — 2026-07-06

This skill uses **step-file architecture** (4 steps, each with a `[C] continue` menu) rather than memlog.
Commands run:

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-create-epics-and-stories --key workflow
# ... 4 steps executed (validate prerequisites -> design epics -> create stories -> final validation),
#     each gated on user "C"; output built up in epics.md frontmatter stepsCompleted[].
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-create-epics-and-stories --key workflow.on_complete
```

**Output:** `_bmad-output/planning-artifacts/epics.md` — 4 epics, 16 stories, all 16 FRs covered (status: **complete**)

### Phase 3c — Implementation Readiness (skill: `bmad-check-implementation-readiness`) — 2026-07-06

Step-file workflow (6 steps: discovery → PRD analysis → epic coverage → UX alignment → epic quality → final assessment).

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-check-implementation-readiness --key workflow
# ... 6 steps executed; report built up section-by-section, appended via heredoc.
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-check-implementation-readiness --key workflow.on_complete
```

**Output:** `_bmad-output/planning-artifacts/implementation-readiness-report-2026-07-06.md`
**Verdict:** READY ✅ — 100% FR coverage (16/16), 0 critical / 0 major, 3 accepted minor concerns.

### Phase 4 — Sprint Planning (skill: `bmad-sprint-planning`) — 2026-07-06

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-sprint-planning --key workflow
# generated _bmad-output/implementation-artifacts/sprint-status.yaml (4 epics, 16 stories, 4 retros; all backlog)
uv run --with pyyaml python -c "import yaml; ..."   # validated: valid YAML, all statuses legal
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-sprint-planning --key workflow.on_complete
```

**Output:** `_bmad-output/implementation-artifacts/sprint-status.yaml` — sprint tracker, all items `backlog`, ready for the story cycle.

> Note: `yaml` is not in the base `uv` env — use `uv run --with pyyaml python ...` to parse the sprint file.

### Git setup — 2026-07-06

Repo initialized and pushed to GitHub (`github.com/aizbashoe/bmad-ecommerce`, private).
`.gitignore` excludes the BMAD engine (`_bmad/`, `.claude/`) and generated artifacts
(`_bmad-output/`); only app code + `README.md`/`BMAD.md` are tracked.

```bash
git init -b main
# .gitignore created (ignores _bmad/, .claude/, _bmad-output/, Python/Node/DynamoDB-local junk)
git add -A
git commit -m "chore: initialize repo with BMAD planning docs and runbook"   # f0bddd4
git remote add origin https://github.com/aizbashoe/bmad-ecommerce.git
git push -u origin main   # Git Credential Manager handled auth (no token needed)
```

**Commit policy (agreed):** **fine-grained commits — roughly one per FR or logical part,
NOT one big commit per story** (scaffold stories split by logical piece). Claude proposes
each commit and waits for user approval before running it. Conventional-commit messages.
Tracked: app code + `README.md`/`BMAD.md`; `_bmad/`, `.claude/`, `_bmad-output/` gitignored.

### Phase 4 — Story cycle

#### Story 1.1 — create-story (skill: `bmad-create-story`) — 2026-07-06

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-create-story --key workflow
# authored the story file; then updated sprint-status.yaml (epic-1 -> in-progress, 1-1 -> ready-for-dev)
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-create-story --key workflow.on_complete
```

**Output:** `_bmad-output/implementation-artifacts/1-1-project-scaffold-and-local-runtime.md` (status: **ready-for-dev**)
Covers walking skeleton: hexagonal FastAPI scaffold + React/Vite frontend + docker-compose with amazon/dynamodb-local; 7 ACs, 5 tasks.

#### Story 1.1 — dev-story (skill: `bmad-dev-story`) — 2026-07-06

```bash
uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-dev-story --key workflow
git rev-parse HEAD    # baseline_commit bc299c4 stamped into story frontmatter
# ... wrote backend/ (FastAPI hexagonal scaffold), frontend/ (React 19/Vite 8), docker-compose.yml, .env.example

# Backend verification (Python 3.13 venv):
cd backend && uv venv --python 3.13 .venv && uv pip install --python .venv -e ".[dev]"
.venv/Scripts/python -m pytest -q          # -> 7 passed
# Frontend verification:
cd frontend && npm install && npm run build # -> tsc + vite 8.1.3 build OK
```

**Output:** working walking skeleton. Backend 7/7 tests pass; frontend builds.
**Status:** story kept **in-progress** — code complete, but Task 4 (live `docker compose up`)
is BLOCKED (Docker daemon not running in this environment); live end-to-end is a manual step.

<!-- Next: run `docker compose up` to finish AC verification, then bmad-code-review, then commit per-part. -->
