# ARGUS Case Reconstruction Specification

- **Document version:** 0.1.0 (Slice 3A gate, incorporating the six AGC Session 014 amendments)
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md) 1.15.0 via the [Derivation Specification](DERIVATION_SPECIFICATION.md), the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md), and [Entity Lifecycles](ENTITY_LIFECYCLES.md)
- **Consumed by:** the Python composer (`argus.reconstruction`), the PostgreSQL rendering (`argus_private.case_reconstruction`), and the H8 conformance suite (triangulation leg 3, ONT-PRN-015)

**The governing rule (AGC Session 014):** *Composition may reveal relationships already present in the constitutional graph. It may never create a meaning that no constitutional record already carries.*

## 1. Ontological status (Amendment 1)

> A Case Reconstruction is a **transient, read-only projection** of the constitutional state of one Case at the time of evaluation. It has **no epistemic standing independent of the records from which it is derived**.

A CaseReconstruction is **not** a sixteenth first-class object (Session 014: NOT AUTHORIZED). It has no persistent identity, no citation, no lifecycle, no creator, no retraction, no independent provenance, and no audit history. It is the system's reconstruction **of its records** — not of reality (ONT-PRN-001). Exposing it under any framing that suggests "the system's reconstruction of reality" is a constitutional defect.

## 2. Non-effects (ONT-PRN-024 constraint floor)

Reconstruction is a pure read. It mutates nothing, emits no domain or audit events, triggers no transitions, retracts nothing, repairs nothing, and never reaches across cases (Article VI). Evaluating it twice against unchanged records yields identical documents. Database transaction identifiers, request identifiers, and evaluation timestamps never enter the canonical payload (Amendment 6: a pure function must not produce different bytes because the clock moved).

## 3. Two levels of equivalence (Amendment 2)

**H8 is tested through semantic structural equality and strengthened by canonical byte identity.**

- **Level 1 — constitutional semantic equivalence (the H8 requirement):** both renderings contain exactly the same nodes, relationships, stored values, derived values, visibility states, historical/current distinctions, and retraction states. Verified by structural comparison (e.g., `jsonb` equality, which is representation-independent).
- **Level 2 — canonical byte equivalence (the strengthened conformance test):** after applying §7's serialization rules, both outputs produce identical bytes. Byte divergence fails **implementation conformance**; it does not automatically prove **epistemic divergence** until the cause is classified (a timestamp-precision mismatch is a conformance defect, not evidence that one renderer constructed a different investigation). H8 reporting classifies any divergence accordingly.

## 4. Structural non-preference (Amendment 3)

Lexical scanning is one conformance mechanism, not the constitutional rule. The rule is **structural**:

1. One uniform schema for every object of the same class — no privileged slots, no "featured" or exceptional placement, no summary object that aggregates one class into a judgment about another.
2. Field presence may differ within a class **only** as a consequence of the visibility envelope (§6) — never as a consequence of health, disposition, alternative status, retraction of a sibling, or any epistemic state.
3. Ordering is exclusively by the documented non-epistemic identifiers of §8. Insertion order, database physical order, and ORM return order are never load-bearing. Determinism is designed, not observed.
4. No selective omission based on health or disposition: retracted and degraded records are present and labeled.
5. No aggregation: uncertainty statuses, health states, and boundary states appear per-object and are never combined into any scalar, grade, count-of-support, or cross-class summary judgment.

The prohibited-key registry (structured surface, D-PRN-018 discipline) additionally forbids these stems in canonical-payload key names: `verdict`, `conclu`, `narrat`, `preferred`, `featured`, `leading`, `primary`, `rank`, `weight`, `score`, `confiden`, `probab`, `winner`, `theory`, `accept`, `likelihood`, `predict`, `refut`, `promot`, `best`.

## 5. The Reconstruction Manifest (Amendment 4)

Completeness is defined against this **closed manifest**, not against intuition. **Every constitutional record is accounted for exactly once, subject to its authorized visibility envelope.** The completeness test compares the implemented manifest against the domain registry (every mapped table must be classified), so a future constitutional object cannot leave the reconstruction silently "complete."

