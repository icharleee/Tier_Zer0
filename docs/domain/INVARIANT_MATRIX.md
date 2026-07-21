# ARGUS Domain Invariant Matrix

- **Document version:** 0.13.0 (Slice 1F-C: Case Presentation rows per the five Session 022 amendments)
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

### Interpretation (Slice 2A)

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Interpretation: meaning, reasoning, uncertainty envelope, citation | ONT-INT-001, ONT-PRN-002, ONT-PRN-005 | CI after creation | none | — | SELECT-only grant; inserts solely via `argus_private.create_interpretation`, which calls `validate_interpretation` (canonical matrix incl. the comparative-vocabulary guard and the structured uncertainty envelope — CHECK constraints back the envelope) | claim-created | `test_interpretation_admissibility_matrix`, `test_h4_validator_conformance` |
| Interpretation: no-preference surface | ONT-PRN-018 (Article IV) | invariant | — | — | contamination registry forbids rank/preferred/primary/weight vocabulary; no uniqueness constraint prevents siblings over identical grounding; citation order documented non-evidentiary | — | `test_h4_no_epistemic_priority` |
| InterpretationGrounding: observation ref, statement_fingerprint, role, linked_at | ONT-INT-001, ONT-PRN-004 | CI | none (snapshot rows survive retraction of anything) | — | inserted only inside `create_interpretation`; fingerprint computed in-function from the observation statement | — (part of claim-created) | `test_grounding_snapshot_preserved` |
| Interpretation: retraction | ONT-PRN-006, ONT-PRN-007 | V | retract with reason | Human | `argus_private.retract_interpretation`; no effect on siblings, groundings, or observations | claim-retracted | `test_interpretation_retraction_no_promotion` |
| `grounding_health` (derived; no storage) | ONT-INT-001, ONT-PRN-015 | invariant | none — GROUNDED iff ≥1 grounding references an unretracted, grounded Observation; else DEGRADED | — | Python predicate + `argus_private.interpretation_grounding_health`, conformance-tested; surfaces, never auto-retracts (Article II) | — | `test_grounding_health_degrades_both_renderings` |

### Unknown, UnknownLink, UnknownResolution (Slice 2B, ADR-0024/0025)

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Unknown: question, impact, citation | ONT-UNK-001, ONT-PRN-020 | CI after creation | none (question corrections = retract/replace pattern deferred with AI suggestions) | — | SELECT-only grant; inserts solely via `argus_private.create_unknown` (question-form + anti-TODO guard) | unknown-created | `test_unknown_admissibility_matrix` |
| Unknown: operational_state | ONT-PRN-012 | CT | OPEN ⇄ UNDER_REVIEW only | Human | named transition functions; epistemic disposition NOT writable here | unknown-review-started / -paused | `test_under_review_is_operational_not_epistemic` |
| Unknown: epistemic disposition | ONT-UNK-001, ONT-PRN-007 | derived | none — derived from the UnknownResolution record | — | no disposition column exists to write; status computed | (via resolution) | `test_disposition_derived_never_stored` |
| UnknownLink: target, nature | ONT-PRN-021 | CI (validity-boundary family — may never gain grounding semantics) | none (link errors: retract pattern, V) | Human create | inserted via `create_unknown` / `link_unknown`; same-case CHECK in function | unknown-linked | `test_links_are_boundaries_not_grounds` |
| UnknownResolution: type, rationale, claim refs | ONT-UNR-001, ONT-PRN-007 | CI | none | **Human only** | `argus_private.resolve_unknown`: ANSWERED/PARTIALLY_ANSWERED require ≥1 claim reference; rationale required; terminal | unknown-resolved / -partially-resolved / -withdrawn / -marked-unresolvable | `test_answer_requires_evidence`, `test_disposition_human_only_at_db` |
| H5 negative obligations | ONT-PRN-020 | invariant | — | — | no trigger, function, or validator mutates bounded records on link or resolution; verified by byte-identity tests | — | `test_resolution_alters_no_linked_record`, `test_open_unknown_changes_nothing` |

