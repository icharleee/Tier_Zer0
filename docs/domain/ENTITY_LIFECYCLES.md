# ARGUS Entity Lifecycles

- **Document version:** 2.3.0 — Ratified at 1.0.0 by AGC Review Session 001; 2.2.0 applied the operational/epistemic separation to Contradiction; 2.3.0 adds the Hypothesis creation preconditions (ONT-PRN-023), HypothesisAlternative (§15), and ContradictionLink (§16) per AGC Session 012
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md); structural context in the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md)

This document is authoritative for entity states and permitted transitions. The Domain Schema Specification references it per entity; the [Invariant Matrix](INVARIANT_MATRIX.md) will specify the enforcing mechanism for each transition.

**Conventions.** Immutability classes CI/V/CT per Domain Schema Specification C5; retraction pattern per C6. Every transition below is a material mutation and emits an AuditEntry atomically (C9). Per ONT-PRN-012 (Resolution 007), every constitutional transition is explicit — an audit event, a responsible actor, a timestamp, an allowed predecessor state — and these tables are the authoritative allowed-predecessor registry; implementations encode transitions as named operations, never bare status writes. "Human" = HumanActor, "AI" = AIWorkflow, "System" = SystemProcess (C1). The AI **review status** (`UNREVIEWED → ACCEPTED | REJECTED`, human-only, at most one transition, per C8) is orthogonal to lifecycle state and applies to every AI-created record; it is not repeated in each table.

---

## 1. Case (CT)

```
OPEN ⇄ SUSPENDED
OPEN → CLOSED → OPEN (reopen, with justification)
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → OPEN | Human | Legal authority basis recorded | case-created |
| OPEN → SUSPENDED | Human | Reason recorded | case-suspended |
| SUSPENDED → OPEN | Human | Reason recorded | case-resumed |
| OPEN → CLOSED | Human | Reason recorded | case-closed |
| CLOSED → OPEN | Human | Justification recorded | case-reopened |

`CLOSED` freezes analytical writes; reads (with authority) and audit emission continue. No deleted state exists.

## 2. EvidenceArtifact (CI content; CT operational fields)

Pre-constitutional: **STAGED** — bytes exist in the staging area, tracked by ingestion session only; nothing else is guaranteed — no domain record, no ontology, no provenance, no claims (ADR-0007 §2).

Constitutional record states:

```
PENDING_VERIFICATION → ACTIVE → RETRACTED
        │                 ├──→ SEALED ⇄ ACTIVE
        └──→ QUARANTINED ←┘
                └──→ (human disposition: RETRACTED, or ACTIVE after verified recovery)
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → PENDING_VERIFICATION | Human or System (attributing human authority) | Bytes staged; system-computed hash; acquisition description recorded (T1, atomic with audit) | artifact-ingested |
| PENDING_VERIFICATION → ACTIVE | System (verification) | Staged and permanent copies both pass integrity verification (ADR-0007 §3–4; T2, atomic with audit) | artifact-activated |
| PENDING_VERIFICATION → QUARANTINED | System (detection) | Hash mismatch or corruption; bytes retained in quarantine | artifact-quarantined |
| ACTIVE → QUARANTINED | System (detection) | Integrity failure detected post-activation (e.g., read-time hash mismatch) | artifact-quarantined |
| QUARANTINED → RETRACTED | **Human only** | Disposition rationale recorded | artifact-retracted |
| QUARANTINED → ACTIVE | **Human only** | Re-verification passed; recovery rationale recorded | artifact-reactivated |
| ACTIVE → RETRACTED | Human | Reason; superseding artifact linked where applicable | artifact-retracted |
| ACTIVE → SEALED | Human | Legal basis recorded | artifact-sealed |
| SEALED → ACTIVE | Human | Legal basis recorded | artifact-unsealed |

No SourceLocator may be created against a non-`ACTIVE` artifact. Every read of `SEALED` content emits an audit event. Quarantine disposition is human-only: the system detects, humans dispose (ONT-PRN-007).

## 3. SourceLocator (V)

