# ADR-0015: Documentation freeze and vertical-slice implementation

- **Status:** Accepted (Chief Architect Directive 003 / Founder Resolution 006, AGC Review Session 003)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience); Prime Directive
- **Supersedes:** none (amends the sequencing clause of ADR-0014 and the Task 001/002 structure of ADR-0006's validation plan; both documents' substance is unchanged)

## Context

AGC Review Session 003 reviewed the architecture of the project itself rather than any document, and found the bottleneck has moved: with the Constitution, Ontology, Domain Schema, Entity Lifecycles, Derivation Specification, governance process, standards, and research framework in place, approximately 95% of the enduring philosophy required for ARGUS v0.1 is captured. The remaining 5% will emerge only through implementation. Continuing to write governance without implementation pressure risks a system that is internally elegant but untested against reality — and the project's own first axiom applies: **reality precedes representation** (ONT-PRN-001). Reality is saying it is time to build.

## Decision

### 1. Documentation Freeze (Chief Architect Directive 003)

A **temporary** freeze on foundational documentation takes effect. From this point forward: **no new foundational ADR unless implementation discovers a genuine gap or contradiction.** Implementation becomes the forcing function that validates governance instead of governance continuing to invent itself. Exempt from the freeze: this session's enactments, ADR-0007 (already reserved and required by Slice 1), applied research, slice-scoped engineering documents, and supersessions triggered by discovered gaps.

### 2. Founder Resolution 006

> **Implementation is now the primary source of architectural feedback.**

Recorded with its explicit boundary: this does **not** say implementation defines meaning — the ontology still does (ONT-PRN-008). It says implementation is where missing ontology is *discovered*. The discovery flow:

```
Ontology → Implementation → Discovery → ADR (if needed) → Supersession
```

The principle receives stable identifier **ONT-PRN-011**.

### 3. Vertical slices replace horizontal tasks

Task 001 (infrastructure scaffold) and Task 002 (domain layer) are replaced by **vertical slices** — each a complete constitutional loop through every layer (ontology, schema, API, database, UI, audit, tests):

| Slice | Scope | The loop |
|---|---|---|
| 1 | Evidence Ingestion | Upload synthetic artifact → hash verification → EvidenceArtifact record → audit event → visible in UI |
| 2 | SourceLocator | Address into an active artifact, end to end |
| 3 | Observation | First ladder claim with provenance enforcement, end to end |
| 4 | Unknown | First negative-space object with human-only disposition, end to end |

Each slice ends in review; a discovered gap becomes an ADR and a supersession *before* the next slice — not after 40,000 lines.

**Sequencing amendment:** the Invariant Matrix and ERD are no longer fully populated before any code (ADR-0014's ordering). They populate **incrementally, slice by slice**: the matrix rows and ERD coverage for a slice's entities MUST exist before that slice's code is written, preserving ADR-0006's requirement that enforcement is specified before it is implemented, per entity rather than en bloc.

### 4. The success metric

Success for the implementation phase is redefined. Not "the API works," "the database migrated," or "the UI renders," but:

> **Can a synthetic EvidenceArtifact travel through the entire constitutional system without violating a single invariant?**

### 5. Research program boundary

The research corpus is formally divided:

- **Foundational research** — ISS, ODE, Epistemic Integrity, Fragmentation Theory. Changes rarely; governed at full ceremony.
- **Applied research** — ingest performance, graph traversal, OCR evaluation, evidence clustering, retrieval quality, provenance UX. Evolves with implementation; iterates rapidly.

### 6. Standing instruction to the implementing engineer

Not "build ARGUS," but: **"Implement one complete constitutional slice. Prove that the ontology can become working software without violating itself."** Success validates not just a feature but the entire development methodology.

## Governance review

1. **Constitutional Review** — No violation. The freeze changes what gets *written*, not what governs; every existing guarantee stands, and the discovery flow routes changes through the same ADR/supersession discipline. **PASS.**
2. **Domain Review** — The ontology's authority is explicitly restated inside Resolution 006 (implementation discovers, never defines). The ladder is untouched; Slice ordering (artifact → locator → observation → unknown) actually walks *up* the ladder, exercising it in derivation order. **PASS.**
3. **Architectural Review** — Reversible (lifting the freeze is one superseding ADR); maintainable — it *reduces* documentation load; operationally realistic for a small team, which is the point; understandable; testable (the success metric is a single executable question). **PASS.**

## Consequences

- Governance output drops deliberately; engineering output begins. Future sessions are engineering design reviews.
- Discovered gaps get cheaper: each slice review catches ontology/schema mismatches at the smallest possible blast radius.
- The freeze must be honored by this project's own maintainers and agents — including resisting the temptation to polish governed documents while slices are unfinished.
- Risk accepted: per-slice matrix population means enforcement for not-yet-sliced entities remains unspecified longer; mitigated by the slice-gate rule in §3.

## Alternatives considered

- **Complete the matrix and ERD for all fourteen entities first** — rejected by this session: it validates one layer at a time and defers reality-contact; the per-slice gate keeps the same guarantee at smaller granularity.
- **A permanent freeze** — rejected: the discovery flow *requires* the ability to write ADRs when implementation finds gaps; the freeze is a filter, not a wall.
- **Continue horizontal Task 001/002** — rejected: horizontal layers validate nothing constitutional until they meet, which is the most expensive possible moment to discover a missing invariant.

## Constitutional Checklist

- [x] Article I — Evidence before opinion
- [x] Article II — Human judgment is final
- [x] Article III — Every analytical conclusion must explain itself
- [x] Article IV — Alternative explanations must always remain possible
- [x] Article V — Evidence is immutable
- [x] Article VI — Privacy and legal authority must be respected
- [x] Article VII — Scientific integrity before convenience
- [x] Article VIII — Justice requires transparency
- [x] Article IX — Certainty must never exceed the evidence

**Affected Articles:** VII (reinforced: governance claims now get empirically tested instead of accumulating untested) and the Prime Directive via ONT-PRN-001 — the decision is itself an application of "reality precedes representation" to the project's own process. Others untouched.

**Compliant?** YES

**Explanation:** A process decision about sequencing and scope. No guarantee is weakened; every constitutional mechanism (ADRs, supersession, AGC review, derivation, verification) remains mandatory — implementation now supplies the pressure that proves them.