### Contradiction, ContradictionMember, ContradictionDisposition (Slice 2C, ADR-0027)

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Contradiction: description, type, scope, basis, citation | ONT-CON-001 | CI after creation | none | — | SELECT-only grant; inserts solely via `argus_private.create_contradiction` (basis matrix + adjudicative-language guard) | contradiction-created | `test_contradiction_admissibility_matrix` |
| Contradiction: operational_state | ONT-PRN-012 | CT | OPEN ⇄ UNDER_REVIEW only; refused after disposition | Human | named transition function; epistemic disposition NOT writable | contradiction-review-started / -paused | `test_contradiction_review_operational_only` |
| Contradiction: epistemic disposition | ONT-CDP-001, ONT-PRN-007 | derived | none — derived from the ContradictionDisposition record | — | no disposition column exists to flip | (via disposition) | `test_contradiction_disposition_derived` |
| ContradictionMember: type, id, fingerprint, role, linked_at | ONT-CNM-001 | CI | none — members survive every retraction and disposition | — | inserted only inside `create_contradiction`; role CHECK = INCOMPATIBLE_CLAIM | (part of contradiction-created) | `test_members_immutable_and_symmetric` |
| ContradictionDisposition: outcome, rationale, informing refs | ONT-CDP-001, ONT-PRN-007 | CI | none | **Human only** | `argus_private.dispose_contradiction`: five non-adjudicating outcomes; rationale required; terminal; alters no member | contradiction-disposed | `test_disposition_human_only_no_survivor` |
| `contradiction_health` (derived; no storage) | ONT-CON-001, ONT-PRN-015 | invariant | none — CURRENT iff all members unretracted and available; else DEGRADED | — | Python predicate + `argus_private.contradiction_health`, conformance-tested; surfaces, never auto-disposes | — | `test_health_degrades_without_autodisposition` |
| H6 negative obligations | ONT-CON-001 (Article IV) | invariant | — | — | no survivor/winner/preference surface (contamination registry); creation and disposition leave every member byte-identical; existing validators unchanged | — | `test_h6_no_adjudication`, existing conformance sweeps |