```
ACTIVE → RETRACTED
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → ACTIVE | Human or AI (as part of a proposal) | Target artifact `ACTIVE`; address resolves within artifact bounds | locator-created |
| ACTIVE → RETRACTED | Human | Reason; replacement linked where applicable | locator-retracted |

When the owning artifact is retracted or sealed, the locator is flagged (downstream-degraded), not transitioned; flags propagate up the ladder for human disposition.

## 4–6. Observation, Interpretation, Hypothesis (V)

The three ladder claims share one lifecycle:

```
ACTIVE → RETRACTED        (review status orthogonal, per C8)
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → ACTIVE | Human or AI (proposal; Hypothesis: **Human only** — AI authorship NOT AUTHORIZED, Session 012) | Full provenance (C7); ladder references valid (C10): Observation ≥1 SourceLocator; Interpretation ≥1 Observation; Hypothesis ≥1 `DERIVED_FROM` Interpretation (contextual-only inadmissible). Hypothesis additionally (ONT-PRN-023): uncertainty envelope; testability statement + challenge condition; alternative articulation (link or absence explanation, recorded immutably at creation); Unknown and Contradiction articulation (boundary link or explicit no-current explanation) | claim-created |
| ACTIVE → RETRACTED | Human | Reason; successor linked where applicable | claim-retracted |
| (flag) ungrounded / grounding-degraded | System (detection) | Every supporting reference retracted, or any reference degraded | grounding-flag-raised |

Flags are surfaced states, not transitions: a degraded claim awaits **human** disposition and is never auto-retracted (Article II). **Hypothesis has no `CONFIRMED`, `TRUE`, or any terminal success state** — conviction lives in human Understanding, outside the system. Hypothesis derived states (`hypothesis_health` CURRENT/DEGRADED/UNSUPPORTED, `current_alternative_state`, boundary states) are computed, never stored, and never transition anything: even UNSUPPORTED — no `DERIVED_FROM` Interpretation remains current — leaves the historical explanation recorded and awaiting human review. Boundary resolution/disposition and sibling retraction alter no stored Hypothesis field.

## 7. Contradiction (V description; operational state CT; terminal disposition via ContradictionDisposition)

Two independent families (AGC Session 010 / ADR-0027, mirroring §9):

```
Operational (CT, human-only, reversible):        OPEN ⇄ UNDER_REVIEW
Epistemic (derived from ContradictionDisposition): EXPLAINED | NO_LONGER_APPLICABLE | WITHDRAWN | UNRESOLVED | SUPERSEDED
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → OPEN | Human (AI suggestion deferred) | ≥2 distinct same-case unretracted members; type + scope definition + incompatibility basis; adjudicative-language guard | contradiction-created |
| OPEN ⇄ UNDER_REVIEW | **Human only** | No disposition exists (operational stewardship; implies nothing about strength or proof) | contradiction-review-started / -paused |
| open/under-review → any disposition | **Human only** | ContradictionDisposition with outcome + rationale; optional informing provenance refs; **no outcome implies a member was proven correct** | contradiction-disposed (outcome in detail) |

All dispositions terminal; recurrence or re-scoping = new Contradiction (`SUPERSEDED` links it). Disposition never retracts, modifies, or promotes any member. Member retraction degrades derived `contradiction_health` (CURRENT → DEGRADED) and is surfaced — never auto-disposed (Article II).

## 8. ContradictionMember (CI)

No lifecycle. Created with (or added to) its Contradiction; never removed, retargeted, or deleted. Erroneous membership is handled by withdrawing/superseding the Contradiction, preserving the historical fact that the claims were held incompatible.

## 9. Unknown (V question text; operational state CT; terminal disposition via UnknownResolution)

Two independent state families (AGC Session 008, Amendment 1 — operational activity is not epistemic resolution):

```
Operational (CT, human-only, reversible):   OPEN ⇄ UNDER_REVIEW
Epistemic (derived from UnknownResolution): ANSWERED | PARTIALLY_ANSWERED | UNRESOLVABLE | WITHDRAWN
```

`UNDER_REVIEW` records only that a Steward is actively evaluating the Unknown — it carries no conclusion. Epistemic status is derived from the resolution record; a bare epistemic flip without an UnknownResolution is impossible.

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → OPEN | Human (AI suggestion deferred) | Question stated as a question (guard: interrogative form, no task vocabulary) | unknown-created |
| OPEN → UNDER_REVIEW | **Human only** | — (operational marker) | unknown-review-started |
| UNDER_REVIEW → OPEN | **Human only** | — (review paused; nothing concluded) | unknown-review-paused |
| open/under-review → ANSWERED | **Human only** | `ANSWERED` UnknownResolution with ≥1 answering claim reference | unknown-resolved |
| open/under-review → PARTIALLY_ANSWERED | **Human only** | `PARTIALLY_ANSWERED` UnknownResolution with ≥1 claim reference; the remaining gap is re-stated as a **new** Unknown referencing this one | unknown-partially-resolved |
| open/under-review → WITHDRAWN | **Human only** | `WITHDRAWN` UnknownResolution with rationale | unknown-withdrawn |
| open/under-review → UNRESOLVABLE | **Human only** | `UNRESOLVABLE` UnknownResolution with rationale | unknown-marked-unresolvable |

All dispositions terminal; a reopened question is a new Unknown referencing the old. Resolving an Unknown alters **no** linked record — knowing more ≠ changing meaning; linked Interpretations change only through explicit human reconsideration (ONT-PRN-020).

## 10. UnknownLink (V)

```
ACTIVE → RETRACTED
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → ACTIVE | Human or AI (part of suggestion) | Target in same Case; nature of dependency recorded | unknown-linked |
| ACTIVE → RETRACTED | Human | Reason | unknown-unlinked |

