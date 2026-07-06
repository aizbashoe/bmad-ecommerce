# Authoring & Integrating a New BMAD Skill

How to add a new capability to the BMAD toolset in this project — the anatomy of a skill,
the three ways to create one, how it gets registered/discovered, and how to integrate it
into the workflow. Companion to [lifecycle.md](lifecycle.md) (what the built-in skills do).

> **Terminology:** a BMAD "skill" is a Claude Code skill installed under `.claude/skills/<name>/`.
> You invoke it by name (e.g. *"Run bmad-create-story"*) or by its menu code.

---

## 1. Anatomy of a skill

Each skill is a folder under `.claude/skills/<skill-name>/`. From `bmad-create-story`:

```
.claude/skills/bmad-create-story/
├── SKILL.md            # the skill's prompt/instructions (the entry the model runs)
├── customize.toml      # the [workflow] block: activation steps, persistent_facts, paths, on_complete
├── template.md         # output template(s) the skill fills
├── checklist.md        # a validation/quality checklist the skill applies
└── discover-inputs.md  # a sub-instruction file the SKILL.md reads
```

Larger skills also have `steps/` (step-file architecture — one micro-file per step),
`references/`, and `scripts/` (helper Python run via `uv run`). Two conventions matter:

- **`SKILL.md`** starts with a description/frontmatter (name, when-to-use) and a `## On Activation`
  section that resolves customization, loads config, and greets — then a `<workflow>` body.
- **`customize.toml`** holds a `[workflow]` table (activation_steps_prepend/append, persistent_facts,
  paths, on_complete). It's resolved at runtime by `_bmad/scripts/resolve_customization.py`
  in base → team → user order (`customize.toml` → `_bmad/custom/<skill>.toml` → `_bmad/custom/<skill>.user.toml`).

### How skills are registered / discovered

The installer maintains a registry under `_bmad/_config/`:

| File | Role |
|------|------|
| `bmad-help.csv` | the menu catalog (`bmad-help` reads it): module, skill, display name, **menu code**, description, phase, output-location |
| `skill-manifest.csv` | installed skills manifest |
| `files-manifest.csv` | every installed file (for update/uninstall) |
| `manifest.yaml` | module/version manifest |

A skill is "known" to `bmad-help` and the loader when it's in `.claude/skills/` **and** in these
manifests. That's why you don't hand-edit these by hand — the tooling generates them (see §2).

---

## 2. Three ways to create a skill (pick by need)

### A. Customize / extend an existing skill — `bmad-customize` (BC) ✅ installed

For "change how a skill behaves" — add persistent facts, swap a template, insert an activation
hook, tweak a menu — **don't fork the skill**; use the customize skill. It writes overrides to
`_bmad/custom/` (never touching the installer-managed files) and verifies the merge.

```
Run bmad-customize
> Add a persistent fact to bmad-create-story: "our repo tracks _bmad-output/"; and
> swap its story template for docs/templates/our-story.md.
```

Output: TOML override files under `_bmad/custom/` — survive re-installs, layered by the resolver.
**Use this for 90% of "I want the skill to do X differently" needs.**

### B. Build a brand-new skill — the **BMad Builder** module (`bmb`)

Authoring a new skill/agent/workflow is what the **BMad Builder** module is for. It isn't
installed here (this project installed only `bmm`). Add it, then use its builder:

```bash
# add the builder module (same installer, extra module)
npx --yes bmad-method install --yes --action update \
  --directory "<repo>" --modules bmb --tools claude-code < /dev/null
```

Then invoke the builder skill (e.g. `bmad-workflow-builder` / the module's skill-builder) and
describe the skill — it scaffolds `SKILL.md` + `customize.toml` + steps/templates **and** wires
the `_bmad/_config` manifests + `bmad-help.csv` entry so the skill is discoverable. This is the
supported path — it handles registration for you.

### C. Hand-author a skill (full control / no builder)

If you'd rather write it directly (or can't add `bmb`):

1. Create `.claude/skills/<your-skill>/SKILL.md` following the shape of an existing skill:
   a description + `## On Activation` (resolve customization, load `_bmad/bmm/config.yaml`,
   greet) + a `<workflow>` body. Add `customize.toml` with a `[workflow]` block (copy a simple
   skill like `bmad-shard-doc` as a skeleton).
2. Add step/template/reference files as needed; put any Python helpers in `scripts/` and call
   them with `uv run`.
3. **Register it** so `bmad-help` and the loader see it: add a row to `_bmad/_config/bmad-help.csv`
   (module, skill, display-name, menu-code, description, phase, output-location) and entries to
   `skill-manifest.csv` / `files-manifest.csv`. (The builder in (B) does this automatically —
   hand-registration is fiddly, so prefer B for anything non-trivial.)
4. Verify: `Use the bmad-help skill` → your skill should appear; then invoke it by name.

---

## 3. Integrating the skill into this project

- **Invoke** it by name in Claude Code (*"Run <your-skill>"*) or via its menu code from `bmad-help`.
- **Place it in the flow:** if it's a phase/story-cycle step, add it to the "Skills used per phase / task"
  table in [command-log.md](command-log.md) and, if relevant, to [lifecycle.md](lifecycle.md).
- **Log usage:** per this project's convention, record the commands you run for the new skill in
  [command-log.md](command-log.md) (see [../../MEMORY note]).
- **Respect the architecture:** a skill that generates code must obey the same ADs
  (`ARCHITECTURE-SPINE.md`) and go through `bmad-code-review` + a fine-grained commit, like any story.

### ⚠️ Persistence & git (important here)

This project **gitignores `_bmad/` and `.claude/`** (they're regenerated by `npx bmad-method install`).
So a hand-authored skill under `.claude/skills/` or overrides under `_bmad/custom/` are **not tracked**
and would be lost on a clean checkout / re-install. To keep a custom skill:

- **Preferred:** keep it in a **module** you install (the `bmb`-built module is reinstallable), or
- Keep the skill's **source** in a tracked location (e.g. a committed `bmad-custom/` folder) and
  document the install/copy step in [command-log.md](command-log.md), or
- Relax `.gitignore` to track `_bmad/custom/` specifically if the overrides must live with the repo.

Decide this **before** investing in a custom skill, or it won't survive.

---

## 4. Checklist

- [ ] Is this really a *new* skill, or a **customization** of an existing one? (Prefer `bmad-customize`.)
- [ ] For a new skill: added the **`bmb`** module and used its builder (handles registration)?
- [ ] `SKILL.md` + `customize.toml` present; steps/templates as needed; helpers in `scripts/`.
- [ ] Registered in `_bmad/_config` (builder does this) — appears in `bmad-help`.
- [ ] Invocable by name; behaves per its workflow.
- [ ] Placed in the phase table (command-log.md) / lifecycle if it's part of the flow.
- [ ] **Persistence decided** given `_bmad/` + `.claude/` are gitignored.
- [ ] If it generates code: obeys the architecture spine, reviewed, committed fine-grained.

---

*Built-in skills and their inputs/outputs: [lifecycle.md](lifecycle.md). Adopting BMAD on an
existing codebase: [brownfield-guide.md](brownfield-guide.md).*
