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
- **Documentation Freeze in effect** ([ADR-0015](0015-documentation-freeze-and-vertical-slices.md)): no new foundational ADR unless implementation discovers a genuine gap or contradiction. Slice-scoped engineering decisions and gap-triggered supersessions remain open.
- ADRs are unversioned; governance documents elsewhere follow the [Governance Versioning Standard](../knowledge/standards/GOVERNANCE_VERSIONING_STANDARD.md).

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-adopt-layered-governance-documentation.md) | Adopt layered governance documentation | Accepted |
| [0002](0002-separate-observation-interpretation-hypothesis.md) | Separate Observation, Interpretation, and Hypothesis as distinct entities | Accepted |
| [0003](0003-append-only-evidence-with-retraction.md) | Append-only evidence with retraction instead of deletion | Accepted |
| [0004](0004-mandatory-provenance-for-analytical-claims.md) | Mandatory provenance for all analytical claims | Accepted |
| [0005](0005-unknowns-and-contradictions-as-first-class-entities.md) | Unknowns and contradictions as first-class entities | Accepted |
| [0006](0006-argus-core-v0.1-technology-stack.md) | ARGUS Core v0.1 technology stack | Accepted |
| [0007](0007-evidence-ingestion-and-atomic-finalization.md) | Evidence ingestion and atomic finalization | Accepted (amended and ratified by AGC Session 004) |
| [0008](0008-establish-arb-and-documentation-governance.md) | Establish the Architecture Review Board and Phase 1 documentation governance | Superseded by 0009 |
| [0009](0009-establish-argus-governance-council.md) | Establish the ARGUS Governance Council | Accepted |
| [0010](0010-verification-derives-from-the-ontology.md) | Verification derives from the ontology | Accepted |
| [0011](0011-stable-ontology-identifiers.md) | Stable ontology identifiers | Accepted |
| [0012](0012-consolidate-knowledge-corpus.md) | Consolidate the knowledge corpus under docs/knowledge/ | Accepted |
| [0013](0013-implementation-must-remain-replaceable.md) | Implementation must remain replaceable | Accepted |
| [0014](0014-establish-the-derivation-specification-layer.md) | Establish the Derivation Specification layer | Accepted |
| [0015](0015-documentation-freeze-and-vertical-slices.md) | Documentation freeze and vertical-slice implementation | Accepted |
| [0016](0016-append-only-audit-hash-chain.md) | Append-only audit hash chain (tamper-evident within the trust boundary) | Accepted (freeze exemption per ONT-PRN-011) |
| [0017](0017-single-source-lifecycle-definitions.md) | Authoritative lifecycle definitions shall exist exactly once | Accepted (freeze exemption per ONT-PRN-011) |
| [0018](0018-constitutional-predicates.md) | Constitutional predicates, and eligibility versus sufficiency | Accepted (freeze exemption per ONT-PRN-011) |
| [0019](0019-triangulated-derivations.md) | Independent derivations should be triangulated whenever practical | Accepted (freeze exemption per ONT-PRN-011) |
| [0020](0020-sourcelocator-as-scope-of-constitutional-support.md) | SourceLocator is the scope of constitutional support | Accepted (freeze exemption per ONT-PRN-011) |
| [0021](0021-persistence-implements-admissibility.md) | Persistence implements admissibility, not defines it | Accepted (freeze exemption per ONT-PRN-011) |
| [0022](0022-semantic-contamination.md) | Epistemic layers reject semantic contamination from higher layers | Accepted (freeze exemption per ONT-PRN-011) |
| [0023](0023-accumulating-epistemic-obligations.md) | The ladder accumulates obligations | Accepted (freeze exemption per ONT-PRN-011) |
| [0024](0024-unknowns-as-epistemic-boundaries.md) | Unknowns are epistemic boundaries; boundary objects kept distinct | Accepted (freeze exemption per ONT-PRN-011) |
| [0025](0025-existence-versus-validity-relationships.md) | Existence relationships are distinct from validity-boundary relationships | Accepted (freeze exemption per ONT-PRN-011) |
| [0026](0026-dimensions-over-objects.md) | Epistemic layers expand dimensions, not merely object counts | Accepted (freeze exemption per ONT-PRN-011) |
| [0027](0027-contradiction-disposition.md) | ContradictionDisposition as a first-class object | Accepted (freeze exemption per ONT-PRN-011) |
| [0028](0028-explanations-must-state-their-conditions.md) | An explanation must state what supports, limits, challenges, and escapes it | Accepted (freeze exemption per ONT-PRN-011) |
| [0029](0029-constraint-precedes-expressive-power.md) | No expressive power without prior constraint | Accepted (freeze exemption per ONT-PRN-011) |
| [0030](0030-historical-articulation-vs-current-condition.md) | Historical articulation and current derived condition remain distinct | Accepted (freeze exemption per ONT-PRN-011) |
| [0031](0031-reconciliation-never-converts-agreement-into-truth.md) | Reconciliation never converts agreement into truth | Accepted (freeze exemption per ONT-PRN-011) |
| [0032](0032-no-silent-repair-of-constitutional-history.md) | No silent repair of constitutional history | Accepted (freeze exemption per ONT-PRN-011) |
| [0033](0033-identity-is-authenticated-never-asserted.md) | Identity is authenticated, never asserted | Accepted (freeze exemption per ONT-PRN-011) |
