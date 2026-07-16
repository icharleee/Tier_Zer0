# ADR-0028: An explanation must state what supports, limits, challenges, and escapes it

- **Status:** Accepted (Founder Resolution 018, AGC Review Session 011 — freeze exemption per ONT-PRN-011: the obligation floor for Hypothesis was fixed by the built lower rungs)
- **Date:** 2026-07-13
- **Constitutional articles:** III (Conclusions explain themselves), IV (Alternatives remain possible), VII (Scientific integrity), IX (Certainty never exceeds evidence)
- **Supersedes:** none (instantiates ONT-PRN-019's accumulation at the Hypothesis rung)

## Context

Hypothesis is the first object that attempts to *explain* reality, which creates risks absent at every lower rung: hidden preference among explanations, unfalsifiable narratives, unsupported expansion beyond grounded meaning, absence treated as support, contradiction treated as automatic refutation, confidence masquerading as evidence, and — later — AI-generated explanatory authority. The lower rungs were built first precisely so their constraints would be standing when explanation arrived.

## Decision

Founder Resolution 018 is recorded (stable identifier **ONT-PRN-023**), as the governing principle for the Hypothesis layer:

> **An explanation is constitutionally admissible only when the system can state what supports it, what limits it, what could challenge it, and what remains unknown.**

Normative consequences:

1. **Hypothesis ≠ conclusion.** The Domain Schema Specification states plainly (verbatim, at the Slice 2D gate): *a Hypothesis is a provisional, testable explanatory structure; its existence means only that it is admissible for examination — not that ARGUS considers it likely, preferred, correct, or accepted.*
2. **The four conditions are structural, not prose:** *supports* — existence relationships (`DERIVED_FROM` ≥1 grounded Interpretation; `CONTEXTUALIZED_BY` optional; never directly from raw EvidenceArtifacts or SourceLocators — rung-skipping prohibited); *limits* — validity boundaries (`LIMITED_BY_UNKNOWN`, `CHALLENGED_BY_CONTRADICTION`; **no `REFUTED_BY`** — a Contradiction challenges without killing); *challenge* — a mandatory `testability_statement` and `challenge_condition` (a declaration of what future evidence would matter, not a prediction); *unknown* — the inherited uncertainty envelope plus visible open boundaries.
3. **Prohibited permanently at this rung:** `probability`, `confidence_score`, `preferred`, `primary`, `leading`, `best_fit`, `winner`, `case_theory`, `accepted` — no such field, outcome, or constraint may be authorized (contamination registry enforced).
4. **Automatic revision prohibited:** resolving or disposing any boundary changes no Hypothesis; retracting or disposing one Hypothesis promotes no other. The governing rule: **ARGUS may preserve explanations for examination; it may never convert explanation into verdict.**

## Governance review

1. **Constitutional Review** — PASS: this is Articles III/IV/VII/IX composed into one admissibility spine for the most dangerous rung.
2. **Domain Review** — PASS: ONT-PRN-019 (obligations accumulate) and ONT-PRN-021 (existence vs. validity) applied as designed; the Lexicon's Hypothesis definition ("a testable explanatory model") is fulfilled, not altered.
3. **Architectural Review** — PASS: reversible before implementation; maintainable (the four conditions map to the established validator/dual-rendering pattern); testable — each condition is a refusal code.

## Consequences

- Slice 2D's validator floor is fixed before design begins: everything Interpretation refuses, plus the four conditions.
- The alternative-articulation mechanism (how Article IV is exercised at creation) is consequential and **deliberately left to the Slice 2D plan gate** rather than decided here.

## Alternatives considered

- **Free-form hypothesis text with review discipline** — rejected: persuasive narrative is exactly the failure mode; conditions must be structural.
- **Requiring two hypotheses to create one** — noted from the session as likely to encourage artificial alternatives; the explicit-absence mechanism is evaluated at the plan gate instead.

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

**Affected Articles:** III, IV, VII, IX (composed into the Hypothesis admissibility spine). Others untouched.

**Compliant?** YES

**Explanation:** Fixes the conditions under which explanation may exist, before any explanation exists. Its purpose is singular: to make it structurally impossible for ARGUS to hold an explanation it cannot account for.