| Constitutional class | Classification | Where accounted |
|---|---|---|
| Case | NODE | `case` |
| CaseAuthority | NODE | `case.authorities[]` (append-only, in full) |
| EvidenceArtifact | NODE | `evidence_artifacts[]` (visibility envelope applies) |
| SourceLocator | NODE | `source_locators[]` |
| Observation | NODE | `observations[]` |
| ObservationGrounding | RELATIONSHIP | `observations[].groundings[]` |
| Interpretation | NODE | `interpretations[]` |
| InterpretationGrounding | RELATIONSHIP | `interpretations[].groundings[]` |
| Unknown | NODE | `unknowns[]` |
| UnknownLink | RELATIONSHIP | `unknowns[].links[]` (boundary-owned) |
| UnknownResolution | DISPOSITION | `unknowns[].resolution` |
| Contradiction | NODE | `contradictions[]` |
| ContradictionMember | RELATIONSHIP | `contradictions[].members[]` |
| ContradictionDisposition | DISPOSITION | `contradictions[].disposition` |
| ContradictionLink | RELATIONSHIP | `contradictions[].links[]` (boundary-owned) |
| Hypothesis | NODE | `hypotheses[]` |
| HypothesisGrounding | RELATIONSHIP | `hypotheses[].groundings[]` |
| HypothesisAlternative | RELATIONSHIP | `hypothesis_alternatives[]` — **top-level**: the pair is symmetric and unordered; nesting it under either Hypothesis would privilege one side structurally |
| AuditEntry | SUMMARY_METADATA | `audit_chain` (count + integrity status; the full trail remains separately queryable per Article VIII) |
| CaseAuditHead | SUMMARY_METADATA | `audit_chain` (verification input) |
| Derived states (`is_grounded`, `grounding_health`, contradiction health/status, unknown disposition, `hypothesis_health`, `current_alternative_state`, boundary states, chain integrity) | DERIVED_STATE | per-object `derived` objects, labeled |
| Artifact `storage_ref`; staging area; content bytes | EXCLUDED_BY_DESIGN | operational pointer / pre-constitutional / never in a projection |

Relationships count as relationships — a junction row is accounted once at its manifest location, never duplicated as nodes.

## 6. Visibility envelope (Amendment 5)

Absence must never be ambiguous. Every EvidenceArtifact carries an explicit envelope:

```
visibility:
  state: FULL | SEALED
  content_visible: boolean
  provenance_detail_visible: boolean
  withholding_basis: null | "AUTHORITY_REQUIRED"
```

Only the states ARGUS currently understands are authorized: `FULL` and `SEALED` (`REDACTED` has no constitutional meaning yet and is **not** authorized). A `SEALED` artifact appears as existence-plus-status: `id`, `status`, `created_at`, `retraction`, and the envelope — with `hash_algorithm`, `hash_digest`, `size_bytes`, `media_type`, `acquisition_description`, `ingested_by_class`, `ingested_by_id`, and `human_authority` **absent and declared withheld** (`content_visible: false`, `provenance_detail_visible: false`, `withholding_basis: "AUTHORITY_REQUIRED"`). `withholding_basis` names the category only; it never exposes authority details (none exist to expose before the authority model). The reconstruction must reveal that the information exists and that its absence from the projection is intentional — a sealed object is never silently omitted.

## 7. Canonical serialization

The canonical payload is a JSON document serialized per the **chain_version=1 canonical JSON rules already normative for the audit chain** (ADR-0016; both renderings of that serializer are parity-proven): UTF-8; object keys sorted by codepoint; separators `,` and `:` with no whitespace; non-ASCII unescaped; **no floats** (all numbers in this document are integers). Timestamps use the chain's canonical form: `YYYY-MM-DDTHH:MM:SS.ffffffZ` (UTC, fixed six-digit microseconds). Enumerations serialize as their stable string values. Absent-by-visibility fields are absent; all other declared fields are present, with JSON `null` for empty.