### Hypothesis, HypothesisGrounding, HypothesisAlternative, ContradictionLink (Slice 2D, ADR-0028)

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Hypothesis: explanatory statement, reasoning, uncertainty envelope, testability statement, challenge condition, citation | ONT-HYP-001, ONT-PRN-023, ONT-PRN-005 | CI after creation | none | — | SELECT-only grant; inserts solely via `argus_private.create_hypothesis`, which calls `validate_hypothesis` (canonical matrix: four conditions, comparative guard, articulation XORs — CHECK constraints back the envelope and articulation pairing) | claim-created | `test_hypothesis_admissibility_matrix`, `test_h7_validator_conformance` |
| Hypothesis: creation-time alternative articulation (`alternative_articulation_at_creation`, `alternative_absence_explanation`) | ONT-PRN-023 (Article IV), ONT-PRN-006 | CI | none — historical truth of the creation moment; later links never erase it | — | stored immutably at creation; CHECK pairs the mode with the explanation's presence; `current_alternative_state` derived separately | (part of claim-created) | `test_creation_articulation_survives_later_linking` |
| Hypothesis: boundary articulation (`no_current_unknowns_explanation`, `no_current_contradictions_explanation`) | ONT-PRN-023, ONT-PRN-020 | CI | none | — | XOR with boundary links enforced in `validate_hypothesis` (silence is the refusal codes `…-articulation-required`); explanations state present articulation, never reality | (part of claim-created) | `test_boundary_articulation_required` |
| Hypothesis: no-preference / no-verdict surface | ONT-PRN-018, ONT-PRN-023 (Article IV) | invariant | — | — | contamination registry (structured surfaces): no probability/confidence/preferred/primary/leading/best/winner/theory/accept/refutation stems; no uniqueness constraint privileges any sibling; only HumanActor may author (AI NOT AUTHORIZED) | — | `test_h7_no_preference_surface`, contamination sweep |
| Hypothesis: retraction | ONT-PRN-006, ONT-PRN-007 | V | retract with reason | Human | `argus_private.retract_hypothesis`; no effect on siblings, alternatives, groundings, or boundaries — no promotion | claim-retracted | `test_hypothesis_retraction_no_promotion` |
| HypothesisGrounding: interpretation ref, fingerprint v2, role, linked_at | ONT-HYP-001, ONT-PRN-004 | CI | none (snapshot rows survive every retraction) | — | inserted only inside `create_hypothesis`; fingerprint v2 computed in-function (4 fields, 0x1F separator, documented version); role CHECK ∈ {DERIVED_FROM, CONTEXTUALIZED_BY}; FK to interpretations makes rung-skips unrepresentable | — (part of claim-created) | `test_grounding_snapshot_fingerprint_v2` |
| HypothesisAlternative: normalized pair, relation explanation, linked_at | ONT-HYP-001 (Article IV), ONT-PRN-006 | CI | none — survives either side's retraction | Human create (at creation or via `link_hypothesis_alternative`) | dedicated SECURITY DEFINER function: self-link/cross-case/duplicate refused, explanation required, comparative-language guard, normalized (a < b) CHECK; modifies neither Hypothesis | hypothesis-alternative-linked | `test_alternative_link_symmetric_immutable` |
| ContradictionLink: contradiction ref, hypothesis ref, fingerprint v1, relationship, explanation | ONT-CON-001, ONT-PRN-021, ONT-PRN-023 | CI content; V (retract for link errors, with reason — never silent removal) | retract with reason | **Human only** | `argus_private.link_contradiction`: relationship CHECK = CHALLENGED_BY_CONTRADICTION (no refutation value may ever exist); same-case; duplicate refused; alters neither endpoint; disposed Contradictions remain linked | contradiction-linked / contradiction-unlinked | `test_contradiction_link_challenges_without_killing` |
| UnknownLink: target set extension (Hypothesis) | ONT-UNL-001, ONT-PRN-021 | (unchanged rows above) | — | Human | `argus_private.link_unknown` target validation extended to hypotheses; same-case CHECK unchanged | unknown-linked | `test_unknown_bounds_hypothesis` |
| `hypothesis_health` (derived; no storage) | ONT-HYP-001, ONT-PRN-015 | invariant | none — CURRENT / DEGRADED / UNSUPPORTED over DERIVED_FROM groundings only | — | Python predicate + `argus_private.hypothesis_health`, conformance-tested; even UNSUPPORTED never auto-retracts (Article II) | — | `test_hypothesis_health_three_states_both_renderings` |
| `current_alternative_state`, `unknown_boundary_state`, `contradiction_boundary_state` (derived; no storage) | ONT-HYP-001, ONT-PRN-023, ONT-PRN-015 | invariant | none — derived from links, resolutions, dispositions; no authoritative boolean stored | — | Python predicates + `argus_private.*` renderings, conformance-tested; state changes only through derivation | — | `test_derived_states_change_without_touching_bytes` |
| H7 negative obligations | ONT-HYP-001, ONT-PRN-023 (Articles II, IV, IX) | invariant | — | — | resolving the shared Unknown, disposing the linked Contradiction, linking alternatives, and retracting a sibling leave every Hypothesis byte-identical; no automatic promotion, refutation, or revision path exists in any function | — | `test_h7_no_automatic_revision`, `test_h7_retraction_no_promotion` |

### Case Reconstruction read model (Slice 3A, AGC Session 014)

