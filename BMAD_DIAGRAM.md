# BMAD Lifecycle

The phase-based flow this project follows, from planning through the per-story build cycle.
Each node names the **BMAD skill** (menu code) that drives it.

```mermaid
flowchart TD
    Start([Idea]) --> Planning

    subgraph P1["Phase 1-2 · Planning"]
        direction TB
        Planning["Product Brief<br/><i>bmad-product-brief · CB</i>"]
        PRD["PRD<br/><i>bmad-prd · PRD</i>"]
        UX["UX design <i>(optional)</i><br/><i>bmad-ux · CU</i>"]
        Planning --> PRD --> UX
    end

    subgraph P3["Phase 3 · Solutioning"]
        direction TB
        Arch["Architecture spine<br/><i>bmad-architecture · CA</i>"]
        Epics["Epics &amp; Stories<br/><i>bmad-create-epics-and-stories · CE</i>"]
        Ready{"Implementation<br/>readiness<br/><i>IR</i>"}
        Arch --> Epics --> Ready
    end

    subgraph P4["Phase 4 · Implementation"]
        direction TB
        Sprint["Sprint planning<br/><i>bmad-sprint-planning · SP</i>"]
        Story["Create Story<br/><i>bmad-create-story · CS</i>"]
        Dev["Dev Story<br/><i>bmad-dev-story · DS</i>"]
        Test["Tests<br/><i>pytest / vitest</i>"]
        Review{"Code Review<br/><i>bmad-code-review · CR</i>"}
        Done(["Story done"])

        Sprint --> Story --> Dev --> Test --> Review
        Review -->|issues → fix| Dev
        Review -->|approved| Done
        Done -->|next story| Story
    end

    UX --> Arch
    Ready -->|READY| Sprint
    Ready -.->|gaps → revise| Arch
    Done -.->|epic complete| Retro["Retrospective<br/><i>bmad-retrospective · ER</i>"]
    Retro -.->|next epic| Story

    classDef gate fill:#fde68a,stroke:#b45309,color:#000;
    classDef terminal fill:#bbf7d0,stroke:#15803d,color:#000;
    class Ready,Review gate;
    class Done,Start,Retro terminal;
```

## The spine in words

| Step | Skill | Produces |
|------|-------|----------|
| **Planning** | `bmad-product-brief` → `bmad-prd` (+ optional `bmad-ux`) | brief → PRD (FRs/NFRs) |
| **Architecture** | `bmad-architecture` | the invariant "spine" (ADs) all code obeys |
| **Story** | `bmad-create-epics-and-stories` → `bmad-create-story` | epics → context-rich story files |
| **Dev** | `bmad-dev-story` | working code (red → green → refactor) |
| **Test** | pytest / vitest (inside dev-story) | passing unit/integration tests |
| **Review** | `bmad-code-review` | adversarial findings → patch / defer / dismiss |

## Key loops

- **Story cycle** — `Create Story → Dev → Test → Review` repeats once per story; Review sends work back to Dev on issues, or forward to *done*, then pulls the next story.
- **Readiness gate** — before any code, `IR` confirms PRD ↔ Architecture ↔ Stories align; gaps loop back to revise the plan.
- **Per-epic retrospective** — optional at each epic's end, feeding lessons into the next epic.

> Status of each story is tracked in `_bmad-output/implementation-artifacts/sprint-status.yaml`
> (`backlog → ready-for-dev → in-progress → review → done`).
