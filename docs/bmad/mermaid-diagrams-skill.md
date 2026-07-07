# The `bmad-mermaid-diagrams` Skill — Design & Details

Everything that defines the custom BMAD skill that generates Mermaid diagrams for the project's
documentation: what it does, its anatomy, the diagram catalog and lint rules, how it activates and
runs, how it integrates with `bmad-document-project`, how it's registered/discovered, and — because
`.claude/` and `_bmad/` are gitignored here — how its source is kept tracked and re-installed.

Companion to [authoring-skills.md](authoring-skills.md) (how to author *any* BMAD skill). This doc is
the concrete, worked instance of that guide.

---

## 1. What it does

Generates **Mermaid** diagrams *from* the existing docs and planning artifacts and embeds them back
into the docs as fenced ```mermaid blocks. GitHub, VS Code, and most Markdown viewers render Mermaid
natively, so there is **no external render step** — the deliverable is valid Mermaid source. Diagrams
are written into **marked, idempotent regions** so re-runs update in place instead of duplicating.

Design principles:

- **Honest to the source.** It diagrams only what the source states; ambiguities become Open
  Questions, never invented edges. (E.g. it draws the `Products` table because it exists, and holds
  off on `Carts`/`Orders` until Epics 3–4 build them.)
- **No render dependency.** Rendering to SVG/PNG (via `@mermaid-js/mermaid-cli`) is optional and
  opt-in; embedding validated source is the default and the contract.
- **Idempotent.** `<!-- BMAD-MERMAID:START id=… -->` / `END` sentinels bound each diagram; re-runs
  replace the region body, leaving surrounding prose untouched.

## 2. Anatomy (files)

Installed under `.claude/skills/bmad-mermaid-diagrams/`:

```
bmad-mermaid-diagrams/
├── SKILL.md                     # description + On Activation + <workflow> (the entry the model runs)
├── customize.toml               # [workflow] block: activation steps, persistent_facts, render_command, on_complete
└── references/
    └── mermaid-patterns.md      # the diagram catalog (templates per kind) + the lint checklist
```

- **`SKILL.md`** — frontmatter (`name`, `description` with trigger phrases) + a `## On Activation`
  section (resolve customization → prepend steps → persistent facts → load `config.yaml` → greet →
  append steps) + a `<workflow>` of six steps: scope → extract → generate → lint → write → report.
- **`customize.toml`** — the `[workflow]` table. Notable scalars: `render_command`
  (`npx --yes @mermaid-js/mermaid-cli`, optional hard-validate/render) and `aggregate_output`
  (`docs/diagrams.md`, where aggregate-mode writes). Resolved base→team→user by
  `_bmad/scripts/resolve_customization.py`.
- **`references/mermaid-patterns.md`** — six patterns (component/layer `flowchart`, data-model
  `erDiagram`, request-flow `sequenceDiagram`, status `stateDiagram-v2`, hierarchy/coverage
  `flowchart TD`, process `flowchart TD`), each with a canonical template, plus a **10-point lint
  checklist** the skill applies to every block (quoting labels, safe node ids, balanced brackets,
  kind-appropriate arrows, ER cardinality tokens, `[*]` in state diagrams, ≤~20 nodes, etc.).

## 3. Diagram catalog (source → diagram mapping)

| Source material | Diagram | Mermaid kind |
|-----------------|---------|--------------|
| Architecture layering (ports-and-adapters, AD-1) | component / layer | `flowchart LR` |
| Data models (tables, keys, GSIs) | entity-relationship | `erDiagram` |
| API contract / a request's path through layers | request flow | `sequenceDiagram` |
| Story or epic status | state machine | `stateDiagram-v2` |
| Epics → stories → FRs, or dependencies | hierarchy / dependency | `flowchart TD` |
| BMAD phase/skill process | process flow | `flowchart TD` |

## 4. Activation & workflow

**Activation** mirrors every BMAD skill: `resolve_customization.py --key workflow` →
`activation_steps_prepend` → `persistent_facts` (loads `**/project-context.md` if present) → load
`_bmad/bmm/config.yaml` (`project_name`, `project_knowledge` = docs root, `planning_artifacts`, …) →
greet → `activation_steps_append`.

**Workflow** (in `SKILL.md`):

1. **Scope** — take the user's target(s), or scan `project_knowledge` + `planning_artifacts` and ask
   which docs/diagram types to produce; confirm output mode (embed-in-doc vs aggregate
   `docs/diagrams.md`).
2. **Extract** — read `references/mermaid-patterns.md`, then read the source doc(s) and pull only the
   stated structure (components + allowed deps; entities + keys; flow participants; states; hierarchy).
3. **Generate** — pick the kind, emit Mermaid from the template, add a heading + one-line caption,
   split large systems into focused views.
