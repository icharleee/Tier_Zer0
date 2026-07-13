# Architecture Decision Records

This directory is the permanent record of architecturally significant decisions made on ARGUS.

An ADR is required for any decision that:

- shapes the domain model, persistence strategy, or API surface;
- affects a guarantee made by the [Engineering Constitution](../foundation/ENGINEERING_CONSTITUTION.md); or
- would be expensive to reverse.

## Conventions

- One decision per file: `NNNN-short-title.md`, numbered sequentially.
- Use [`0000-template.md`](0000-template.md).
- ADRs are immutable once **Accepted** — like everything else in ARGUS, they are superseded, never rewritten. A replacing ADR links back with `Supersedes`/`Superseded by`.
- Every ADR cites the constitutional article(s) it reinforces or touches.
- Every ADR from 0009 onward records the three ARGUS Governance Council reviews (Constitutional, Domain, Architectural) and **finishes** with a Constitutional Checklist auditing all nine articles — see [ADR-0009](0009-establish-argus-governance-council.md).
- ADRs are unversioned; governance documents elsewhere follow the [Governance Versioning Standard](../standards/GOVERNANCE_VERSIONING_STANDARD.md).

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-adopt-layered-governance-documentation.md) | Adopt layered governance documentation | Accepted |
| [0002](0002-separate-observation-interpretation-hypothesis.md) | Separate Observation, Interpretation, and Hypothesis as distinct entities | Accepted |
| [0003](0003-append-only-evidence-with-retraction.md) | Append-only evidence with retraction instead of deletion | Accepted |
| [0004](0004-mandatory-provenance-for-analytical-claims.md) | Mandatory provenance for all analytical claims | Accepted |
| [0005](0005-unknowns-and-contradictions-as-first-class-entities.md) | Unknowns and contradictions as first-class entities | Accepted |
| [0006](0006-argus-core-v0.1-technology-stack.md) | ARGUS Core v0.1 technology stack | Accepted |
| 0007 | Evidence ingestion and atomic finalization | Reserved (forward-referenced by ADR-0006; not yet drafted) |
| [0008](0008-establish-arb-and-documentation-governance.md) | Establish the Architecture Review Board and Phase 1 documentation governance | Superseded by 0009 |
| [0009](0009-establish-argus-governance-council.md) | Establish the ARGUS Governance Council | Accepted |
