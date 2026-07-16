# ADR-0026: Epistemic layers expand dimensions, not merely object counts

- **Status:** Accepted (Founder Resolution 017, AGC Review Session 009 — freeze exemption per ONT-PRN-011: the trajectory was observed across six built slices)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience), IX (Certainty must never exceed the evidence)
- **Supersedes:** none

## Context

Reviewing the built slices as a sequence: 1A represented *objects*, 1B *change*, 1C *permission*, 1D *claims*, 2A *meaning*, 2B *limits*. The architecture stopped adding entities some time ago — it has been adding **dimensions of representation**. Adding a table is easy; adding a dimension changes the expressive power of the entire ontology. Unknown did exactly that: it made ignorance representable, not just more things.

## Decision

Founder Resolution 017 is recorded (stable identifier **ONT-PRN-022**):

> **Every new epistemic layer should expand the dimensions through which reality may be represented rather than merely increasing the number of representable objects.**

Normative consequences:

1. A slice plan for a new epistemic layer states *which dimension* it adds (what becomes representable that was not), not merely which tables it creates. A proposed entity that adds no representational dimension is presumptively workflow or infrastructure, not ontology — and is routed accordingly.
2. **The boundary taxonomy is normative** (recorded in the Ontology §3): boundary objects constrain reasoning; they never rewrite it. The "Alters automatically?" column is permanently `Never` — a boundary object that mutated what it bounds would be adjudication, which belongs to humans (Article II).
3. The emerging ODE pattern — *every increase in expressive power is preceded by an increase in structural constraint* (provenance before Observation; grounding before Interpretation; admissibility before Unknown; Unknown and Contradiction before Hypothesis) — is recorded as a **candidate principle**, to be elevated only if it repeats through Slice 2D.

## Governance review

1. **Constitutional Review** — PASS: Article IX generalized — expressive power gated behind constraint is certainty gated behind evidence, applied to the architecture itself.
2. **Domain Review** — PASS: no ontology content changes; a criterion for future layers.
3. **Architectural Review** — PASS: reversible (a review criterion); maintainable (one question per slice plan); testable in review ("what dimension does this add?" has a checkable answer).

## Consequences

- Slice 2C must answer the dimension question explicitly (it does: joint incompatibility — that admissible structures cannot all be simultaneously true — becomes representable).
- Entity proposals without a dimension face a higher bar, which is the point.

## Alternatives considered

- **Counting entities as progress** — rejected: it is how ontologies bloat into schemas.

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

**Affected Articles:** VII, IX (reinforced at the meta-level); II (the never-alters column). Others untouched.

**Compliant?** YES

**Explanation:** A criterion for how the ontology grows, plus the permanent record that boundaries constrain and never rewrite. It authorizes nothing and prevents dimension-free accretion.