No tables are added or altered by this slice; the ERD is unchanged. The reconstruction is a transient projection ([CASE_RECONSTRUCTION.md](CASE_RECONSTRUCTION.md)) — these rows govern the read surface itself.

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Reconstruction: purity (non-effects) | ONT-PRN-024, ONT-PRN-010 | invariant | none — a pure read: no writes, no events, no transitions; twice-identical against unchanged records | — | Python composer issues only SELECTs; `argus_private.case_reconstruction` is STABLE (no writes possible); no evaluation-time values in the canonical payload | — (deliberately none: reconstruction is not a material mutation) | `test_reconstruction_pure_and_deterministic` |
| Reconstruction: dual-rendered equivalence | ONT-PRN-015 | invariant | — | — | semantic structural equality (jsonb equality) as the H8 requirement; canonical byte identity (chain_version=1 serialization rules, both canonicalizers parity-proven) as the strengthened conformance test | — | `test_h8_semantic_equality`, `test_h8_canonical_byte_identity` |
| Reconstruction: completeness against the closed manifest | ONT-PRN-003, ONT-PRN-006 (Article VIII) | invariant | — | — | every constitutional class classified in the Reconstruction Manifest; per-class DB count = reconstruction count; manifest-vs-registry coverage test breaks when a future table is unclassified | — | `test_manifest_completeness`, `test_manifest_covers_registry` |
| Reconstruction: retraction and degradation visibility | ONT-PRN-006 (Article VIII) | invariant | — | — | retracted records present with labeled retraction objects; degraded health surfaced per object; no selective omission by health or disposition | — | `test_retracted_records_visible` |
| Reconstruction: structural non-preference | ONT-PRN-023 (Article IV) | invariant | — | — | uniform per-class schema, no privileged slots, ordering solely by documented non-epistemic identifiers, symmetric top-level `hypothesis_alternatives`, no aggregation of uncertainty/health/boundary states; prohibited-key registry as tripwire | — | `test_structural_symmetry`, `test_no_prohibited_keys` |
| Reconstruction: historical/current pairing | ONT-PRN-025 | invariant | — | — | stored articulations and derived states side by side, labeled (`derived` containment); neither merged nor concealed | — | `test_historical_and_current_side_by_side` |
| Reconstruction: visibility envelope (SEALED) | ONT-EVA-001 (Article VI vs. VIII) | invariant | — | — | explicit `visibility` object; SEALED = existence-plus-status with withheld fields absent and declared (`withholding_basis: AUTHORITY_REQUIRED`); never silent omission; only FULL and SEALED authorized | — | `test_sealed_visibility_envelope` |
| Reconstruction: audit summary semantics | ONT-AUD-001 (Article VIII) | invariant | — | — | `integrity_status` ∈ CHAIN_VALID/CHAIN_INVALID/CHAIN_NOT_VERIFIED means chain integrity only; CHAIN_INVALID never prevents reconstruction (surface, never silently dispose); independent SQL recomputation in `argus_private.audit_chain_status` | — | `test_broken_chain_surfaced_not_hidden` |
| Reconstruction: refusal | ONT-CAS-001 | invariant | — | — | unknown case refuses with `ONT-CAS-001:unknown-case`; empty case reconstructs validly | — | `test_unknown_case_refused`, `test_empty_case_valid` |

### Storage Reconciliation (Slice 1E, ADR-0031/0032)

No tables are added or altered; the ERD is unchanged. Detection only — repair is behind a later gate.

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Scan: purity (non-effects) | ONT-PRN-027 | invariant | none — pure read: no writes, no transitions, no quarantine, no repair, no audit emission; twice-identical canonical reports over unchanged DB + store | — | prober/composer issue only reads; classifier functions STABLE; runtime metadata confined to the meta envelope | — (deliberately none) | `test_scan_pure_and_deterministic` |
| Integrity conditions: closed set, never truth | ONT-PRN-026 | invariant | — | — | closed enum MATCHED/MISSING/DIVERGENT/UNREADABLE/UNVERIFIED; no CORRECT/AUTHORITATIVE/TRUE_VERSION/WINNER exists; prohibited-stem scan over report surfaces; no path from any condition into any epistemic record | — | `test_no_truth_surface`, `test_classification_matrix` |
| MATCHED: full applicable invariant agreement | ONT-PRN-026 (Amendment 2) | invariant | — | — | MATCHED requires verification performed + present + readable + supported algorithm + digest, size, and storage-location agreement — mutual consistency, never authenticity | — | `test_matched_requires_all_invariants` |
| DIVERGENT: diagnostic reasons | ONT-PRN-026 (Amendment 1) | invariant | — | — | DIGEST_MISMATCH / SIZE_MISMATCH / STORAGE_LOCATION_MISMATCH as subconditions; recorded vs. expected storage refs distinguished; a matching hash never hides metadata drift | — | `test_divergence_reasons` |
| Classification precedence | ONT-PRN-015 (Session 016) | invariant | — | — | normative five-step precedence in STORAGE_RECONCILIATION.md §5; Python classifier + `argus_private.classify_storage_integrity` dual-rendered over shared observed facts, conformance-swept | — | `test_h9_classifier_conformance` |
| SEALED: metadata-only probe | ONT-EVA-001 (Article VI) | invariant | — | — | default scan never opens sealed content (a pure scan cannot audit a sealed read); UNVERIFIED with explicit envelope; observed.present = storage-level existence without content access; digest-bearing details withheld and declared | — | `test_sealed_metadata_only` |
| Stalled verification: separate surfacing | ONT-PRN-012 (ADR-0007 §4) | invariant | — | — | PENDING_VERIFICATION artifacts in `stalled_verification` only — never classified, never mixed into UNVERIFIED, never auto-transitioned | — | `test_stalled_separate_not_classified` |
| Operational summary: separated, reconciled | ONT-PRN-026 (Amendment 3) | invariant | — | — | counts outside the per-artifact results; sum of condition counts = classified permanent-storage artifacts; no evidentiary, epistemic, or prioritization meaning | — | `test_summary_sum_invariant` |
| ContentStore protocol contract | ONT-PRN-010, ONT-PRN-013 | invariant | — | — | reusable conformance suite every adapter must pass (write-once promotion, content-addressing rule, metadata-level existence, exact reads, quarantine retains, error normalization) — an adapter may not change what MISSING/UNREADABLE means | — | `test_content_store_contract` |
| Refusal | ONT-CAS-001 | invariant | — | — | unknown case refuses `ONT-CAS-001:unknown-case`; empty case reconciles validly | — | `test_unknown_case_refused_empty_valid` |

