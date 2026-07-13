# ADR-0005: Unknowns and contradictions as first-class entities

- **Status:** Accepted
- **Date:** 2026-07-13
- **Constitutional articles:** II (Human judgment is final), IV (Alternatives remain possible), IX (Certainty never exceeds evidence)

## Context

Investigations fail quietly in two ways: missing information gets treated as settled ("nobody mentioned a second vehicle, so there wasn't one"), and conflicting evidence gets averaged away instead of confronted. Both failures are invisible when gaps and conflicts exist only as analyst intuition or UI decoration. ARGUS requires them to be durable objects that demand disposition.

## Decision

We will model missing information and evidentiary conflict as explicit, persistent entities:

- **`Unknown`** — a specific piece of missing information, stated as such. `UnknownLink` connects an Unknown to the records it affects (observations, interpretations, hypotheses, entities). `UnknownResolution` records how an Unknown was resolved — created only by an authenticated human, with provenance for whatever evidence resolved it.
- **`Contradiction`** — an explicit conflict between analytical records. `ContradictionMember` links each participating record. A Contradiction remains open until a human resolves it; resolution requires a recorded rationale and produces an `AuditEntry`.
- The AI may **suggest** Unknowns and Contradictions (as unreviewed proposals per ADR-0004). It may never resolve or close them (Article II) — this is enforced by authorization rules and schema constraints on the resolving actor, not convention.
- Neither entity is ever deleted; disposition follows the retraction pattern of ADR-0003.

## Consequences

- Gaps and conflicts are queryable case objects: "what don't we know?" and "what conflicts?" are first-class questions with first-class answers.
- Hypothesis review can require that a Hypothesis enumerate the open Unknowns and Contradictions it touches, keeping certainty calibrated to evidence (Article IX).
- More modeling and UI surface than an annotations approach; accepted cost.
- Analysts must triage suggested Unknowns/Contradictions, creating workload — the workload *is* the epistemic work the system exists to surface.

## Alternatives considered

- **Free-text notes/tags for gaps and conflicts** — rejected: not queryable, not linkable, silently ignorable; nothing demands disposition.
- **Deriving contradictions dynamically at read time** — rejected: derived conflicts have no identity, no history, and no human disposition trail; a conflict that disappears when a query changes violates "nothing disappears."
