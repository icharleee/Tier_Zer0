# ARGUS Entity Lifecycles

- **Document version:** 2.0.0 — Ratified at 1.0.0 by AGC Review Session 001; 2.0.0 applies the explicit EvidenceArtifact lifecycle of ADR-0007 as amended by AGC Session 004 (state renames are MAJOR: a reader of 1.0.0 would implement the wrong states)
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
| create → ACTIVE | Human or AI (proposal) | Full provenance (C7); ladder references valid (C10): Observation ≥1 SourceLocator; Interpretation ≥1 Observation; Hypothesis ≥1 Interpretation | claim-created |
| ACTIVE → RETRACTED | Human | Reason; successor linked where applicable | claim-retracted |
| (flag) ungrounded / grounding-degraded | System (detection) | Every supporting reference retracted, or any reference degraded | grounding-flag-raised |

Flags are surfaced states, not transitions: a degraded claim awaits **human** disposition and is never auto-retracted (Article II). **Hypothesis has no `CONFIRMED`, `TRUE`, or any terminal success state** — conviction lives in human Understanding, outside the system.

## 7. Contradiction (V description; terminal disposition)

```
OPEN → RESOLVED
   └─→ WITHDRAWN
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → OPEN | Human or AI (suggestion) | ≥2 ContradictionMembers | contradiction-created |
| member added | Human or AI (suggestion) | Member claim in same Case | contradiction-member-added |
| OPEN → RESOLVED | **Human only** | Non-empty rationale; resolving-evidence references where resolution rests on evidence | contradiction-resolved |
| OPEN → WITHDRAWN | **Human only** | Non-empty rationale (raised in error) | contradiction-withdrawn |

Both terminal; recurrence = new Contradiction referencing the old. Resolution never retracts the conflicting claims. Retraction of a member raises a flag for human disposition — no auto-resolution.

## 8. ContradictionMember (CI)

No lifecycle. Created with (or added to) its Contradiction; never removed, retargeted, or deleted. Erroneous membership is handled by withdrawing/superseding the Contradiction, preserving the historical fact that the claims were held incompatible.

## 9. Unknown (V question text; terminal disposition via UnknownResolution)

```
OPEN → RESOLVED
   ├─→ WITHDRAWN
   └─→ UNRESOLVABLE
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → OPEN | Human or AI (suggestion) | Question stated as a question | unknown-created |
| OPEN → RESOLVED | **Human only** | Via `ANSWERED` UnknownResolution with ≥1 answering claim reference | unknown-resolved |
| OPEN → WITHDRAWN | **Human only** | Via `WITHDRAWN` UnknownResolution with rationale | unknown-withdrawn |
| OPEN → UNRESOLVABLE | **Human only** | Via `UNRESOLVABLE` UnknownResolution with rationale | unknown-marked-unresolvable |

Status is derived from the resolution record — a bare status flip without an UnknownResolution is impossible. All terminal; a reopened question is a new Unknown referencing the old.

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

---

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft, extracted from Domain Schema Specification 0.1.0 per ADR-0009 document hierarchy. |
| 1.0.0 | 2026-07-13 | Ratified by AGC Review Session 001. |
| 2.0.0 | 2026-07-13 | EvidenceArtifact lifecycle made explicit per ADR-0007 / AGC Session 004: STAGED recognized as pre-constitutional; PENDING renamed PENDING_VERIFICATION; QUARANTINED introduced with human-only disposition; ONT-PRN-012 conventions added. MAJOR: 1.0.0 state names would mislead an implementer. |
