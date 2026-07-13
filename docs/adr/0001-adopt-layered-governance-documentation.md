# ADR-0001: Adopt layered governance documentation

- **Status:** Accepted
- **Date:** 2026-07-13
- **Constitutional articles:** VIII (Justice requires transparency); Prime Directive

## Context

ARGUS is a constitutional system: its value depends on every contributor — human or AI agent — making decisions that reinforce the same epistemic guarantees. Without a durable, ordered set of governing documents, those guarantees would live in individual memory and erode with every onboarding, handoff, or agent session.

## Decision

We will govern the repository through four documentation layers, each grounding the one below it:

```
docs/foundation/PROJECT_BRIEF.md            — onboarding: why ARGUS exists
docs/foundation/ENGINEERING_CONSTITUTION.md — governance: binding engineering law
AGENTS.md                                   — behavior: how engineers and AI agents work here
docs/adr/                                   — decisions: the architectural record
```

Implementation sits beneath all four. Lower layers must comply with higher layers; conflicts resolve upward, with the Constitution supreme. The brief is the source the Constitution elaborates; AGENTS.md operationalizes both for day-to-day work; ADRs record how specific architectural questions were settled within those constraints.

## Consequences

- Every contributor and agent has a single, ordered reading path before making changes.
- Constitutional review of pull requests has a citable reference document.
- Changes to the Constitution or the brief require an ADR, adding friction — deliberately.
- Documentation must be kept consistent across layers; drift between layers is a defect.

## Alternatives considered

- **Single monolithic README** — rejected: mixes onboarding narrative, binding law, agent behavior, and point-in-time decisions, making the binding parts unenforceable and the record unmaintainable.
- **Wiki or external documentation** — rejected: governance must version with the code it governs and travel with every clone (Article VIII — auditable by external parties).