4. **Lint** — apply the 10-point checklist; optionally hard-validate via `render_command`; fix + recheck.
5. **Write** — insert into `BMAD-MERMAID` sentinel regions (replace if the `id` exists, else append
   under a `## Diagrams` heading); prose untouched. Aggregate mode refreshes `docs/diagrams.md`.
6. **Report** — docs touched, diagram counts, any splits, Open Questions; remind to log the run.

## 5. Integration with BMAD doc generation

The skill is built to run **after `bmad-document-project` (DP)** to enrich its as-built docs, and can
also follow `bmad-architecture` or `bmad-create-epics-and-stories`, or run standalone.

- **Hand-off hook.** `_bmad/custom/bmad-document-project.toml` sets `[workflow].on_complete` to offer
  running `bmad-mermaid-diagrams` on the freshly generated docs once DP finishes. This is a
  customization override (the supported way to extend an existing skill — never fork it), merged over
  DP's base `customize.toml` by the resolver. A tracked copy lives at
  `bmad-custom/config/bmad-document-project.toml`.
- **Catalog registration.** A row in `_bmad/_config/bmad-help.csv` makes it discoverable via
  `bmad-help` and gives it menu code **`MD`** (see §7).
- **Docs.** Listed in the phase/skill tables of [command-log.md](command-log.md) and the docs index
  ([README.md](README.md)); the generated output lives in [../diagrams.md](../diagrams.md).

## 6. Invoking it

- By name: *"Run bmad-mermaid-diagrams"* / *"add mermaid diagrams to the architecture doc"*, or menu
  code **`MD`** from `bmad-help`.
- With a target argument: a doc path, a subject ("data model", "PDP flow"), or "all docs".
- After DP: accept the completion prompt to hand off automatically.

Worked output on this repo: [../diagrams.md](../diagrams.md) — backend layer view, `Products` ER,
PDP request-flow sequence, story-status state machine, and the BMAD phase flow.

## 7. Registration row (bmad-help.csv)

```
BMad Method,bmad-mermaid-diagrams,Mermaid Diagrams,MD,Generate Mermaid diagrams for documentation and embed them into the docs.,,[targets],anytime,bmad-document-project,,false,project-knowledge,*
```

Columns: `module, skill, display-name, menu-code, description, action, args, phase, preceded-by,
followed-by, required, output-location, outputs`.

## 8. Persistence & re-install ⚠️

`.gitignore` excludes `_bmad/` and `.claude/` (regenerated by `npx bmad-method install`). So the live
skill (`.claude/skills/bmad-mermaid-diagrams/`), the catalog row (`_bmad/_config/bmad-help.csv`), and
the DP override (`_bmad/custom/bmad-document-project.toml`) are **not tracked** and are lost on a
clean checkout or re-install. The **tracked source of truth** is therefore kept under `bmad-custom/`:

```
bmad-custom/
├── skills/bmad-mermaid-diagrams/        # full skill source (SKILL.md, customize.toml, references/)
└── config/bmad-document-project.toml    # the DP integration override
```

**Re-install steps** (after `npx bmad-method install`):

```bash
# 1) install the skill
cp -r bmad-custom/skills/bmad-mermaid-diagrams .claude/skills/

# 2) restore the document-project integration hook
mkdir -p _bmad/custom && cp bmad-custom/config/bmad-document-project.toml _bmad/custom/

# 3) re-register in the help catalog (append the row from §7, on its own line)
printf '%s\n' 'BMad Method,bmad-mermaid-diagrams,Mermaid Diagrams,MD,Generate Mermaid diagrams for documentation and embed them into the docs.,,[targets],anytime,bmad-document-project,,false,project-knowledge,*' >> _bmad/_config/bmad-help.csv

# 4) verify
#   Use the bmad-help skill  -> "Mermaid Diagrams (MD)" should appear
```

*A more durable alternative (future): package this as a proper `bmb`-built module so the installer
tracks it — see [authoring-skills.md](authoring-skills.md) §2B. For now the tracked-source + copy-on-
install approach keeps it in the repo.*

## 9. Checklist (was this skill authored correctly?)

- [x] `SKILL.md` (description + On Activation + `<workflow>`) and `customize.toml` present; catalog
  in `references/`.
- [x] Registered in `_bmad/_config/bmad-help.csv` (menu code `MD`); appears in `bmad-help`.
- [x] Integrated with doc generation (DP `on_complete` hand-off).
- [x] Invocable by name / `MD`; produced real output (`docs/diagrams.md`).
- [x] Placed in the docs (this file, command-log, README index).
- [x] **Persistence decided** — tracked source in `bmad-custom/` + documented re-install (given
  `_bmad/`+`.claude/` are gitignored).
- [x] Generates only from source (no invention); output is valid, lint-checked Mermaid.
