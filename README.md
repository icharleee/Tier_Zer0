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

**Version 0.1 — Documentation Freeze; implementation phase (ADR-0015).** The governance foundation is complete and frozen: the Constitution governs, the Governance Council decides, the Ontology defines meaning, the Derivation Specification explains translation, the Schema defines structure, the Invariant Matrix defines enforcement, the code implements, the tests verify — nothing skips a layer, and no new foundational ADR is written unless implementation discovers a gap (Founder Resolution 006). Slice roadmap (AGC Session 007 — infrastructure keeps waiting; the ontology is still teaching): **1A ✔ → 1B ✔ → 1C ✔ → 1D ✔ → 2A Competing Interpretations ✔ → 2B Unknowns and evidentiary limits ✔ → 2C Contradictions ✔ → 2D Hypotheses → 1E storage + reconciliation → 1F API/UI**. The ladder's first two rungs exist: `OBS-000001 "Blue sedan visible."` and competing interpretations `INT-000001`/`INT-000002` over identical grounding — coexisting without epistemic preference, each carrying a structured uncertainty envelope and grounding snapshots. ARGUS preserves competing human meanings; it does not convert coexistence into comparison. The first acceptance test — a synthetic image ingested, identified, verified, activated, fully audited, and made Observation-eligible with zero invariant violations — **passes**, at the application layer and against the database's independent enforcement.

## Start here

This project is governed through four documentation layers. Read them in order:

| Layer | Document | Role |
|-------|----------|------|
| 1 | [`docs/foundation/PROJECT_BRIEF.md`](docs/foundation/PROJECT_BRIEF.md) | Onboarding — why ARGUS exists, the problem, the philosophy |
| 2 | [`docs/foundation/ENGINEERING_CONSTITUTION.md`](docs/foundation/ENGINEERING_CONSTITUTION.md) | Governance — binding law for every schema, API, constraint, and test |
| 3 | [`AGENTS.md`](AGENTS.md) | Behavior — how engineers and AI coding agents work in this repo |
| 4 | [`docs/adr/`](docs/adr/README.md) | Decisions — the architectural record (ADRs) |

Lower layers must comply with higher layers. Where they conflict, the Constitution prevails (see [ADR-0001](docs/adr/0001-adopt-layered-governance-documentation.md)).

Supporting corpora (established by ADR-0008; governed per [ADR-0009](docs/adr/0009-establish-argus-governance-council.md)): the [Lexicon](docs/glossary/LEXICON.md) — canonical vocabulary, normative everywhere — the [knowledge corpus](docs/knowledge/README.md) ([Standards](docs/knowledge/standards/README.md), [ISS research](docs/knowledge/research/README.md), the [Academy](docs/knowledge/academy/README.md); ADR-0012), and [Architecture artifacts](docs/architecture/README.md).

ARGUS develops by **Ontology-Driven Engineering** (ADR-0010): the ontology defines meaning, the schema defines structure, implementation realizes behavior, and verification proves conformance. [The ARGUS Ontology](docs/domain/ONTOLOGY.md) is the source of truth for meaning (Founder Resolution 003); the [Domain Schema Specification](docs/domain/DOMAIN_SCHEMA_SPECIFICATION.md), [Entity Lifecycles](docs/domain/ENTITY_LIFECYCLES.md), [Invariant Matrix](docs/domain/INVARIANT_MATRIX.md), implementation, and tests all derive from it — tests cite the stable ontology identifiers they protect (ADR-0011). Project governance runs through the ARGUS Governance Council (ADR-0009).

## Core commitments

- **Evidence before opinion** — every claim traces to source evidence. No provenance, no claim.
- **Observation ≠ Interpretation ≠ Hypothesis ≠ Judgment** — the analytical ladder is never collapsed.
- **Evidence is immutable** — retractions replace deletions; nothing disappears.
- **Unknowns and contradictions are explicit objects** — missing information and conflicting evidence are surfaced, never smoothed over.
- **Human judgment is final** — the AI organizes, summarizes, and proposes; it never decides.
- **Certainty must never exceed the evidence.**

## Contributing

All changes — human or AI-authored — are reviewed against the [Engineering Constitution](docs/foundation/ENGINEERING_CONSTITUTION.md). Architecturally significant decisions require an [ADR](docs/adr/README.md). If a requested change would violate the Constitution: stop, explain why, and propose a compliant alternative.