### Authenticated Actor Context (Slice 1F-A, ADR-0033)

No epistemic tables are added or altered. Migration 012 adds the database principal guard (read-side assertion) and wires it into the audit-append path as defense-in-depth; the FastAPI transport is the first application-layer surface.

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Actor attribution: derived from principal | ONT-PRN-028 | invariant | — | — | `bind_actor` derives the domain Actor from an `AuthenticatedPrincipal`; the endpoint never constructs `Actor(...)` from request fields; binding is pure | — (binding emits nothing) | `test_binding_matrix`, `test_api_records_authenticated_principal` |
| Command schemas: no identity field | ONT-PRN-028 (Amendment 3) | invariant | — | — | strict request schemas (`extra=forbid`); any caller identity field refused even when it matches the principal | — | `test_identity_input_prohibited`, `test_matching_identity_still_refused` |
| Unauthenticated command refused | ONT-PRN-028 | invariant | — | — | transport dependency requires a verified principal; DB guard fails closed (no principal bound → refuse); no record, no audit entry | — | `test_unauthenticated_refused`, `test_no_write_on_refusal` |
| Principal class vs. required action class | ONT-PRN-028, ONT-PRN-007 | invariant | — | — | `bind_actor` refuses `principal-class-mismatch`; a SERVICE principal cannot perform a HUMAN-only action by claiming HUMAN | — | `test_principal_class_mismatch` |
| SERVICE human_attribution: attribution only | ONT-PRN-028 (Amendment 2) | invariant | — | — | `human_attribution` traces to the provisioned principal, never payload; narrowed meaning (not authority); legacy `human_authority` field flagged for 1F-B | — | `test_service_human_attribution_from_principal` |
| Database principal guard: SET LOCAL, fail-closed | ONT-PRN-028 (Amendment 4) | invariant | — | — | `argus_private.assert_transaction_principal` at mutation entry; transaction-scoped `SET LOCAL`; consistency re-checked in `append_audit_event` as defense-in-depth; honest trust-boundary limit stated | — | `test_db_guard_actor_principal_mismatch`, `test_principal_does_not_leak_across_transactions` |
| Authentication ≠ authority | ONT-PRN-028 corollary | invariant | — | — | `AuthenticatedPrincipal` carries no permission set / case access / visibility; `bind_actor` performs no resource authorization (structural) | — | `test_authentication_confers_no_authority` |
| Identity ≠ epistemic meaning | ONT-PRN-028 corollary, Article IX | invariant | — | — | records authored under different authenticated principals are epistemically identical; differences confined to attribution/audit fields | — | `test_same_object_different_authors` |
| Refusal | ONT-PRN-007 | invariant | — | — | canonical codes (unauthenticated / identity-input-prohibited / identity-substitution / principal-class-mismatch / actor-principal-mismatch) | — | `test_refusal_codes` |

### Authority and Visibility (Slice 1F-B, ADR-0034/0035)

