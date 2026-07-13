# ARGUS Domain Invariant Matrix

- **Document version:** 0.0.3 (Skeleton — populated after the [Derivation Specification](DERIVATION_SPECIFICATION.md) ratifies, before Task 001)
- **Date:** 2026-07-13
- **Required by:** ADR-0006 (per-table enforcement specification and material-mutation enumeration)
- **Derived from:** the [Ontology](ONTOLOGY.md) via the [Derivation Specification](DERIVATION_SPECIFICATION.md) (ADR-0014), with structure from the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md) and [Entity Lifecycles](ENTITY_LIFECYCLES.md)

The matrix maps every constitutional invariant to its concrete enforcement mechanism and its verifying release-blocking test. It is the bridge between doctrine and implementation: ADR-0006 forbids blanket enforcement rules ("not every table has the same immutability requirements") and requires enforcement to be specified per table, here.

It also carries the authoritative enumeration of **material domain mutations** — the operations whose AuditEntry emission is constitutionally mandatory (ADR-0006, validation criterion 2). Until populated, the audit events listed per entity in the Domain Schema Specification and Entity Lifecycles serve as the provisional enumeration.

## Row schema

Each row of the populated matrix will specify:

| Column | Meaning |
|---|---|
| Entity / field group | The record type and the group of fields the row governs |
| Ontology rule | The stable identifier(s) of the rule(s) the row enforces (ONT-…, per ADR-0011) |
| Immutability class | CI (content-immutable) / V (versioned) / CT (controlled-transition), per spec C5 |
| Permitted mutations | The exhaustive list of allowed changes (empty for CI) |
| Permitted actors | Who may cause each mutation (spec C1) |
| Enforcing mechanism | Database role privilege / constraint / trigger / controlled function / service-layer rule — named concretely |
| Material mutations audited | The audit events emitted, atomically in-transaction |
| Verifying test | The release-blocking constitutional test that proves the enforcement (Constitution, Enforcement §3), which itself cites the row's ontology rule (ADR-0010) |

The matrix thereby closes the ODE verification loop: test → matrix row → ontology identifier → constitutional article.

## Status

The [Derivation Specification](DERIVATION_SPECIFICATION.md) is ratified (1.0.0, AGC Session 003); the matrix instantiates its obligations **incrementally, slice by slice** (ADR-0015): the rows for a slice's entities exist before that slice's code is written. First population: Slice 1 (EvidenceArtifact and AuditEntry rows), with the corresponding ERD coverage. Rows are reviewed at slice review by the Governance Council's Architecture Review Board.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.0.1 | 2026-07-13 | Skeleton: row schema and population plan. Relocated from docs/architecture/ per ADR-0009. |
| 0.0.2 | 2026-07-13 | Added Ontology-rule column (ADR-0011) and ODE loop-closure semantics (ADR-0010); population re-sequenced ahead of Task 001 per AGC Session 001. |
| 0.0.3 | 2026-07-13 | Re-derived through the Derivation Specification (ADR-0014); population follows its ratification. |
| 0.0.4 | 2026-07-13 | Population re-sequenced to slice-by-slice per ADR-0015; slice gate: rows before code. |
