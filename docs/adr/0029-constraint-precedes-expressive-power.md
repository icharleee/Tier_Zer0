# ADR-0029: No expressive power without prior constraint

- **Status:** Accepted (Founder Resolution 019, AGC Review Session 013 — freeze exemption per ONT-PRN-011: promoted from a candidate observation that survived the full implemented ladder)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity), IX (Certainty never exceeds evidence), III (Conclusions explain themselves)
- **Supersedes:** none (gives ODE Principle P1 concrete enforcement inside ARGUS)

## Context

Session 009 recorded a candidate observation: complex systems become trustworthy when every increase in expressive power is preceded by an increase in structural constraint. Its promotion condition — "elevate if the pattern holds through Slice 2D" — was met: Hypothesis, the most dangerous rung, was not introduced and constrained afterward. Its obligation floor (ONT-PRN-023, the Session 012 amendments, the Invariant Matrix rows) existed before its schema did. Session 013 promoted the generalized form to **ODE Principle P1** (ODE-0001 §6) and proposed this resolution as its ARGUS-side enforcement.

## Decision

Founder Resolution 019 is recorded (stable identifier **ONT-PRN-024**):

> **No new epistemic object or capability may be implemented until the ontology defines the constraints, refusal conditions, provenance obligations, validity boundaries, and non-effects that limit its expressive power.**

This extends the existing derivation discipline: *the ontology defines meaning; constraints define admissibility; implementation may then express only what both permit.*

Boundaries of the decision:

1. The resolution mandates **constraint-before-expression**, not positive/negative alternation. The alternating rhythm remains Observation O8 — an observed pattern, deliberately not constitutionalized (two cycles establish credibility, not necessity).
2. "Non-effects" are part of the constraint floor: what the new capability must **not** do (no automatic revision, no promotion, no adjudication) is defined with the same rigor as what it may do.
3. Whether ARGUS should bind all future ontology extensions to P1 *constitutionally* is deferred; this resolution binds implementation sequencing, which is already within the AGC's slice-gate authority (ADR-0015: rows before code — now generalized to constraints before expression).

## Governance review

1. **Constitutional Review** — PASS: Articles VII and IX applied to the development process itself — the system may not become more expressive than its constraints can refuse.
2. **Domain Review** — PASS: consistent with ONT-PRN-019 (obligations accumulate) and ONT-PRN-023; formalizes the practice every slice since 1D has followed.
3. **Architectural Review** — PASS: enforceable at the plan gate (a slice plan lacking the constraint floor is unapprovable); testable — each constraint lands as refusal codes, matrix rows, and negative-obligation tests before code.

## Consequences

- Slice 3A and every later slice must present its constraint floor — refusal conditions, provenance obligations, validity boundaries, and non-effects — at the plan gate, before implementation.
- A proposed capability whose constraints cannot yet be stated is not ready to exist, however useful it appears.

## Alternatives considered

- **Constitutionalize positive/negative alternation (O8) as well** — rejected by the session: two cycles do not prove all future epistemic architectures must alternate; the claim stays proportional to the evidence.
- **Leave the pattern as engineering habit** — rejected: habits decay; the resolution makes the discipline checkable at every gate.

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

**Affected Articles:** III, VII, IX (the development process bound by the same integrity discipline as the artifact). Others untouched.

**Compliant?** YES

**Explanation:** Makes it structurally impossible for ARGUS to gain a power before gaining the ability to limit, trace, and refuse that power.
