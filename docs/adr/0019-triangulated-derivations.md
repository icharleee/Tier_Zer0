# ADR-0019: Independent derivations should be triangulated whenever practical

- **Status:** Accepted (Founder Resolution 010, AGC Review Session 007 / Slice 1C review — freeze exemption per ONT-PRN-011: the pattern was discovered working in Slice 1C's test design before it was named)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience), VIII (Justice requires transparency)
- **Supersedes:** none (extends the verification doctrine of ADR-0010)

## Context

Slice 1C's conformance suite did something unplanned but important: the test file transcribed the canonical eligibility matrix as its own literal, making it a **third** independent derivation — alongside the Python predicate and the PostgreSQL function — with none of the three deriving from another executable artifact. Dual implementations can agree by sharing a mistake; a shared mistake across three independent derivations of one normative source is far less likely. The Architecture Review named the pattern: this is not dual implementation, it is **triangulation**.

## Decision

Founder Resolution 010 is recorded as a founding principle (stable identifier **ONT-PRN-015**):

> **Independent derivations should be triangulated whenever practical.**
> Critical constitutional behavior should ideally exist in three independent forms: (1) a normative specification, (2) an executable implementation, (3) independent verification. No implementation should be verified only against itself.

Normative consequences:

1. **The three legs derive from the ontology, never from each other.** A test that reads the implementation's tables, constants, or registries to build its expectations has collapsed into leg 2 and no longer verifies anything (the sole exception: transition-authority predicates deliberately reuse the registry per ONT-PRN-013 — there, the *conformance sweep against PostgreSQL* is the independent leg).
2. **"Whenever practical" is a real qualifier.** Triangulation is mandatory for constitutional behavior (transitions, predicates, provenance rules, audit semantics); ordinary plumbing needs ordinary tests. The slice plan states which behaviors get triangulated.
3. Where a normative artifact is machine-readable (the canonical matrix; a future Lifecycle Specification per ADR-0017), the verification leg SHOULD eventually be *generated from it* — making triangulation cheaper as the generation program matures.

**ODE Observation O2 is registered** in the research corpus: *independent verification derived directly from the ontology detected implementation divergence without sharing executable logic* (the H2 sweep caught the PostgreSQL array-literal parsing defect precisely because its expectations came from the transcribed matrix, not from the function under test).

## Governance review

1. **Constitutional Review** — No violation; Article VII strengthened (verification becomes evidence about the implementation rather than a restatement of it). **PASS.**
2. **Domain Review** — No ontology content changes; the principle governs how derivations are checked, not what they mean. **PASS.**
3. **Architectural Review** — Reversible (a superseding ADR can relax the requirement); maintainable (the third leg already exists in the current suites; the rule prevents its silent decay); operationally realistic via the "whenever practical" qualifier; understandable; testable in review ("where did this test's expectations come from?" is a concrete question). **PASS.**

## Consequences

- Slice plans now declare their triangulated behaviors; reviews check the independence of the three legs.
- Test-writing discipline changes: expectations are transcribed from normative artifacts, never imported from implementation modules (importing reason-code *constants* is acceptable — they are the normative registry's rendering — importing decision *logic* is not).
- Slight duplication of normative content into tests is accepted as the cost of independence; ADR-0017's generation direction will eventually reclaim it.

## Alternatives considered

- **Dual implementation with mutual conformance only** — rejected: two derivations that share a misreading of the specification agree and pass; the third leg exists precisely to catch shared mistakes.
- **Mandatory triangulation for everything** — rejected: gold-plating plumbing dilutes the discipline where it matters; the qualifier keeps the cost proportional to constitutional weight.

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

**Affected Articles:** VII, VIII (reinforced: verification with independent evidentiary value; agreement between implementations becomes auditable rather than assumed). Others untouched.

**Compliant?** YES

**Explanation:** A verification-methodology principle. It changes no runtime behavior; it ensures that when ARGUS claims its implementations agree with its constitution, that claim rests on three independent witnesses rather than one artifact checking itself.