No epistemic tables are added or altered. Migration 013 adds the dual-render `authorize` decision function (no table access); grants come from an injected provider (persisted grants deferred).

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Authority decision: capability + Case scope | ONT-PRN-029 (Amendments 1, 5) | invariant | — | — | pure `authorize(required_capability, resource_case_id, grants)`; Case scope only (no `*`); no capability inheritance; dual-rendered Python + `argus_private.authorize`, conformance-swept | — | `test_authorize_matrix`, `test_authorize_conformance`, `test_capability_non_inheritance` |
| Resource scope: Case-A grant ≠ Case-B | ONT-PRN-029 (Amendment 5) | invariant | — | — | scope_id match required; a grant for one Case never authorizes another | — | `test_case_scope_isolation` |
| Provider returns facts, not decisions | ONT-PRN-029 (Amendment 4) | invariant | — | — | `AuthorityProvider` yields `AuthorityGrant` facts only; no ALLOW/DENY, no epistemic inspection, no scope expansion (structural) | — | `test_provider_facts_only` |
| Two-stage visibility: no existence leak | ONT-PRN-030 (Amendment 2) | invariant | — | — | no `CASE_READ` → generic resource denial (existence not disclosed); `CASE_READ` → existence visible, protected fields explicitly withheld; withholding exposed only within the entitled-to-existence stage | — | `test_no_existence_leak_without_case_read`, `test_withholding_when_existence_disclosed` |
| Visibility projection: singular record | ONT-PRN-030, ONT-PRN-029 | invariant | — | — | `state/existence_visible/metadata_visible/content_visible/withholding_basis` derived from capabilities; the underlying record is singular, only the projection changes (O14 falsifier) | — | `test_o14_projection_varies_record_singular` |
| Protected content: audit before disclosure | ONT-PRN-030 (Amendment 3) | CT (access history) | append access event | Human (SEALED_CONTENT_READ) | content returned only after `sealed-content-accessed` durably appended; audit failure → no disclosure; read failure → no success event; evidence byte-identical | sealed-content-accessed / sealed-content-access-failed | `test_protected_access_audited`, `test_content_withheld_if_audit_fails`, `test_evidence_byte_identical` |
| SEALED_VERIFY ≠ SEALED_CONTENT_READ | ONT-PRN-030, ONT-PRN-026 | invariant | — | — | `SEALED_VERIFY` returns the integrity result only, never bytes; integrity ≠ authenticity survives elevated access | (verification is a read; no epistemic mutation) | `test_sealed_verify_no_content`, `test_verify_is_integrity_not_authenticity` |
| Epistemic neutrality | ONT-PRN-029, Article IX | invariant | — | — | authority grant/denial changes no stored field, derived state, or admissibility; two principals see identical epistemic state for shared fields | — | `test_authority_changes_no_epistemic_state` |
| Authentication ≠ authority; trusted-internal ≠ user authority | ONT-PRN-029, ONT-PRN-028 | invariant | — | — | an authenticated principal with no grants is denied; trusted-internal (no principal) is infrastructure, never a user-facing authority pass | — | `test_authentication_grants_no_authority`, `test_trusted_internal_not_user_authority` |
| Action authority vs mutation | ONT-PRN-029 | invariant | — | — | read authority without an action capability cannot write; denied action writes nothing | — | `test_read_authority_cannot_write`, `test_denied_action_writes_nothing` |

### Case Presentation (Slice 1F-C, ADR-0036)

No schema changes, no migration, no new refusal codes: the review surface consumes the 1F-B authorized projection unchanged. These rows govern the rendered surface itself ([CASE_PRESENTATION.md](CASE_PRESENTATION.md)).

