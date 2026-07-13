# ARGUS Domain Invariant Matrix

- **Document version:** 0.0.1 (Skeleton — populated during Task 002, after Domain Schema Specification ratification)
- **Date:** 2026-07-13
- **Required by:** ADR-0006 (per-table enforcement specification and material-mutation enumeration)
- **Derived from:** the [Ontology](ONTOLOGY.md), [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md), and [Entity Lifecycles](ENTITY_LIFECYCLES.md)

The matrix maps every constitutional invariant to its concrete enforcement mechanism and its verifying release-blocking test. It is the bridge between doctrine and implementation: ADR-0006 forbids blanket enforcement rules ("not every table has the same immutability requirements") and requires enforcement to be specified per table, here.

It also carries the authoritative enumeration of **material domain mutations** — the operations whose AuditEntry emission is constitutionally mandatory (ADR-0006, validation criterion 2). Until populated, the audit events listed per entity in the Domain Schema Specification and Entity Lifecycles serve as the provisional enumeration.

## Row schema

Each row of the populated matrix will specify:

| Column | Meaning |
|---|---|
| Entity / field group | The record type and the group of fields the row governs |
| Immutability class | CI (content-immutable) / V (versioned) / CT (controlled-transition), per spec C5 |
| Permitted mutations | The exhaustive list of allowed changes (empty for CI) |
| Permitted actors | Who may cause each mutation (spec C1) |
| Enforcing mechanism | Database role privilege / constraint / trigger / controlled function / service-layer rule — named concretely |
| Material mutations audited | The audit events emitted, atomically in-transaction |
| Verifying test | The release-blocking constitutional test that proves the enforcement (Constitution, Enforcement §3) |

## Status

Blocked on: Domain Schema Specification ratification → begins population with Task 002 (domain implementation), one row group per entity, reviewed by the Governance Council's Architecture Review Board.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.0.1 | 2026-07-13 | Skeleton: row schema and population plan. Relocated from docs/architecture/ per ADR-0009. |
