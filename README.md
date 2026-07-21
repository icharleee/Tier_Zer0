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

**Roadmap complete — Phase 4: Constitutional Hardening and Replication (ADR-0037).** The original slice roadmap (ADR-0015) is finished and pinned as **[ARGUS Constitutional Baseline 1.0](docs/foundation/CONSTITUTIONAL_BASELINE_1.0.md)** — an immutable versioned record of the normative corpus, the H1–H12 experimental ledger (each Supported at n = 1), migration head 013, and the 150-test reference result. Phase 4 (AGC Session 023) adds no new epistemic objects; its four workstreams — independent adapter replication (H13), browser and assistive-technology conformance (H14), adversarial and concurrency hardening (H15), and an independent reimplementation study (H16) — each require their own plan gate before implementation.

**Version 0.1 — Documentation Freeze; implementation phase (ADR-0015).** The governance foundation is complete and frozen: the Constitution governs, the Governance Council decides, the Ontology defines meaning, the Derivation Specification explains translation, the Schema defines structure, the Invariant Matrix defines enforcement, the code implements, the tests verify — nothing skips a layer, and no new foundational ADR is written unless implementation discovers a gap (Founder Resolution 006). Slice roadmap (AGC Session 007 — infrastructure keeps waiting; the ontology is still teaching): **1A ✔ → 1B ✔ → 1C ✔ → 1D ✔ → 2A Competing Interpretations ✔ → 2B Unknowns and evidentiary limits ✔ → 2C Contradictions ✔ → 2D Hypotheses ✔ → 3A Case reconstruction read model ✔ (AGC Session 013: integration before new rungs — the authorized epistemic ladder is complete; additional epistemic objects are NOT AUTHORIZED) → 1E storage + reconciliation ✔ (detection only — repair behind a later gate; MinIO adapter deferred behind the ContentStore contract) → 1F, decomposed by AGC Session 017 into 1F-A authenticated actor context ✔ → 1F-B authority and visibility ✔ (resource-scoped capabilities, no inheritance, Case-scope only; a two-stage visibility ladder where withholding is explicit once existence may be known but secrecy never leaks existence; SEALED content disclosed only after the access is durably audited; ONT-PRN-029/030 — authority never makes a record more true, and absence of access is never absence of evidence) → 1F-C visible review surface ✔ (ONT-PRN-031 — presentation may organize, never create epistemic hierarchy: no visual ranking, no truth-semantic color, no default hypothesis preference, no hidden retracted history, and accessibility semantics are constitutional too) (identity, authority, and presentation are different problems)**. The roadmap's slices are complete: an investigation now travels the whole constitutional path — ingested, verified, claimed, interpreted, bounded, contradicted, explained, reconstructed, reconciled — and reaches a human screen that helps them find the information without telling them which of it deserves belief. The first transport boundary now exists — a minimal FastAPI surface where a constitutional command binds to an authenticated principal and refuses any caller-supplied identity, with a transaction-scoped database guard that independently verifies the recorded actor matches the bound principal. Identity is authenticated, never asserted (ONT-PRN-028): the actor attributed to any action derives from an authenticated principal at the transport boundary, never from caller payload — and authentication establishes attribution only, conferring no authority, access, credibility, or epistemic standing. Reconciliation classifies integrity, never truth: representations can agree or diverge (`MATCHED`/`MISSING`/`DIVERGENT`/`UNREADABLE`/`UNVERIFIED`); only evidence, reasoning, and human judgment address truth — and the first scan proved its worth by catching a real defect the entire prior suite had missed. The whole graph now renders as one **Case Reconstruction** — a transient, read-only projection of the records (never of reality), dual-rendered to byte-identical canonical documents: every record accounted for under its visibility envelope, retractions labeled, historical articulations beside current derived states, a broken audit chain surfaced rather than hidden — and no narrative, ranking, or synthesized conclusion anywhere. The ladder's first two rungs exist: `OBS-000001 "Blue sedan visible."` and competing interpretations `INT-000001`/`INT-000002` over identical grounding — coexisting without epistemic preference, each carrying a structured uncertainty envelope and grounding snapshots. Both boundary objects now stand beside them: an Unknown bounds interpretation without becoming evidence (resolved only by a human, with evidence), and a Contradiction records a formally scoped joint incompatibility — disposed by human explanation, never adjudicated by the system. And the ladder now reaches its highest authorized rung: competing explanations `HYP-000001`/`HYP-000002` coexist over the same interpretations, each stating what supports it, what limits it, what could challenge it, and what remains unknown (ONT-PRN-023) — bounded by the Unknown, challenged by the Contradiction, and never revised, promoted, or refuted by the system. ARGUS preserves competing human meanings; it does not convert coexistence into comparison, absence into support, conflict into verdict, or explanation into conclusion. Understanding and Judgment remain human, outside the schema. The first acceptance test — a synthetic image ingested, identified, verified, activated, fully audited, and made Observation-eligible with zero invariant violations — **passes**, at the application layer and against the database's independent enforcement.

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
