# ADR-0025: Existence relationships are distinct from validity-boundary relationships

- **Status:** Accepted (Founder Resolution 016, AGC Review Session 008 — freeze exemption per ONT-PRN-011: the orthogonality appeared in the built structure before it was named)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), IV (Alternatives remain possible), IX (Certainty must never exceed the evidence)
- **Supersedes:** none (extends ADR-0023's inheritance rules and ADR-0024's boundary objects)

## Context

Every ladder object now carries two independent relationship families. Interpretation is *grounded by* Observations (pointing downward — why it may exist) and *bounded by* Unknowns (pointing outward — what limits its validity). These are orthogonal: one justifies existence, the other constrains meaning. The symmetry repeats upward: Hypothesis will be derived from Interpretations and limited by Contradictions.

## Decision

Founder Resolution 016 is recorded (stable identifier **ONT-PRN-021**):

> **Every epistemic object shall explicitly distinguish the relationships that justify its existence from the relationships that limit its validity.**

As an inherited architectural rule (ONT-PRN-019 applies — it accumulates up the ladder):

| Object | Existence (justifies) | Validity (limits) |
|---|---|---|
| Observation | grounded by SourceLocators | — (bounded at the artifact/eligibility layer) |
| Interpretation | grounded by Observations | limited by Unknowns |
| Hypothesis (future) | derived from Interpretations | limited by Contradictions |

Normative consequences: the two families are never stored in one polymorphic relationship table, never share a junction, and never convert into each other (a validity boundary can never become grounds; a grounding can never become a limit). Removal of an existence relationship threatens admissibility; presence of a validity boundary threatens nothing — it *informs* (Article IX). **Unknown scope** is a derived classification of a boundary's reach — observational, interpretive, or (later) explanatory, computed from what an Unknown links to — derived, never stored (ONT-PRN-013 pattern); recorded in the ontology now, implementation deferred beyond v0.1.

## Governance review

1. **Constitutional Review** — PASS: Article I governs existence relationships; Articles IV/IX govern validity boundaries; separating them keeps each article's machinery clean.
2. **Domain Review** — PASS: names the orthogonality already ratified in ADR-0020 (grounding) and ADR-0024 (boundaries); no ladder change.
3. **Architectural Review** — PASS: reversible in naming only; maintainable — it *prevents* the polymorphic-junction refactor someone would eventually propose; testable (schema review: every epistemic junction declares which family it belongs to).

## Consequences

- Slice 2B's `unknown_links` is a validity-boundary table and may never gain grounding semantics; `interpretation_groundings` is an existence table and may never gain boundary semantics.
- Hypothesis arrives with its two families pre-specified.

## Alternatives considered

- **One generic "related_to" junction with a type column** — rejected: the type column would be the first step toward converting limits into support; the families differ in kind, not in label.

## Constitutional Checklist

- [x] Article I — Evidence before opinion
- [x] Article II — Human judgment is final
- [x] Article III — Every analytical conclusion must explain itself
- [x] Article IV — Alternative explanations must always remain possible
- [x] Article V — Evidence is immutable
- [x] Article VI — Privacy and legal authority must be respected
- [x] Article VII — Scientific integrity before convenience
- [x] Article VIII — Justice requires transparency
- [x] Article IX — Certainty must never exceed the evidence

**Affected Articles:** I, IV, IX (each gains a dedicated relationship family instead of sharing one). Others untouched.

**Compliant?** YES

**Explanation:** A classification of relationships that already exist, preventing their future conflation. Nothing new may exist or be limited because of this ADR; what exists and what limits are simply never allowed to trade places.
