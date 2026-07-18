# ADR-0031: Reconciliation never converts agreement into truth

- **Status:** Accepted (Founder Resolution 021, AGC Review Session 015 — freeze exemption per ONT-PRN-011: the governing constraint for Slice 1E, fixed before its gate)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), V (Evidence is immutable), IX (Certainty never exceeds evidence)
- **Supersedes:** none

## Context

Slice 1E introduces storage reconciliation. In ordinary data systems, reconciliation means *determine the correct version and converge everything toward it*. ARGUS cannot use that definition for epistemic records: convergence toward a "correct version" is adjudication smuggled into infrastructure. Session 015 fixed the ARGUS meaning before the slice gate: reconciliation **detects, surfaces, and accounts for divergence between stored representations without automatically deciding which representation is epistemically authoritative**.

## Decision

Founder Resolution 021 is recorded (stable identifier **ONT-PRN-026**):

> **Reconciliation may identify divergence between representations, but it must never convert representational agreement into evidentiary truth or representational disagreement into epistemic falsity.**

Normative consequences:

1. *Database hash matches object store* means **storage representations agree** — never *the evidence is authentic*. *Hash mismatch* means **representations diverge** — never *the evidence is false*.
2. Reconciliation outcomes are **integrity conditions, not truth conditions**: `MATCHED`, `MISSING`, `DIVERGENT`, `UNREADABLE`, `UNVERIFIED`. No state named `CORRECT`, `AUTHORITATIVE`, `TRUE_VERSION`, or `WINNER` may exist — unless "authoritative" is ever given a narrowly defined *custody* meaning completely separate from epistemic correctness, under its own governance review.
3. No reconciliation result changes any epistemic record, disposition, derived epistemic state, or admissibility. Integrity findings feed the existing surfacing machinery (flags, quarantine as a separate audited transition) — never epistemic conclusions.

## Governance review

1. **Constitutional Review** — PASS: Article IX applied to infrastructure — storage checks must not manufacture certainty about reality; Article I preserved — authenticity remains an evidentiary question, never a byte-comparison result.
2. **Domain Review** — PASS: extends the established separations (eligibility ≠ sufficiency, ONT-PRN-014; operational ≠ epistemic state) into the persistence layer.
3. **Architectural Review** — PASS: enforceable structurally (the condition enum is closed; contamination discipline covers reconciliation surfaces) and testable (classification matrix dual-rendered; no epistemic mutation paths exist to invoke).

## Consequences

- The Slice 1E gate must present the closed integrity-condition set and its classification matrix before code (ONT-PRN-024).
- Reconciliation reporting vocabulary joins the contamination discipline: truth/authenticity vocabulary is prohibited on its structured surfaces.

## Alternatives considered

- **Conventional converge-to-correct reconciliation** — rejected: selects a truth winner; adjudication is prohibited everywhere else in ARGUS and does not become acceptable by moving into infrastructure.
- **Treating verified hashes as authentication** — rejected: a matching digest proves representational agreement with the recorded digest, nothing about the provenance or authenticity of what was recorded (Article IX).

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

**Affected Articles:** I, V, IX (integrity kept distinct from truth at the persistence boundary). Others untouched.

**Compliant?** YES

**Explanation:** Keeps the storage layer honest about what it can know: bytes can agree or diverge; only evidence, reasoning, and human judgment can address truth.
