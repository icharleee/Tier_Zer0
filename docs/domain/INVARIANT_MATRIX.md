# ARGUS Domain Invariant Matrix

- **Document version:** 0.1.0 (Slice 1 populated — Case, EvidenceArtifact, AuditEntry; remaining entities populate with their slices)
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

Populated incrementally, slice by slice (ADR-0015): the rows for a slice's entities exist before that slice's code is written. **Slice 1 (Constitutional Evidence Activation) rows below.** Rows are reviewed at slice review by the Governance Council's Architecture Review Board.

## Slice 1 rows — Constitutional Evidence Activation

Enforcement mechanisms name their PostgreSQL construct per ADR-0006; the service layer enforces the same rule above the database (defense in depth, never instead of it). Verifying tests are release-blocking (Constitution, Enforcement §3) and cite their ontology rule per ADR-0010.

### Case

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Case: identity, created_at | ONT-CAS-001 | CI | none | — | no UPDATE grant on columns; no DELETE grant on table | — | `test_case_immutable_identity` |
| Case: legal authority basis | ONT-CAS-001 | V | append new authority record | Human | INSERT-only authority table; no UPDATE/DELETE grants | case-authority-superseded | `test_case_authority_append_only` |
| Case: status | ONT-CAS-001, ONT-PRN-012 | CT | OPEN⇄SUSPENDED, OPEN→CLOSED, CLOSED→OPEN per Lifecycles §1 | Human | transition via controlled function checking predecessor state; audit in same transaction | case-created/-suspended/-resumed/-closed/-reopened | `test_case_transitions_explicit_and_audited` |
| Case: title/designation | ONT-CAS-001 | CT | update with audit | Human | controlled function; audit in same transaction | case-designation-changed | `test_case_designation_change_audited` |

### EvidenceArtifact

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Artifact: content bytes (object store) | ONT-EVA-001, ONT-PRN-006 | CI | none (content-addressed by hash) | — | write-once permanent location; reads verify recorded hash | sealed-content reads; integrity failures | `test_artifact_content_read_verifies_hash` |
| Artifact: original hash, size, ingestion record | ONT-EVA-001 | CI | none (additive second hash permitted as new row/column, per ADR-0007 §5) | — | no UPDATE grant on columns; no DELETE grant on table | — | `test_artifact_hash_immutable_at_db` |
| Artifact: status | ONT-EVA-001, ONT-PRN-012 | CT | exactly the transitions of Lifecycles §2 | System (activate, quarantine); Human (retract, seal, unseal, quarantine disposition) | transition via controlled function validating predecessor state and actor class; audit in same transaction | artifact-ingested/-activated/-quarantined/-reactivated/-retracted/-sealed/-unsealed | `test_artifact_transitions_explicit`, `test_artifact_activation_requires_verification`, `test_quarantine_disposition_human_only` |
| Artifact: storage reference | ONT-EVA-001 | CT | re-home to verified equivalent copy | System (with human authority) | controlled function verifying hash of destination before switch | artifact-storage-rehomed | `test_rehoming_verifies_destination_hash` |
| Artifact: analytical visibility | ONT-EVA-001, ONT-PRN-005 | invariant | — | — | analysis queries filter status = ACTIVE; FK from SourceLocator validated against ACTIVE at creation (Slice 2) | — | `test_non_active_artifact_invisible_to_analysis` |

### AuditEntry

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| AuditEntry: all fields | ONT-AUD-001 | CI | none — for every role including administrators | — (system-emitted only, as side effect of attributed operations) | INSERT-only privileges for the application role; no UPDATE/DELETE grants for any role; corrections are compensating entries | — | `test_audit_entry_immutable_for_all_roles` |
| AuditEntry: atomic emission | ONT-AUD-001, D-AUD | invariant | — | — | audit INSERT in the same transaction as the mutation (controlled functions emit both) | every material mutation above | `test_mutation_and_audit_atomic_rollback` |
| AuditEntry: per-case ordering | ONT-AUD-001 | invariant | — | — | monotonic sequence per case; unique (case, seq) constraint | — | `test_audit_ordering_gapless_per_case` |

## Version history

| Version | Date | Change |
|---|---|---|
| 0.0.1 | 2026-07-13 | Skeleton: row schema and population plan. Relocated from docs/architecture/ per ADR-0009. |
| 0.0.2 | 2026-07-13 | Added Ontology-rule column (ADR-0011) and ODE loop-closure semantics (ADR-0010); population re-sequenced ahead of Task 001 per AGC Session 001. |
| 0.0.3 | 2026-07-13 | Re-derived through the Derivation Specification (ADR-0014); population follows its ratification. |
| 0.0.4 | 2026-07-13 | Population re-sequenced to slice-by-slice per ADR-0015; slice gate: rows before code. |
| 0.1.0 | 2026-07-13 | First population: Slice 1 rows (Case, EvidenceArtifact, AuditEntry) instantiating Derivation Specification obligations and ADR-0007 as amended. |
