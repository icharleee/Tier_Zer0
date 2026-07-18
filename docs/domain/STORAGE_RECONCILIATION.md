# ARGUS Storage Reconciliation Specification

- **Document version:** 0.1.0 (Slice 1E gate, incorporating the four AGC Session 016 amendments)
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md) 1.16.0 (ONT-PRN-026, ONT-PRN-027) via the [Derivation Specification](DERIVATION_SPECIFICATION.md), with storage semantics from ADR-0006 (boundary 5) and ADR-0007
- **Consumed by:** the Python scan (`argus.reconciliation_scan`), the PostgreSQL classifier (`argus_private.classify_storage_integrity`), the ContentStore protocol conformance suite, and the H9 suite (triangulation leg 3, ONT-PRN-015)

**The governing rule (AGC Session 016):** *Reconciliation may tell ARGUS that its representations disagree. It may never tell ARGUS what reality therefore means.*

## 1. Definition and status

Reconciliation in ARGUS **detects, surfaces, and accounts for divergence between stored representations of constitutional records without deciding which representation is epistemically authoritative** (Resolution 021). It is infrastructural, never epistemic. A reconciliation report is a transient, read-only projection of storage-integrity state — like the Case Reconstruction, it has no persistent identity, lifecycle, or epistemic standing.

*Database hash matches object store* means **storage representations agree** — never *the evidence is authentic*. *Hash mismatch* means **representations diverge** — never *the evidence is false* (ONT-PRN-026).

## 2. Non-effects (ONT-PRN-027: detect ≠ decide ≠ mutate)

The scan is a pure read of ARGUS state: it mutates no content, metadata, provenance, lifecycle state, or epistemic record; retracts nothing; quarantines nothing; repairs nothing; emits no audit events; produces no epistemic conclusion. Repair does not exist in this slice — detection first; restoration sits behind a second, later gate (ADR-0032). The scan may inform the existing quarantine transition; invoking it is a distinct, separately audited act outside the scan. **Automatic quarantine is NOT AUTHORIZED.**

**Observation-envelope purity (Amendment 4):** the store is external, so observations are time-sensitive; a change in the store between scans is not a purity failure. The purity rule: **two scans over unchanged database state and unchanged content-store state produce identical canonical reports.** Runtime metadata (`generated_at`, `backend_type`, filesystem/access timestamps, request identifiers) never enters the canonical payload — it travels in a separate `meta` envelope outside the H9 comparison surface. The report represents the observed integrity state, not incidental properties of the scan invocation.

## 3. Storage-reference authority (Amendment 1)

Three locations are distinguished; none is *epistemically* authoritative:

| Term | Meaning |
|---|---|
| `recorded_storage_ref` | Historical metadata persisted with the artifact (`storage_ref`) |
| `expected_storage_ref` | Deterministically derived from the constitutional content-addressing rule: `{hash_algorithm}/{hash_digest}` |
| observed storage location | What the prober actually inspected (the expected content-addressed location) |

A recorded ref pointing somewhere unexpected is a divergence **even if bytes at the expected location match** — metadata drift is never silently normalized away.

## 4. The closed integrity-condition set and diagnostic reasons

Conditions (closed for 1E; **integrity conditions, never truth conditions**): `MATCHED`, `MISSING`, `DIVERGENT`, `UNREADABLE`, `UNVERIFIED`. No `CORRECT`, `AUTHORITATIVE`, `TRUE_VERSION`, or `WINNER` exists or may be added (ADR-0031).

**MATCHED requires full applicable invariant agreement (Amendment 2)** — all of: `verification_performed`, `present`, `readable`, `supported_algorithm`, `recomputed_digest = recorded_digest`, `observed_size = recorded_size`, `recorded_storage_ref = expected_storage_ref`. MATCHED means *all storage representations checked by this scan are mutually consistent* — still never *evidence is authentic*.

**DIVERGENT** includes any readable permanent representation whose bytes, size, digest, or expected storage location do not conform to recorded constitutional storage metadata. Machine-readable **diagnostic subconditions** (not new top-level states), reported sorted: `DIGEST_MISMATCH`, `SIZE_MISMATCH`, `STORAGE_LOCATION_MISMATCH`. A matching hash never hides metadata drift.

## 5. Canonical classification precedence (normative — Amendment, precedence section)

Independent implementations must classify identically; precedence is normative here, never inferred from code:

1. If permanent verification is **intentionally not performed** → `UNVERIFIED`. This resolves: SEALED content under the default scan; unsupported hash algorithm (no attempt is made to guess a replacement); QUARANTINED artifacts (verification suspended pending human disposition — quarantine bytes are retained under quarantine semantics, not permanent-location semantics).
2. Else if bytes absent at the expected content-addressed location → `MISSING`.
3. Else if bytes cannot be read → `UNREADABLE` (read errors are normalized into the observation — they never escape the scan).
4. Else if any checked storage invariant disagrees → `DIVERGENT` (with its reasons).
5. Else → `MATCHED`.

## 6. Sealed handling (gate decision, approved)