## 11. UnknownResolution (CI)

No lifecycle after creation (Human only). A mistaken resolution is superseded by a successor resolution created by a Human, which reopens the question as a **new** Unknown referencing the old. Audit events: resolution-created; resolution-superseded.

## 12. Entity (V; designation CT)

```
ACTIVE → RETRACTED (superseded_by = surviving duplicate, where applicable)
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → ACTIVE | Human or AI (proposal) | Entity class assigned | entity-created |
| ACTIVE → RETRACTED | Human | Reason; surviving duplicate linked for merges | entity-retracted |
| designation changed | Human | New working designation (non-evidentiary) | entity-designation-changed |

No system- or AI-side merge exists; identity determination is human (Ontology §4).

## 13. Relationship (V)

```
ACTIVE → RETRACTED        (review status orthogonal)
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → ACTIVE | Human or AI (proposal) | Both endpoints in Case; ≥1 grounding claim; uncertainty expressed | relationship-created |
| ACTIVE → RETRACTED | Human | Reason | relationship-retracted |
| (flag) grounding-degraded | System (detection) | Supporting claim retracted/degraded | grounding-flag-raised |

## 14. AuditEntry (CI — strongest guarantee in the system)

No lifecycle. Created only by the system as an atomic side effect of actor-attributed operations; never updated, deleted, retracted, or superseded — by anyone, including administrators, at every layer. A wrong entry is corrected by a subsequent compensating entry that references it.

## 15. HypothesisAlternative (CI)

No lifecycle. Created by a Human — with the second Hypothesis (same transaction) or later via the dedicated `link_hypothesis_alternative` operation (Session 012 Amendment 4) — and never removed, retargeted, or deleted. Unordered, symmetric, normalized by identifier, same-case, non-ranking. **Preserved after either Hypothesis is retracted**: a retracted alternative never silently vanishes from history; `current_alternative_state` is derived while the original link is preserved. Audit event: hypothesis-alternative-linked. Modifies neither Hypothesis.

## 16. ContradictionLink (V)

```
ACTIVE → RETRACTED
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → ACTIVE | **Human only** | Contradiction and Hypothesis in same Case; relationship `CHALLENGED_BY_CONTRADICTION` (the only authorized value — no refutation relationship may ever be added); explanation recorded; hypothesis fingerprint v1 snapshot | contradiction-linked |
| ACTIVE → RETRACTED | Human | Reason (link errors only — never silent removal) | contradiction-unlinked |

A disposed Contradiction remains historically linked; disposition changes only the derived `contradiction_boundary_state`, never the link or the Hypothesis. Linking alters neither endpoint.

---

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft, extracted from Domain Schema Specification 0.1.0 per ADR-0009 document hierarchy. |
| 1.0.0 | 2026-07-13 | Ratified by AGC Review Session 001. |
| 2.0.0 | 2026-07-13 | EvidenceArtifact lifecycle made explicit per ADR-0007 / AGC Session 004: STAGED recognized as pre-constitutional; PENDING renamed PENDING_VERIFICATION; QUARANTINED introduced with human-only disposition; ONT-PRN-012 conventions added. MAJOR: 1.0.0 state names would mislead an implementer. |
| 2.1.0 | 2026-07-13 | Unknown §9: UNDER_REVIEW operational state (reversible, no conclusion) separated from derived epistemic disposition; PARTIALLY_ANSWERED added with the remaining-gap-as-new-Unknown rule (AGC Session 008, Amendment 1). |
| 2.2.0 | 2026-07-13 | Contradiction §7: operational/epistemic separation via ContradictionDisposition with the five non-adjudicating outcomes; incompatibility basis preconditions; derived contradiction_health (ADR-0027, AGC Session 010). |
| 2.3.0 | 2026-07-13 | Hypothesis creation preconditions per ONT-PRN-023 (human-only, four conditions, articulation requirements); derived three-state health noted as non-transitioning; HypothesisAlternative §15 (CI, survives retraction); ContradictionLink §16 (V, CHALLENGED_BY_CONTRADICTION only) — AGC Session 012. |
