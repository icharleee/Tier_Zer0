# ADR-0022: Epistemic layers reject semantic contamination from higher layers

- **Status:** Accepted (Founder Resolution 013, AGC Review Session 006 — freeze exemption per ONT-PRN-011: generalizes a protection Slice 1D built for one entity)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), IV (Alternatives remain possible), IX (Certainty must never exceed the evidence)
- **Supersedes:** none (mechanizes ONT-PRN-004's one-rung doctrine at the schema-vocabulary level)

## Context

Slice 1D shipped a test asserting the Observation table carries no meaning, inference, confidence, or ranking columns. The Standards Review generalized it: the ladder's separations (ADR-0002) can be *mechanically* enforced by forbidding each epistemic layer the vocabulary of the layers above it. A system is defined not only by what it can do but by what it is structurally incapable of becoming without deliberate constitutional change — **the exclusions are load-bearing, and executable**, is hereby standing engineering doctrine.

## Decision

Founder Resolution 013 is recorded (stable identifier **ONT-PRN-018**):

> **Epistemic layers shall reject semantic contamination from higher layers.**

1. A **semantic contamination registry** is established as a normative artifact (Derivation Specification, cross-cutting section D-PRN-018): for each epistemic layer, the forbidden vocabulary of higher layers. Initially — **Observation** may not contain: confidence, inference, probability, interpretation, hypothesis, ranking, suspicion, intent, meaning, likelihood, prediction, score. **Interpretation** (when it arrives) may not contain: hypothesis, likelihood, prediction, verdict, guilt. The registry grows one layer ahead of implementation.
2. A **contamination test** walks every epistemic table's columns against the registry and is release-blocking. Its expectations are transcribed from the registry (triangulation leg 3, ONT-PRN-015), not imported from implementation constants.
3. Vocabulary is a heuristic, not the whole defense: reviews still judge *semantics* (a column named `note` holding verdicts contaminates without tripping the scan). The test catches the accidental; the review catches the deliberate.
4. Adding a forbidden stem is a MINOR registry change; *removing* one is a semantic weakening requiring AGC review.

## Governance review

1. **Constitutional Review** — PASS: mechanizes the never-collapse doctrine (Articles I, IV, IX) at the cheapest possible layer.
2. **Domain Review** — PASS: the ladder itself is untouched; its boundaries gain a tripwire.
3. **Architectural Review** — PASS: reversible, near-zero maintenance, trivially understandable, testable by construction.

## Consequences

- Interpretation cannot leak downward into Observation, and later Hypothesis cannot leak into Interpretation, without a red build naming the column.
- Schema evolution acquires a vocabulary review step; false positives (a legitimate column tripping a stem) are resolved by renaming or by AGC-reviewed registry exception, never by weakening the test silently.

## Alternatives considered

- **Review-only enforcement** — rejected: conventions fail under deadline (the recurring lesson of ADR-0002/0017).
- **Type-system enforcement only** — insufficient alone: columns are named by humans; names are where contamination first appears.

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

**Affected Articles:** I, IV, IX (reinforced — the ladder's separations become mechanically detectable). Others untouched.

**Compliant?** YES

**Explanation:** A structural tripwire for the ontology's oldest rule: never collapse the layers. It forbids nothing new; it makes an existing prohibition impossible to violate accidentally.