**Document/meta separation (Amendment 6):** the byte-compared **canonical payload** (`document`) describes only the Case's constitutional state. Transport metadata — `generated_at`, `reconstruction_schema_version`, `ontology_version`, `case_id` echo — travels in a separate `meta` envelope outside the canonical payload and outside conformance comparison (versions must still be accurate; `generated_at` is the circumstance of the request, not a property of the Case).

## 8. Canonical section order and list ordering

Sections appear in **canonical section order**: `case`, `evidence_artifacts`, `source_locators`, `observations`, `interpretations`, `unknowns`, `contradictions`, `hypotheses`, `hypothesis_alternatives`, `audit_chain`. **Section order expresses ontology organization only and carries no evidentiary, temporal, causal, or preferential meaning.** (The word "ladder" is deliberately not used in this rendered context.)

Every list's ordering is explicit and non-epistemic. Where a class has citations, citation order (documented non-evidentiary since Slice 2A); where it does not, the opaque identifier — an adaptation of the Session 014 table recorded here because EvidenceArtifact and SourceLocator carry no citations:

| List | Order key |
|---|---|
| `case.authorities` | (`created_at`, id) — append sequence |
| `evidence_artifacts` | opaque id |
| `source_locators` | opaque id |
| `observations` / `interpretations` / `unknowns` / `contradictions` / `hypotheses` | citation |
| `observations[].groundings` | locator id |
| `interpretations[].groundings` | observation id |
| `unknowns[].links` | (target_type, target_id) |
| `contradictions[].members` | (member_type, member_id) |
| `contradictions[].links` | hypothesis id |
| `hypotheses[].groundings` | interpretation id |
| `hypothesis_alternatives` | (hypothesis_a_id, hypothesis_b_id) — the stored normalized pair |

## 9. Per-object content

Every node carries its stored fields (historical truth), its `ontology_class`, its `retraction` object (`null`, or `{retracted_at, reason}` — plus `superseded_by` for artifacts) — retracted records are **present and labeled, never omitted** — and a `derived` object holding its read-time derived states, labeled by containment. **Historical articulation and current derived condition appear side by side and are never merged (ONT-PRN-025 / ADR-0030):** `alternative_articulation_at_creation` and `alternative_absence_explanation` beside `derived.current_alternative_state`; disposition records beside derived boundary activity; stored envelopes beside derived health. Relationship rows carry their snapshots (fingerprints, roles, link times) exactly as stored.

`audit_chain` (Amendment 6a):

```
audit_chain:
  entry_count: <integer>
  integrity_status: CHAIN_VALID | CHAIN_INVALID | CHAIN_NOT_VERIFIED
```

`CHAIN_VALID` means **only** that the append-only audit chain passed its structural/cryptographic integrity verification. It never means evidence, observations, claims, or the case are verified. `CHAIN_NOT_VERIFIED` is reserved for renderings that cannot verify (neither current rendering uses it). **`CHAIN_INVALID` never prevents reconstruction** — the projection surfaces the integrity problem and presents the records; it does not hide the case because its audit chain failed (surface degradation; never silently dispose of the underlying record).

## 10. Refusal conditions

| Condition | Code |
|---|---|
| Case does not exist | `ONT-CAS-001:unknown-case` |

An empty case is not an error: it reconstructs to a valid document with empty sections. No other refusal exists in v0.1 (authorization arrives with the authenticated-actor model, Slice 1F; the standing limitation is restated with every H8 report).

## 11. Verifying tests

The H8 suite (Invariant Matrix 0.9.0 rows) transcribes this specification: semantic equality; canonical byte identity; manifest completeness (per-class DB count = reconstruction count, and manifest-vs-registry coverage); structural symmetry of plural Hypotheses after identity normalization; visibility envelope on SEALED; broken-chain surfacing (`CHAIN_INVALID` with records present); purity; historical/current pairing; retraction visibility; prohibited-key scan; empty-case validity; unknown-case refusal.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative specification at the Slice 3A gate, incorporating the six AGC Session 014 amendments: projection status (not a first-class object), two-level equivalence, structural non-preference, the closed Reconstruction Manifest, the visibility envelope, the audit-chain summary enum, and document/meta separation. |
