# ADR-0023: The ladder accumulates obligations

- **Status:** Accepted (Founder Resolution 014, AGC Review Session 007 — freeze exemption per ONT-PRN-011: pattern observed across the built rungs)
- **Date:** 2026-07-13
- **Constitutional articles:** I, III, IX (each rung's inherited guarantees)
- **Supersedes:** none

## Context

Each epistemic rung built so far carries everything beneath it and adds more. Observation: admissible, grounded. Interpretation: admissible, grounded, *and* uncertain (reasoning + envelope). The ladder is not only gaining entities — it is gaining obligations, monotonically.

## Decision

Founder Resolution 014 is recorded (stable identifier **ONT-PRN-019**):

> **Higher epistemic layers may introduce new obligations but may never weaken the obligations inherited from lower layers.**

Interpretation inherits provenance, grounding, admissibility — then adds reasoning and uncertainty. Hypothesis will inherit all of that and add falsifiability. Unknown and Contradiction inherit provenance and human-only disposition. Nothing disappears; the ladder only accumulates.

**Enforcement:** every new rung's admissibility validator MUST include (not re-implement — *include*, by composition or inherited checks) the constraints of the rung below; the slice review diffs the new refusal-code set against the inherited one, and any inherited code missing from the new layer's reachable refusals is a defect. The Derivation Specification's per-object obligations are read cumulatively down the ladder.

## Governance review

1. **Constitutional Review** — PASS: makes Articles I/III/IX guarantees monotone up the ladder.
2. **Domain Review** — PASS: names an existing property of the ratified rungs; no content change.
3. **Architectural Review** — PASS: reversible (a principle), maintainable (validators already compose — Interpretation calls `is_observation_grounded`), reviewable via refusal-code diff.

## Consequences

- Hypothesis's future validator has a floor fixed in advance: everything Interpretation refuses, plus falsifiability.
- "Simplifying" a higher layer by dropping an inherited check is structurally recognizable as a constitutional regression, not a refactor.

## Alternatives considered

- **Per-layer independent obligation sets** — rejected: permits exactly the silent weakening this resolution forbids.

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

**Affected Articles:** I, III, IX (their guarantees become monotone across rungs). Others untouched.

**Compliant?** YES

**Explanation:** A monotonicity rule over existing obligations. It grants nothing new to any layer; it forbids future layers from quietly owing less than their foundations.
