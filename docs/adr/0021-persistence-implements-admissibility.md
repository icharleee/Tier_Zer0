# ADR-0021: Persistence implements admissibility, not defines it

- **Status:** Accepted (Founder Resolution 012, AGC Review Session 006 — freeze exemption per ONT-PRN-011: the layering was discovered in Slice 1D's built shape)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), VII (Scientific integrity before convenience)
- **Supersedes:** none (refines the derivation chain semantics of ADR-0014/ADR-0018)

## Context

Slice 1D was planned as Ontology → Validator → Persistence and was built as Ontology → **Admissibility** → Persistence. The interesting thinking moved upward: validators became pure, creation became mechanical, database functions became small, tests became simple. Persistence became boring — which is what good architecture looks like. The layer immediately beneath ontology is not persistence; it is admissibility.

## Decision

Founder Resolution 012 is recorded (stable identifier **ONT-PRN-017**):

> **Persistence should implement admissibility, not define it.**
> The ontology determines what may exist, under what conditions, with what provenance. Persistence merely ensures those conditions cannot be bypassed.

Normative consequences:

1. Every future entity follows the Slice 1D shape: a pure admissibility surface (canonical codes, dual-rendered, triangulated) above a mechanical creation path. A `create_*` function that contains novel rules — rules absent from the validators and the normative matrix — is a defect.
2. Database enforcement (grants, functions, triggers) is the *bypass-proofing* of admissibility, never an independent source of admissibility rules; where the database must refuse something the validators don't express, the normative matrix is amended first.
3. ODE's derivation chain reads, refined: Ontology → Admissibility → Persistence → Verification. **ODE Observation O3** is registered: *separating admissibility from persistence reduced implementation complexity while increasing independent verifiability.*

## Governance review

1. **Constitutional Review** — PASS: Article I is served structurally (what may exist is decided at the epistemic layer, not by storage convenience).
2. **Domain Review** — PASS: no ontology content changes; the resolution names where its force is applied.
3. **Architectural Review** — PASS: reversible (a naming of layers); maintainable — it *removes* a failure mode (rules accreting inside SQL bodies); operationally realistic; understandable; reviewable ("does this create function contain a rule?" is a concrete question).

## Consequences

- Slice reviews gain a check: diff the `create_*` bodies against the validators; any rule found only in creation is a violation.
- Future storage changes (partitioning, providers, even databases) cannot move admissibility because admissibility never lived there.

## Alternatives considered

- **Leave the layering implicit** — rejected: implicit layers erode; the next engineer under deadline would put "one small check" in the create function.
- **Push all validation into the database** — rejected: inverts the authority relationship (ADR-0006 boundary 2; ONT-PRN-010) and makes the epistemic layer untestable without a server.

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

**Affected Articles:** I, VII (reinforced). Others untouched — a layering principle, no behavior change.

**Compliant?** YES

**Explanation:** Records where constitutional conditions are decided (the admissibility layer) versus protected (persistence). Nothing gains authority; a drift channel is closed.
