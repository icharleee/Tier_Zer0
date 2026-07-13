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

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-adopt-layered-governance-documentation.md) | Adopt layered governance documentation | Accepted |
| [0002](0002-separate-observation-interpretation-hypothesis.md) | Separate Observation, Interpretation, and Hypothesis as distinct entities | Accepted |
| [0003](0003-append-only-evidence-with-retraction.md) | Append-only evidence with retraction instead of deletion | Accepted |
| [0004](0004-mandatory-provenance-for-analytical-claims.md) | Mandatory provenance for all analytical claims | Accepted |
| [0005](0005-unknowns-and-contradictions-as-first-class-entities.md) | Unknowns and contradictions as first-class entities | Accepted |