The default scan never opens SEALED content: every sealed-content read must audit, and a pure scan appends nothing. A SEALED artifact classifies `UNVERIFIED` (precedence step 1) with an explicit envelope:

```
visibility:
  state: SEALED
  content_visible: false
  verification_performed: false
  withholding_basis: AUTHORITY_REQUIRED
```

`observed.present` for SEALED objects means **storage-level existence detectable without content access** — not *content successfully read*; those are different facts. Recorded digest, size, and reference details are withheld from the sealed entry (they would reveal the content-addressed identity); the withholding is declared, never silent. The elevated, audited verification path for sealed content remains outside this slice. FULL entries carry the same envelope keys (`state: FULL`, `content_visible: true`, `verification_performed` as performed, `withholding_basis: null`); field-set differences arise only from the visibility envelope, never from integrity state.

## 7. Report shape

Canonical payload sections, in order:

- **`results`** — one entry per **permanent-storage artifact** (status `ACTIVE`, `SEALED`, `RETRACTED`, or `QUARANTINED`), ordered by artifact id: `{artifact_id, status, condition, divergence_reasons[], observed{present, readable, supported_algorithm, recomputed_digest, observed_size}, recorded{hash_algorithm, hash_digest, size_bytes, recorded_storage_ref, expected_storage_ref}, visibility{…}}` — with the `recorded` object and digest-bearing observations absent (declared withheld) on SEALED entries. Retracted artifacts are included and labeled by their `status` — retention is constitutional.
- **`stalled_verification`** — artifacts still `PENDING_VERIFICATION`, kept **structurally separate** (Amendment 3): *permanent object not verified* ≠ *verification process not yet completed*. Entries `{artifact_id, status, staged_since}`; surfaced, never auto-transitioned, never mixed into `UNVERIFIED`.
- **`operational_summary`** — `{matched_count, missing_count, divergent_count, unreadable_count, unverified_count}`, **outside the per-artifact result set**. *Operational counts summarize scan outcomes only and carry no evidentiary, epistemic, or prioritization meaning.* Invariant: the sum of condition counts equals the number of classified permanent-storage artifacts.

Serialization follows the chain_version=1 canonical JSON rules (as in the Case Reconstruction); all numbers are integers. Prohibited stems on the report's structured surfaces (keys and condition values): `authentic`, `truth`, `correct`, `winner`, `authoritat`, `prevail`, `repair`, `restor`, `verdict`, `conclu`.

## 8. Refusal conditions

| Condition | Code |
|---|---|
| Case does not exist | `ONT-CAS-001:unknown-case` |

A case with no artifacts reconciles validly (empty sections, zero counts).

## 9. Dual rendering (the H9 conformance surface, honestly bounded)

The database cannot probe the filesystem, so the scan splits:

- **Probe** (single implementation, declared as such in every H9 report): the Python prober collects raw observed facts from the ContentStore — metadata-level existence, readability, recomputed digest, observed size — normalizing errors into observations.
- **Classification** (dual-rendered): a pure function from observed facts to condition and reasons — the Python classifier and `argus_private.classify_storage_integrity` / `argus_private.storage_divergence_reasons` — independently derived from §4–5, conformance-swept against the transcribed matrix. **The dual-rendering experiment applies to the classification of shared observations, not to independent filesystem probing.**

The separation is itself the registered candidate O11 pattern: *storage fact ≠ integrity classification ≠ epistemic judgment*.

## 10. ContentStore protocol conformance (required by Session 016)

Every adapter — LocalContentStore now, MinIO later — must satisfy one behavioral contract, verified by a reusable conformance suite: staged put/read round-trip; **write-once promotion** (double promotion of the same digest is a no-op returning the same reference); the content-addressing rule for `expected_storage_ref`; **metadata-level existence** (`permanent_exists` succeeds without content access); exact-byte permanent reads; quarantine retains, never deletes; staging release only after activation; **error normalization** (absence and unreadability are reportable observations, not escaping exceptions). A future adapter may not change what `MISSING`, `UNREADABLE`, or metadata-only existence means.

## 11. Verifying tests

The H9 suite transcribes this specification: the nine-artifact fixture (A `MATCHED`; B `MISSING`; C `DIVERGENT`/`DIGEST_MISMATCH`; D `UNREADABLE`; E SEALED → `UNVERIFIED` with envelope; F `DIVERGENT`/`SIZE_MISMATCH`; G `DIVERGENT`/`STORAGE_LOCATION_MISMATCH`; H unsupported algorithm → `UNVERIFIED`; I `PENDING_VERIFICATION` → `stalled_verification` only), the negative obligations (no retraction, no transition, no rewrite, no provenance change, no epistemic change, no audit emission, no truth/falsity label), second-scan determinism, the summary-sum invariant, and the classifier conformance sweep.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative specification at the Slice 1E gate, incorporating the four AGC Session 016 amendments: storage-reference authority triple, strengthened MATCHED, diagnostic divergence reasons, operational-summary separation, observation-envelope purity, and normative classification precedence. |
