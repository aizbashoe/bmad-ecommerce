# BMAD on an Existing (Brownfield) Project

How to adopt the BMAD method on a codebase that **already exists** — where you must first
capture reality, then plan and build *against* it. This complements the greenfield flow in
[README.md](../../README.md) / [lifecycle.md](lifecycle.md); the story-cycle mechanics in
[story-guide.md](story-guide.md) are identical once you reach implementation.

## Greenfield vs brownfield — what changes

| | Greenfield (this repo's origin) | Brownfield (existing code) |
|--|--------------------------------|----------------------------|
| Start from | An idea → brief → PRD → architecture | **The running code** → document it → *then* plan changes |
| Architecture step | Invent the spine | **Ratify** the spine from what's already built; flag divergence |
| Requirements | Full PRD for the whole product | A PRD/spec for the **enhancement**, scoped against existing behavior |
| First move | `bmad-product-brief` | **`bmad-generate-project-context` + `bmad-document-project`** |

The golden rule: **capture the as-built truth before you plan a single change**, so every
new story is grounded in how the system actually works — not how you wish it worked.

---

## Step 0 · Prerequisites

- A clean git working tree (commit/branch before BMAD writes anything).
- Node.js ≥ 20 (for the installer), plus the project's own toolchain (Python/uv, Node, Docker… as applicable).
- An AI-capable IDE (Claude Code, etc.).

## Step 1 · Install BMAD into the repo

```bash
npx --yes bmad-method install --yes \
  --directory "<abs-path-to-repo>" \
  --modules bmm --tools claude-code \
  --user-name "<you>" \
  --output-folder "_bmad-output" < /dev/null
```

- Pass **`--directory` and `--output-folder` explicitly** — a bare `--yes` install can stall on a prompt and leave a literal `{output_folder}` directory (a real gotcha we hit).
- Decide what to version-control up front (see **Suggestions**): typically gitignore the `_bmad/` engine + `.claude/` skills; track `_bmad-output/` artifacts.

## Step 2 · Generate project context (essential for brownfield)

```
Run bmad-generate-project-context        # menu code: GPC
```

- Scans the codebase and writes a **lean, LLM-optimized `project-context.md`** (conventions, structure, key rules).
- **Why it matters:** every BMAD skill auto-loads `**/project-context.md` as *persistent facts*. This is what makes create-story/dev-story respect your existing patterns instead of inventing new ones. Do this early; refresh it when conventions shift.

## Step 3 · Document the project (the as-built reference)

```
Run bmad-document-project                # menu code: DP  → choose Deep scan
```

- Produces `docs/` — `index.md`, source-tree, per-part architecture, API contracts, data models, dev/deploy guides, integration architecture. (See this repo's `docs/` for the exact shape.)
- Pick scan depth by size: **Quick** (structure/config only), **Deep** (reads key files — recommended), **Exhaustive** (every file; large/legacy migrations).
- Multi-part repos (e.g. `client/` + `server/`) are detected and documented per part.
- **Output is the anchor for everything next:** point the brownfield PRD and reviews at `docs/index.md`.

## Step 4 · Architecture review — ratify the spine from the code

```
Run bmad-architecture                     # menu code: CA  (brownfield: "ratify existing")
```

In brownfield mode, `bmad-architecture` **derives the architecture spine from the existing
codebase** rather than inventing one: it reads the real conventions (via `project-context.md`
+ `docs/`) and records them as invariants (ADs). Use it to:

- **Ratify** the patterns that are actually load-bearing (layering, data-access rules, contracts, money/units, auth) so future stories can't drift from them.
- **Surface divergences** — places where the code already contradicts itself or a stated rule. These become cleanup candidates or accepted exceptions.
- Establish the ADs that new work must obey, and a **Deferred** list of what you're deliberately *not* deciding yet.

Output: `ARCHITECTURE-SPINE.md` (status `final`) — the contract new stories reference. If a
proposed change would *break* a ratified AD, that's a signal to use `bmad-correct-course`.

## Step 5 · Plan the enhancement

Now plan the *new* work — scoped against the documented reality, not the whole system:

- **`bmad-prd` (PRD)** — a PRD for the enhancement; point it at `docs/index.md` as the codebase context so requirements reference existing behavior and call out what must not regress.
- **`bmad-ux` (CU)** — only if the change has meaningful UI.
- **`bmad-create-epics-and-stories` (CE)** — break the enhancement into epics/stories that build on existing components.
- **`bmad-check-implementation-readiness` (IR)** — verify the new PRD ↔ ratified architecture ↔ stories align before coding.

For a **small, self-contained change** you can skip the full plan — see the decision guide.

## Step 6 · Implement (same story cycle as greenfield)

```
Run bmad-sprint-planning                 # SP  → sprint-status.yaml
# then per story:
Run bmad-create-story  → bmad-dev-story  → bmad-code-review    # CS → DS → CR
```

Identical to [story-guide.md](story-guide.md). The difference is that create-story now pulls
brownfield context (`project-context.md`, `docs/`, the ratified spine, the real code), and
dev-story **extends existing files** — so its "read the files being modified" step is
critical: a story must leave the system working end-to-end, not just satisfy its ACs.

---

## Decision guide — how much process for a change?

| Change size | Path |
|-------------|------|
| One-line fix / tiny tweak | `bmad-quick-dev` (QQ) — intent-in, code-out; still obeys the ratified ADs |
| A feature (a few stories) | Enhancement PRD → epics/stories → story cycle (Steps 5–6) |
| Fuzzy / cross-cutting idea | `bmad-spec` (SP) to lock the WHAT first, then a story or quick-dev |
| Conflicts with existing plan/architecture | `bmad-correct-course` (CC) — reconciles and proposes plan changes |
| Big initiative | Full Steps 5–6 with a proper PRD + architecture pass |

(Same guidance as [story-guide.md](story-guide.md) §8 — see it for the ad-hoc/no-planning path.)

---

## Suggestions & best practices

- **Document before you change.** Steps 2–3 first, always. Planning on top of undocumented
  code is how brownfield stories break existing behavior.
- **Ratify, don't reinvent (Step 4).** Encode the conventions the code *actually* follows.
  Fighting them creates inconsistency; if a convention is bad, fix it as its own story.
- **Keep the docs alive.** Re-run `bmad-document-project` after significant changes (it
  supports re-scan and per-area deep-dive) and refresh `project-context.md` when patterns move.
- **Start with a thin vertical slice.** Prove the loop (document → story → dev → review) on one
  small, low-risk change before committing the team to the method.
- **Protect the working system.** Branch before dev-story; rely on `bmad-code-review` (it reads
  the diff against a `baseline_commit`) and run the existing test suite every story — regressions
  are the top brownfield risk.
- **Git hygiene.** Gitignore the `_bmad/` engine + `.claude/` skills (re-installable via
  `npx bmad-method install`); track `_bmad-output/` artifacts + `docs/` so the plan and as-built
  reference live with the code. Commit fine-grained; review/verification fixes as their own `fix(...)`.
- **Let `correct-course` handle drift.** When new requirements clash with the ratified
  architecture or an in-flight plan, run CC rather than silently diverging.

## The brownfield flow at a glance

```
install ─▶ generate-project-context ─▶ document-project ─▶ architecture (ratify)
        │                                                          │
        └───────────────────────────── plan enhancement ◀─────────┘
                     (PRD → epics/stories → readiness)
                                   │
                                   ▼
                 sprint-planning ─▶ create-story ─▶ dev-story ─▶ code-review ─▶ done
```

*Once the code is documented and the spine is ratified, brownfield development is just the
normal BMAD story cycle — grounded in reality instead of a blank page.*
