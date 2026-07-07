---
name: bmad-mermaid-diagrams
description: "Generates Mermaid diagrams for project documentation (architecture, data models, API flows, story lifecycle, epic/sprint status) and embeds them into the docs. Use when the user says 'add diagrams', 'generate mermaid', 'diagram the architecture/data model/flow', or after document-project to enrich the as-built docs."
---

# BMAD Mermaid Diagrams

**Goal:** Turn existing project documentation and planning artifacts into accurate **Mermaid**
diagrams embedded directly in the docs — no external render step required (GitHub, VS Code, and most
Markdown viewers render fenced ```mermaid blocks natively). Diagrams are generated *from the docs*,
so they stay honest to what's written, and they are inserted into a **marked, idempotent region** so
re-running updates them in place instead of duplicating.

**Your Role:** Documentation diagram author. You read the source material, choose the diagram types
that genuinely fit it, emit valid Mermaid, self-check the syntax against the lint rules, and write it
back into the target doc(s). You never invent structure the source doesn't support.

## Conventions

- Bare paths (e.g. `references/mermaid-patterns.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

**If the script fails**, read `{skill-root}/customize.toml` directly and use its `[workflow]` defaults,
then apply team/user overrides from `{project-root}/_bmad/custom/{skill-name}.toml` and
`{project-root}/_bmad/custom/{skill-name}.user.toml` in that order (missing files skipped; scalars
override, arrays append).

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context. Entries prefixed `file:`
are paths/globs under `{project-root}` — load their contents as facts.

### Step 4: Load Config

Load `{project-root}/_bmad/bmm/config.yaml` and resolve: `project_name`, `user_name`,
`communication_language`, `document_output_language`, `user_skill_level`, `planning_artifacts`,
`project_knowledge` (the docs root), and `date`. Missing keys → neutral defaults; never block.

### Step 5: Greet the User

Greet `{user_name}` in `{communication_language}`.

### Step 6: Execute Append Steps

Execute each entry in `{workflow.activation_steps_append}` in order.

Activation is complete. Do not begin the workflow until every activation step has run.

## Diagram catalog

The full catalog — when to use each type, a canonical template, and lint rules — is in
`references/mermaid-patterns.md`. **Read it before generating.** Summary of source → diagram mapping:

| Source material | Diagram type | Mermaid kind |
|-----------------|--------------|--------------|
| Architecture spine / layering (ports-and-adapters, services) | Component / layer | `flowchart LR` or `classDiagram` |
| Data models (tables, keys, GSIs, relationships) | Entity-relationship | `erDiagram` |
| API contracts / a request's path through the layers | Request flow | `sequenceDiagram` |
| Story/sprint status lifecycle (backlog→…→done) | State machine | `stateDiagram-v2` |
| Epics → stories → FRs coverage, or dependencies | Hierarchy / dependency | `flowchart TD` |
| Phase/skill lifecycle (BMAD process) | Process flow | `flowchart TD` |

## Execution

<workflow>

<step n="1" goal="Determine scope and targets">
  <action>If the user named a target (a doc path, "the architecture", "data model", "all docs"), use it. Otherwise, scan `{project_knowledge}` (docs root) and `{planning_artifacts}` and present the candidate docs + the diagram types each would support, then ASK which to generate.</action>
  <action>Resolve `{targets}` = the list of (source doc, diagram type(s)) pairs to produce.</action>
  <action>Confirm the OUTPUT mode with the user (default: embed into the source doc's own "## Diagrams" region). Alternatives: a single aggregate `{project_knowledge}/diagrams.md` index, or a doc-adjacent `*-diagrams.md`.</action>
</step>

<step n="2" goal="Extract structure from the source (no invention)">
  <action>Read `references/mermaid-patterns.md` in full.</action>
  <action>For each target, read the source doc(s) completely and extract only what is actually stated: components/layers and their allowed dependencies; entities with their keys/attributes and relationships; the ordered participants of a flow; the status values + transitions; the epic→story→FR hierarchy.</action>
  <critical>Diagrams must reflect the source. If the source doesn't state a relationship, do NOT draw it. Where the source is ambiguous, note it as an Open Question at the end rather than guessing.</critical>
</step>

<step n="3" goal="Generate valid Mermaid">
  <action>For each target, select the diagram kind from the catalog and emit Mermaid using the matching template in `references/mermaid-patterns.md`.</action>
  <action>Give every diagram a title line (Markdown heading above the block) and a one-sentence caption stating what it shows and its source doc.</action>
  <action>Keep diagrams readable: prefer &lt;= ~20 nodes per diagram; split a large system into focused views (e.g. one flow per endpoint) rather than one unreadable mega-diagram. Log any split you make.</action>
</step>

<step n="4" goal="Self-check syntax against the lint rules">
  <action>Apply the "Lint rules" checklist from `references/mermaid-patterns.md` to every block: correct kind header; quoted labels containing spaces/punctuation/`()`/`{}`; no reserved-word node ids; balanced brackets; valid arrow syntax for the kind; `erDiagram` cardinality tokens valid; `stateDiagram-v2` `[*]` start/end used correctly.</action>
  <action>If a rendering tool is available and the user opts in, run it to hard-validate (see `{workflow.render_command}`); otherwise rely on the lint checklist. Never require rendering — embedding valid source is the deliverable.</action>
  <action>Fix any issues and re-check before writing.</action>
</step>

<step n="5" goal="Write diagrams into the docs (idempotent)">
  <action>Insert each diagram inside a marked region so re-runs replace rather than duplicate. Use HTML-comment sentinels:
    `<!-- BMAD-MERMAID:START id=<slug> -->` … `<!-- BMAD-MERMAID:END id=<slug> -->`.
    If a region with the same `id` already exists in the target, REPLACE its contents; otherwise append a new region under a "## Diagrams" heading (create the heading if absent).</action>
  <action>Preserve all surrounding prose exactly; only the marked regions are touched.</action>
  <action>For aggregate mode, write/refresh `{project_knowledge}/diagrams.md` with a titled section per diagram + a top index; use the same sentinels per section.</action>
</step>

<step n="6" goal="Report and log">
  <action>Report: which docs were touched, how many diagrams of each kind, any diagrams split for readability, and any Open Questions where the source was ambiguous.</action>
  <action>Per this project's convention, remind the user to record the run in `docs/bmad/command-log.md` (or do it if asked).</action>
  <action>Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow.on_complete` — if non-empty, follow it as the final instruction.</action>
</step>

</workflow>

## Integration with BMAD doc generation

This skill is designed to run **after `bmad-document-project`** (DP) to enrich its as-built docs with
diagrams, and can also run standalone or after `bmad-architecture` / `bmad-create-epics-and-stories`.
The integration hook lives in `{project-root}/_bmad/custom/bmad-document-project.toml`
(`[workflow].on_complete`), which offers to hand off to this skill once DP finishes. See
[docs/bmad/mermaid-diagrams-skill.md](../../docs/bmad/mermaid-diagrams-skill.md) for the full design,
the registry row, and the install/persistence steps (this skill lives under the gitignored
`.claude/skills/`, so its tracked source is kept in `bmad-custom/`).
