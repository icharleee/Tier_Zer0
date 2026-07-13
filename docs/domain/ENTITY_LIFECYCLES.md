# ARGUS Entity Lifecycles

- **Document version:** 1.0.0 — **Ratified** by AGC Review Session 001, 2026-07-13, as one package with the [Ontology](ONTOLOGY.md) and the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md)
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md); structural context in the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md)

This document is authoritative for entity states and permitted transitions. The Domain Schema Specification references it per entity; the [Invariant Matrix](INVARIANT_MATRIX.md) will specify the enforcing mechanism for each transition.

**Conventions.** Immutability classes CI/V/CT per Domain Schema Specification C5; retraction pattern per C6. Every transition below is a material mutation and emits an AuditEntry atomically (C9). "Human" = HumanActor, "AI" = AIWorkflow, "System" = SystemProcess (C1). The AI **review status** (`UNREVIEWED → ACCEPTED | REJECTED`, human-only, at most one transition, per C8) is orthogonal to lifecycle state and applies to every AI-created record; it is not repeated in each table.

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

```
PENDING → ACTIVE → RETRACTED
              └──→ SEALED ⇄ ACTIVE
```

| Transition | Actor | Preconditions | Audit event |
|---|---|---|---|
| create → PENDING | Human or System (attributing human authority) | Hash computed; acquisition description recorded | artifact-ingested |
| PENDING → ACTIVE | System (verification) | Integrity verification passed (protocol: ADR-0007, reserved) | artifact-activated |
| PENDING → (failed) | System | Verification failed; artifact never becomes visible to analysis | artifact-verification-failed |
| ACTIVE → RETRACTED | Human | Reason; superseding artifact linked where applicable | artifact-retracted |
| ACTIVE → SEALED | Human | Legal basis recorded | artifact-sealed |
| SEALED → ACTIVE | Human | Legal basis recorded | artifact-unsealed |

No SourceLocator may be created against a non-`ACTIVE` artifact. Every read of `SEALED` content emits an audit event.

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
