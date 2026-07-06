# Anonymous E-Commerce Storefront — BMAD Project Guide

This repository is set up to be built with the **BMAD-METHOD™** (Breakthrough Method for Agile AI-Driven Development), **v6.10.0**, using **Claude Code**. BMAD is an agentic, phase-based workflow: specialized AI personas (Analyst, PM, UX, Architect, Dev, Tech Writer) drive the project from idea → planning docs → sprint → implemented code.

BMAD is **already installed** in this repo (see [What's already set up](#3-whats-already-set-up)). This README tells **you** what to do next.

---

## 1. What we are building

A storefront for **anonymous (not-logged-in) users** with these flows:

| Area | Description |
|------|-------------|
| **PLP** | Product Listing Page — browse / search / filter the catalog |
| **PDP** | Product Detail Page — single product, images, price, add-to-cart |
| **Cart** | View / update / remove line items, subtotal |
| **Checkout** | Guest checkout — shipping + payment, no account required |
| **Order Summary** | Order confirmation / summary after checkout |

### Target architecture

- **Backend:** Python API (FastAPI recommended)
- **Infrastructure:** AWS — **ECS/Fargate** (containerized API) + **DynamoDB** (data store)
- **Frontend:** TypeScript UI (React recommended)
- **State:** Anonymous session/cart — no auth; cart keyed by a guest/session token

> Feed these constraints to the BMAD personas so the PRD and Architecture lock to your stack.

---

## 2. Prerequisites

- **Claude Code** (you're using it) — BMAD skills are installed here as Claude Code skills
- **Node.js** ≥ 20 (used by the BMAD installer)
- **[uv](https://docs.astral.sh/uv/)** — BMAD workflows increasingly run Python helper scripts via `uv run` *(detected during install ✓)*. Also your API's Python runner.
- **Python** ≥ 3.11 — for the API once stories start
- **Docker** — local ECS-style container builds
- **AWS CLI** — configured with credentials, for later deployment

---

## 3. What's already set up

Running the installer produced:

```
TestBmad/
├─ _bmad/                      # BMAD engine: modules (bmm, core), config, scripts
│  ├─ config.toml              #   installer-managed config (read-only)
│  └─ custom/                  #   your durable overrides live here
├─ _bmad-output/               # where BMAD writes artifacts
│  ├─ planning-artifacts/      #   brief, PRD, UX, architecture, epics/stories
│  └─ implementation-artifacts/#   sprint plan, stories, test suites
├─ .claude/skills/             # 46 bmad-* skills registered for Claude Code
├─ docs/                       # project knowledge (BMAD reads/writes here)
├─ backend/                    # Python API — created as stories are implemented
├─ frontend/                   # TypeScript UI — created as stories are implemented
├─ infra/                      # IaC for ECS + DynamoDB (CDK/Terraform)
└─ README.md                   # this file
```

> `backend/`, `frontend/`, and `infra/` are empty scaffolds — the Dev persona fills them in during Phase 4.

### The personas (who does what)

| Icon | Name | Role | Drives |
|------|------|------|--------|
| 📊 | Mary | Business Analyst | Research, product brief |
| 📋 | John | Product Manager | PRD |
| 🎨 | Sally | UX Designer | UX design |
| 🏗️ | Winston | System Architect | Architecture |
| 💻 | Amelia | Senior Engineer | Story implementation, code review |
| 📚 | Paige | Technical Writer | Docs, diagrams |

---

## 4. How to invoke BMAD in Claude Code

BMAD ships as **skills**. Start every session by invoking the help/menu skill:

```
Use the bmad-help skill
```

It prints a menu of every workflow with a short **menu code** (e.g. `PRD`, `CA`, `CS`). You then pick the next step by name or code — e.g. *"Run bmad-prd"* or *"Do PRD"*. Skills are phase-aware and tell you what comes next.

---

## 5. The workflow — four phases

Do the phases in order. **Phase 1 is optional**, Phases 2–4 are the spine.

### Phase 1 — Analysis *(optional but recommended)*

| Code | Skill | Output |
|------|-------|--------|
| `BP` | Brainstorm Project | brainstorming notes |
| `MR` / `DR` / `TR` | Market / Domain / Technical Research | research docs |
| `CB` | **Create Brief** (Mary) | product brief |

```
Run bmad-product-brief for an anonymous-user e-commerce storefront:
PLP, PDP, cart, guest checkout, order summary. Python API on AWS
ECS + DynamoDB, TypeScript React UI, no accounts / no auth.
```

### Phase 2 — Planning

| Code | Skill | Required | Output |
|------|-------|:--------:|--------|
| `PRD` | **Create/Edit/Review PRD** (John) | ✅ | `_bmad-output/planning-artifacts/prd*` |
| `CU` | **Create UX** (Sally) | — (do it: UI is central) | ux design |

```
Run bmad-prd. Break scope into epics/stories for PLP, PDP, Cart,
Checkout, Order Summary. NFRs: guest-only, AWS ECS + DynamoDB,
Python API, TypeScript UI.
```

### Phase 3 — Solutioning

| Code | Skill | Required | Output |
|------|-------|:--------:|--------|
| `CA` | **Architecture** (Winston) | ✅ | architecture spec |
| `CE` | **Create Epics and Stories** | ✅ | epics + stories |
| `IR` | **Check Implementation Readiness** | ✅ | readiness report |

```
Run bmad-architecture:
- Python FastAPI service, containerized for AWS ECS (Fargate)
- DynamoDB table design for products, carts, orders
- TypeScript/React frontend + API contract
- Guest session/cart token strategy (no auth)
```

Then `CE` to generate epics/stories, then `IR` to confirm PRD ↔ UX ↔ Architecture ↔ Stories are aligned before coding.

### Phase 4 — Implementation

Kick off, then run the **story cycle** one story at a time:

| Code | Skill | Role in cycle |
|------|-------|---------------|
| `SP` | **Sprint Planning** | once — produces the plan agents follow |
| `SS` | Sprint Status | anytime — where am I, what's next |
| `CS` | **Create Story** | cycle start — prep next story |
| `VS` | Validate Story | check story is ready before coding |
| `DS` | **Dev Story** (Amelia) | implement tasks + tests |
| `CR` | **Code Review** | review; back to `DS` if issues |
| `QA` | QA Automation Test | generate API/E2E tests |
| `ER` | Retrospective | optional at epic end |

```
   Sprint Planning (SP)  ── once
        │
        ▼
   ┌─────────────────────────────────────────────┐
   │  CS → VS → DS → CR                           │
   │  (create → validate → develop → review)      │
   │  fixes? back to DS.  epic done? ER, next epic│
   └─────────────────────────────────────────────┘
```

**Suggested epic order:** Foundation & infra scaffold → Catalog/PLP → PDP → Cart → Checkout → Order Summary.

---

## 6. Your checklist

- [x] Install prerequisites (Node ✓, uv ✓ detected) — still need Python, Docker, AWS CLI for later
- [x] BMAD installed (`_bmad/`, `.claude/skills/`)
- [ ] `bmad-help` → confirm the menu appears
- [ ] Phase 1: `CB` product brief *(optional)*
- [ ] Phase 2: `PRD`, then `CU` UX
- [ ] Phase 3: `CA` architecture → `CE` epics/stories → `IR` readiness
- [ ] Phase 4: `SP` sprint planning, then loop `CS → VS → DS → CR` per story
- [ ] Provision AWS (ECS cluster + DynamoDB tables) per the architecture doc
- [ ] Deploy container to ECS; connect the UI to the API

---

## 7. Handy anytime skills

- `bmad-quick-dev` (`QQ`) — intent-in, code-out for small standalone tasks
- `bmad-correct-course` (`CC`) — when a significant change forces a plan revision
- `bmad-document-project` (`DP`) — regenerate project docs
- `bmad-shard-doc` (`SD`) — split a doc that grew past ~500 lines
- `bmad-customize` (`BC`) — persistently tweak an agent/workflow (writes to `_bmad/custom/`)

---

## References

- BMAD docs: https://docs.bmad-method.org/  ·  https://bmadcode.com/
- Repo: https://github.com/bmad-code-org/BMAD-METHOD
- Config lives in `_bmad/` (installer-managed; put durable overrides in `_bmad/custom/`).

*BMAD-METHOD™ is a trademark of BMad Code, LLC.*
