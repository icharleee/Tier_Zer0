# ARGUS

**Cognitive infrastructure for reconstructing reality from fragmented evidence.**

> "The greatest obstacle to justice is not the absence of evidence.
> It is the fragmentation of truth."

ARGUS helps human investigators organize, connect, and reason about fragmented evidence — photographs, forensic reports, interviews, dispatch logs, financial records, timelines — so they can spend their cognitive effort on understanding rather than organizing.

ARGUS does **not** determine guilt, replace investigators, or make legal decisions. It stops before judgment. **Judgment belongs to humans.**

```
Evidence → Context → Reasoning → Understanding → Human Judgment
                                                 └── outside ARGUS
```

## Status

**Version 0.1 — Foundational Development.** This repository currently contains the project's governing documentation. Implementation follows from it, not the other way around.

## Start here

This project is governed through four documentation layers. Read them in order:

| Layer | Document | Role |
|-------|----------|------|
| 1 | [`docs/foundation/PROJECT_BRIEF.md`](docs/foundation/PROJECT_BRIEF.md) | Onboarding — why ARGUS exists, the problem, the philosophy |
| 2 | [`docs/foundation/ENGINEERING_CONSTITUTION.md`](docs/foundation/ENGINEERING_CONSTITUTION.md) | Governance — binding law for every schema, API, constraint, and test |
| 3 | [`AGENTS.md`](AGENTS.md) | Behavior — how engineers and AI coding agents work in this repo |
| 4 | [`docs/adr/`](docs/adr/README.md) | Decisions — the architectural record (ADRs) |

Lower layers must comply with higher layers. Where they conflict, the Constitution prevails (see [ADR-0001](docs/adr/0001-adopt-layered-governance-documentation.md)).

Supporting corpora (see [ADR-0008](docs/adr/0008-establish-arb-and-documentation-governance.md)): the [Lexicon](docs/glossary/LEXICON.md) — canonical vocabulary, normative everywhere — plus [Standards](docs/standards/README.md), [ISS research](docs/research/README.md), the [Academy](docs/academy/README.md), [Architecture artifacts](docs/architecture/README.md), and the [Domain Schema Specification](docs/domain/DOMAIN_SCHEMA_SPECIFICATION.md).

## Core commitments

- **Evidence before opinion** — every claim traces to source evidence. No provenance, no claim.
- **Observation ≠ Interpretation ≠ Hypothesis ≠ Judgment** — the analytical ladder is never collapsed.
- **Evidence is immutable** — retractions replace deletions; nothing disappears.
- **Unknowns and contradictions are explicit objects** — missing information and conflicting evidence are surfaced, never smoothed over.
- **Human judgment is final** — the AI organizes, summarizes, and proposes; it never decides.
- **Certainty must never exceed the evidence.**

## Contributing

All changes — human or AI-authored — are reviewed against the [Engineering Constitution](docs/foundation/ENGINEERING_CONSTITUTION.md). Architecturally significant decisions require an [ADR](docs/adr/README.md). If a requested change would violate the Constitution: stop, explain why, and propose a compliant alternative.