| Entity / field group | Ontology rule | Class | Permitted mutations | Permitted actors | Enforcing mechanism | Material mutations audited | Verifying test |
|---|---|---|---|---|---|---|---|
| Rendered page: read-only, downstream of authority | ONT-PRN-031, ONT-PRN-029 | invariant | none — no mutation path, no workflow controls; renderer receives the projection only (no grants, no authorize access) | — | pure `render_case_review(projection)`; route applies 1F-B generic denial before rendering; defensive omission permitted, visibility expansion structurally impossible | — (an ordinary constitutional read) | `test_projection_only_authority`, `test_no_existence_leak_review` |
| Non-interference: structure, never meaning | ONT-PRN-031 (Amendment 1) | invariant | — | — | closed presentation vocabulary; no paraphrase/summary/inference/evaluation/synthesis of epistemic content | — | `test_no_synthesized_content` |
| Content parity: exactly once, both directions | ONT-PRN-031 (Amendment 2) | invariant | — | — | every projection-derived value present once in its structural context; visible values outside the projection belong to the closed vocabulary; no unauthorized duplication (repetition ≠ prominence) | — | `test_content_parity_completeness`, `test_no_unauthorized_duplication` |
| Peer symmetry: equal rules, not equal dimensions | ONT-PRN-031 (Amendment 4) | invariant | — | — | same template/heading level/field order/classes/state/landmarks for peers; no conditional prominence by health, disposition, or identity; no truncation for geometry | — | `test_peer_rule_equality` |
| Retraction visibility, inline | ONT-PRN-006, ONT-PRN-031 (Amendment 5) | invariant | — | — | citation order in one section; `Status: RETRACTED` + reason inline; visible retracted count; no "failed" grouping, no condemnation styling | — | `test_retractions_visible_inline` |
| Ordering and identity | ONT-PRN-031 | invariant | — | — | citation order only; citations visible (`Hypothesis — HYP-000001`); no ordinal or "main" labels | — | `test_citation_order_and_identity` |
| Health/integrity as text; no truth semantics | ONT-PRN-026, ONT-PRN-031 | invariant | — | — | text labels primary; no green/red truth colors; no ✓/✗/⚠ as primary signal; neutral definitions on-page | — | `test_health_text_no_truth_semantics` |
| Contamination: text, attributes, CSS | ONT-PRN-018, ONT-PRN-031 | invariant | — | — | scanner over visible text + class/id/data-*/aria-label/title against the transcribed registries; CSS in conformance review | — | `test_attribute_and_css_contamination` |
| Accessibility-semantic source parity | ONT-PRN-031 (Amendment 3) | invariant | — | — | static DOM inspection: source order, heading hierarchy, landmarks, peer depth, focus order, accessible names; full AT conformance claims NOT AUTHORIZED | — | `test_accessibility_semantic_source_parity` |
| Red-team discipline (O12 applied to presentation) | ONT-PRN-031, ONT-PRN-015 | invariant | — | — | synthetic violating fixtures must fail the conformance scanner (featured slot, vocabulary, health ordering, asymmetric expansion, hidden retraction, truth CSS, synthesized summary, order mismatch) | — | `test_red_team_fixtures_fail_scanner` |

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
| 0.5.0 | 2026-07-13 | Slice 2A gate: Interpretation rows — uncertainty envelope, grounding snapshot, no-preference invariant, derived grounding_health. |
| 0.6.0 | 2026-07-13 | Slice 2B gate: Unknown/UnknownLink/UnknownResolution rows per ADR-0024/0025 and the Session 008 amendments. |
| 0.7.0 | 2026-07-13 | Slice 2C gate: Contradiction/ContradictionMember/ContradictionDisposition rows (ADR-0027, Session 010 amendments). |
| 0.8.0 | 2026-07-13 | Slice 2D gate: Hypothesis/HypothesisGrounding/HypothesisAlternative/ContradictionLink rows per ADR-0028 (ONT-PRN-023) and the five Session 012 amendments — creation-time vs. derived alternative state, mandatory boundary articulation, versioned fingerprints, three-state health, H7 negative obligations. |
| 0.9.0 | 2026-07-13 | Slice 3A gate: Case Reconstruction read-model rows (purity, two-level equivalence, manifest completeness, visibility envelope, structural non-preference, historical/current pairing, audit summary semantics, refusal) per the six Session 014 amendments. No schema changes. |
| 0.10.0 | 2026-07-13 | Slice 1E gate: Storage Reconciliation rows (purity, closed integrity conditions, strengthened MATCHED, diagnostic divergence reasons, normative precedence, sealed metadata-only probe, stalled-verification separation, summary reconciliation, ContentStore contract, refusal) per the four Session 016 amendments. No schema changes. |
| 0.11.0 | 2026-07-13 | Slice 1F-A gate: Authenticated Actor Context rows (derived attribution, identity-free schemas, unauthenticated refusal, principal-class check, attribution-only human_attribution, SET LOCAL fail-closed DB guard, authentication≠authority, identity≠epistemic, refusal codes) per ONT-PRN-028 and the four Session 018 amendments. No epistemic schema changes. |
| 0.12.0 | 2026-07-13 | Slice 1F-B gate: Authority and Visibility rows (dual-render authorize, Case-scope isolation, facts-only provider, two-stage visibility with no existence leak, singular-record projection, audit-before-disclosure, SEALED_VERIFY≠CONTENT_READ, epistemic neutrality, authentication/trusted-internal ≠ authority) per ONT-PRN-029/030 and the five Session 020 amendments. No epistemic schema changes. |
| 0.13.0 | 2026-07-13 | Slice 1F-C gate: Case Presentation rows (projection-only rendering, non-interference, two-class content parity, peer-rule symmetry, inline retraction visibility, citation identity, text-primary health semantics, text/attribute/CSS contamination, accessibility-semantic source parity, red-team scanner discipline) per ONT-PRN-031 and the five Session 022 amendments. No schema changes, no migration. |
