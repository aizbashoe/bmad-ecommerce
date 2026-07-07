# BMAD Process Docs

Runbooks for how this project is built with the BMAD method. (The as-built *code*
documentation is one level up in [`docs/`](../index.md).)

| Doc | What it's for |
|-----|---------------|
| [command-log.md](command-log.md) | The reproducible command log + skills-per-phase table (every BMAD command run here) |
| [lifecycle.md](lifecycle.md) | The phase lifecycle diagram + a per-skill reference (name · role · input · output) |
| [story-guide.md](story-guide.md) | How a single story goes from `epics.md` to reviewed, committed code (incl. the no-planning/ad-hoc path) |
| [reworking-shipped-stories.md](reworking-shipped-stories.md) | How to add work that changes/restyles/redoes already-`done` stories without reopening them |
| [execution-report.md](execution-report.md) | Manifest of every step run and the actual files it produced |
| [brownfield-guide.md](brownfield-guide.md) | How to adopt BMAD on an existing (brownfield) codebase — setup, architecture review, suggestions |
| [authoring-skills.md](authoring-skills.md) | How to create a new BMAD skill (customize / BMad Builder / hand-author) and integrate it |
| [mermaid-diagrams-skill.md](mermaid-diagrams-skill.md) | Design & details of the custom `bmad-mermaid-diagrams` skill (diagram catalog, integration, re-install) |

Project overview: [../../README.md](../../README.md). Planning artifacts: `_bmad-output/planning-artifacts/`.
