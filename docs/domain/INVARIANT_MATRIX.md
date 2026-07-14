# ARGUS Domain Invariant Matrix

- **Document version:** 0.4.0 (Slice 1D: SourceLocator and Observation row groups per ADR-0020 — rows before code)
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
| AuditEntry: all fields (incl. chain fields per ADR-0016) | ONT-AUD-001 | CI | none for the application and ordinary operational roles (privileged owners remain inside the declared trust boundary; unauthorized privileged modification is detected via chain verification, migration review, and operational controls) | — (emitted only via `argus_private.append_audit_event`, as side effect of attributed operations) | SELECT-only grant for `argus_app` on `audit_entries`; inserts solely through the SECURITY DEFINER append function; no UPDATE/DELETE grants; corrections are compensating entries | — | `test_direct_audit_update_fails`, `test_direct_audit_delete_fails`, `test_direct_audit_insert_fails` |
| AuditEntry: atomic emission | ONT-AUD-001, D-AUD | invariant | — | — | transition functions update the aggregate and append the event in one function body — one transaction, both or neither | every material mutation above | `test_transition_appends_event_atomically`, `test_failed_transition_appends_no_event` |
| AuditEntry: per-case ordering | ONT-AUD-001 | invariant | — | — | `case_audit_heads` row locked FOR UPDATE first in the global lock order (ADR-0016); `next = last_sequence + 1`; unique (case, seq) constraint as backstop | — | `test_concurrent_appends_gapless_per_case` |
| AuditEntry: hash chain | ONT-AUD-001 (ADR-0016) | invariant | — | — | `event_hash = sha256(canonical_text)` chain_version 1, computed in the append function from stored bytes; genesis = 64 zeros; head tracks `last_event_hash` | — | `test_chain_verification_valid`, `test_chain_verification_detects_corruption` |
| CaseAuditHead: last_sequence / last_event_hash | ONT-AUD-001 (ADR-0016) | CT | advanced only by the append function | — (function-internal) | SELECT/INSERT-only grant for `argus_app`; UPDATE only inside `argus_private.append_audit_event` | — (bookkeeping, not a domain event) | `test_direct_head_update_fails` |

### SourceLocator and Observation (Slice 1D, ADR-0020)

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| SourceLocator: scheme, payload, artifact ref | ONT-SRC-001, ONT-PRN-016 | CI after creation | none (corrections = retract and replace) | — | SELECT-only grant for `argus_app`; inserts solely via `argus_private.create_source_locator` (validates ACTIVE artifact, scheme registry, byte-range bounds) | locator-created | `test_locator_requires_active_artifact`, `test_locator_bounds_checked` |
| SourceLocator: retraction | ONT-PRN-006 | V | retract with reason | Human | `argus_private.retract_source_locator` | locator-retracted | `test_locator_retraction_human_with_reason` |
| Observation: statement, method, groundings, citation | ONT-OBS-001, ONT-PRN-004, ONT-PRN-005 | CI after creation | none | — | SELECT-only grant; inserts solely via `argus_private.create_observation`, which calls `validate_observation` (the canonical admissibility matrix) and refuses on any code; groundings junction rows CI; citation unique per case, allocated under the head lock | claim-created | `test_observation_admissibility_matrix`, `test_h3_validator_conformance` |
| Observation: retraction | ONT-PRN-006, ONT-PRN-007 | V | retract with reason | Human | `argus_private.retract_observation` | claim-retracted | `test_observation_retraction_human_with_reason` |
| `is_grounded` (derived; no storage) | ONT-OBS-001, ONT-PRN-015 | invariant | none — derived: ≥1 non-retracted locator whose artifact is ACTIVE | — | Python predicate + `argus_private.is_observation_grounded`, conformance-tested; never auto-retracts (Article II — degradation is surfaced for human disposition) | — | `test_groundedness_degrades_on_retraction` |

### Constitutional predicates (Slice 1C, ADR-0018)

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| `can_support_observation` (derived; no storage) | ONT-EVA-001, ONT-CAS-001, ONT-PRN-014 | invariant | none — derived from constitutional state per the [canonical matrix](CONSTITUTIONAL_PREDICATES.md); **no persisted eligibility flag exists anywhere** | — | Python predicate module + `argus_private.can_support_observation` PostgreSQL function, independently derived; identical decisions and canonical reason codes proven by conformance sweep | — (a pure read; the gate it feeds — Observation creation — audits in Slice 1D) | `test_predicate_matrix_python`, `test_predicate_conformance_python_vs_postgres` |

## Version history

| Version | Date | Change |
|---|---|---|
| 0.0.1 | 2026-07-13 | Skeleton: row schema and population plan. Relocated from docs/architecture/ per ADR-0009. |
| 0.0.2 | 2026-07-13 | Added Ontology-rule column (ADR-0011) and ODE loop-closure semantics (ADR-0010); population re-sequenced ahead of Task 001 per AGC Session 001. |
| 0.0.3 | 2026-07-13 | Re-derived through the Derivation Specification (ADR-0014); population follows its ratification. |
| 0.0.4 | 2026-07-13 | Population re-sequenced to slice-by-slice per ADR-0015; slice gate: rows before code. |
| 0.1.0 | 2026-07-13 | First population: Slice 1 rows (Case, EvidenceArtifact, AuditEntry) instantiating Derivation Specification obligations and ADR-0007 as amended. |
| 0.2.0 | 2026-07-13 | Slice 1B: AuditEntry rows re-mechanized per ADR-0016 (append function, head-row lock order, hash chain, trust-boundary language per AGC amendments); CaseAuditHead row added; verifying tests renamed to the adversarial suite. |
| 0.3.0 | 2026-07-13 | Slice 1C: can_support_observation predicate row (ADR-0018) — derived never stored, dual-rendered, conformance-tested. |
| 0.4.0 | 2026-07-13 | Slice 1D gate: SourceLocator and Observation row groups, is_grounded derived row (ADR-0020). |
