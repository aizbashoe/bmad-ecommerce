# Reworking Already-Shipped Stories

How to add work that changes, restyles, or redoes stories that are already `done` — **without
reopening the completed stories**. This is the pattern used for the PLP restyle (Epic 5 / story
5.1) after the UX phase landed, and for the category-badge tweak (a `bmad-quick-dev` one-shot).

> **The core rule:** a `done` story stays `done`. New work on shipped code is modeled as **new
> work** — a new story (or an ad-hoc one-shot), never an edit to a closed story's status. Reopening
> `done` stories desyncs the sprint tracker and erases the audit trail. `bmad-create-story` will even
> refuse to create a story in a `done` epic.

---

## 1. First, classify the change

| The change is… | Route it as… | Skill |
|----------------|--------------|-------|
| A **bug** in shipped code (behavior is wrong) | a fix, committed as its own `fix(...)` — usually surfaced by `code-review` or a deferred item | `bmad-code-review` / direct fix |
| A **small, self-contained tweak** (cosmetic, one concern, no epic ceremony) | an **ad-hoc one-shot** with a `spec-*.md` trace, not a sprint story | `bmad-quick-dev` |
| An **enhancement / restyle / re-do** of a shipped feature (new ACs, real scope) | a **new story** in a new or existing epic | `bmad-create-story` → `dev-story` → `code-review` |
| A **mid-sprint scope change** to stories not yet done | a course correction | `bmad-correct-course` |

If it has its own acceptance criteria and is more than a few lines, it's a **story** (next section).
If it's a quick visual/ad-hoc change, prefer the `bmad-quick-dev` one-shot (see §5).

## 2. Give the new story a home (don't reopen the old epic)

The restyle/redo does **not** belong to the epic that originally shipped the code — that epic is
`done`. Pick one:

- **A new epic** — cleanest when the work is a new theme (e.g. "Storefront UX Alignment"). Add it to
  `epics.md` and `sprint-status.yaml`. This is what Epic 5 did for the PLP restyle.
- **An existing, still-open epic** — only if the work genuinely fits that epic's charter.

Never add the story under the completed epic and flip it back to `in-progress` — that rewrites
history and confuses "what shipped when."

### Wiring it into the tracker

1. **`epics.md`** — add the epic to the `## Epic List` overview **and** a detailed `## Epic N`
   section with the story's user-story + BDD acceptance criteria. State plainly if it carries **no
   new FRs** (a restyle covers existing FRs). Note if it's **pulled forward** out of roadmap order.
2. **`sprint-status.yaml`** — add `epic-N: backlog`, `N-1-<slug>: backlog`, and
   `epic-N-retrospective: optional`. `create-story`/`dev-story` will advance these
   (`backlog → ready-for-dev → in-progress → review → done`) as usual.
3. Then run the normal cycle: `create-story` → `dev-story` → `code-review` → commits.

## 3. Write the story to PROTECT the shipped behavior

A redo's biggest risk is a **regression** — silently dropping behavior the original story
guaranteed. Defend against it in the story file:

- **State an explicit scope fence.** Spell out what is *in* scope and, just as importantly, what is
  **out** (e.g. "restyle only — no behavior change", "backend unchanged", "add-to-cart stays
  disabled"). The reviewers are told to treat fenced items as intentional, not defects.
- **List the invariants to preserve.** Enumerate the exact behaviors from the shipped story that
  must survive byte-for-byte (for the PLP: search reset, multi-category OR, cursor Load-more,
  latest-wins guard, empty/loading/error states, `<Link>` nav). Make "re-verify these" a task.
- **Read the file being changed.** `create-story` requires reading each UPDATE file and documenting
  *current state → what changes → what must be preserved*. Do not skip this — it's the top cause of
  redo regressions.
- **Fold in related deferred items.** A redo is the natural moment to clear `deferred-work.md`
  entries for that surface (5.1 folded in the PLP `invalid_cursor` reset). Cite them in the ACs.

## 4. Review, and expect "preservation" findings

Run `bmad-code-review` as usual. For a redo, the adversarial lenses focus on:

- the **removed-behavior audit** (did the rewrite drop a guard/branch the old code had?), and
- **new code** introduced by the redo (e.g. 5.1's `invalid_cursor` recovery and the result-context
  label both drew the only real findings).

Patch, defer, or dismiss as normal; record the outcome in the story's *Senior Developer Review (AI)*
section and push deferrals to `deferred-work.md`.

## 5. The lighter path: `bmad-quick-dev` one-shot

For a genuinely small, ad-hoc change to shipped code (no new ACs, no epic), skip the sprint
machinery: run `bmad-quick-dev`, which produces a `spec-*.md` trace in
`implementation-artifacts/` (route `one-shot`) and still goes through an adversarial review. The
category badge on PLP tiles was done this way (`spec-category-badge.md`). Use this when a full story
would be ceremony; use a story (§2–4) when the work has real acceptance criteria or spans layers.

## 6. Commit & log

- Commit fine-grained per the project policy (see [command-log.md](command-log.md)) — one commit per
  logical part; review fixes as their own `fix(...)` when the feature was committed before review.
- Record the `create-story`/`dev-story`/`code-review` runs in [command-log.md](command-log.md).
- If the redo changes how future work should be sequenced, capture it in memory (the PLP restyle
  decision lives in the `ux-adoption-plan` memory).

---

### Worked example — Epic 5 / Story 5.1 (PLP restyle)

The UX phase produced a design the already-shipped Epic 1 PLP didn't match. Instead of reopening
Epic 1 (six `done` stories):

1. Added **Epic 5: Storefront UX Alignment** to `epics.md` + `sprint-status.yaml` (no new FRs;
   pulled forward ahead of Epics 3–4).
2. Wrote story **5.1** as a **restyle-only** change with an explicit fence ("no behavior change, no
   backend change") and an enumerated list of Epic 1 behaviors to preserve; folded in the deferred
   PLP `invalid_cursor` reset.
3. Ran `dev-story` → `code-review` (Approve-with-patches: the two findings were both in the *new*
   code) → fine-grained commits. Epic 1 stayed `done` throughout.

*Related: [story-guide.md](story-guide.md) (the normal story cycle), [lifecycle.md](lifecycle.md)
(phase/skill reference), [command-log.md](command-log.md) (commands + commit policy).*
