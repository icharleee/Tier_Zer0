# ADR-0010: Verification derives from the ontology

- **Status:** Accepted (Founder Resolution 004, AGC Review Session 001)
- **Date:** 2026-07-13
- **Constitutional articles:** III (Conclusions explain themselves), VII (Scientific integrity before convenience)
- **Supersedes:** none

## Context

AGC Review Session 001's Architectural Review passed the ratified domain bundle with one directive: the derivation chain (Ontology → Domain Schema → Implementation) is missing its last rung — Verification. In conventional practice, tests derive from implementation: the code is written, then tests are written to match what the code does. That makes tests self-confirming — a bug in the implementation becomes a bug in the expectation, and the suite proves conformance to itself.

## Decision

Founder Resolution 004 is recorded as a founding principle:

> **Verification is derived from ontology.**
> Every automated test should ultimately answer one question: *"Which ontological rule is this test protecting?"*

The full derivation chain becomes:

```
Reality → Ontology → Domain Schema → Implementation → Verification → Operation
```

Normative requirements:

1. **Tests derive from the ontology, not from implementation.** Expected behavior in a domain test is justified by an ontological rule, never by "what the code currently does."
2. **Every domain-protecting test declares its rule** by stable ontology identifier (per ADR-0011) in its docstring or marker — e.g., `test_observation_requires_source_locator` documents `ONT-OBS-001 / ONT-PRN-004: an Observation is grounded only through SourceLocators`.
3. **A test that cannot name its rule** is one of two things: infrastructure plumbing (exempt — it protects machinery, not meaning), or evidence of an undocumented rule. In the second case, the ontology is amended *first* (AGC review, version bump), and the test cites the new rule — the test suite is never allowed to be the only place a rule exists.
4. **Constitutional tests** (Constitution, Enforcement §3) trace: test → Invariant Matrix row → ontology identifier → constitutional article. The Invariant Matrix's "Verifying test" column closes this loop.

This completes what the session named **Ontology-Driven Engineering (ODE)**: a methodology in which the ontology defines meaning, the schema defines structure, implementation realizes behavior, and verification proves conformance. ODE is registered as planned research paper ISS-0005.

## Governance review

1. **Constitutional Review** — No violation. The decision strengthens Article VII (tests become reproducible statements of *why* behavior is expected) and Article III applied to the engineering process itself: every test explains itself. **PASS.**
2. **Domain Review** — The ontology is untouched in content and elevated in authority: it now governs verification as well as structure. The ladder is unaffected. **PASS.**
3. **Architectural Review** — Reversible (a superseding ADR can drop the annotation requirement; the tests remain valid). Maintainable (one docstring line per test). Operationally realistic (enforceable by review and, later, a lint that checks domain tests for ONT references). Understandable and testable by construction. **PASS.**

## Consequences

- Test intent becomes auditable: a reviewer — or a defense expert — can walk from any test to the rule it protects to the constitutional article behind it.
- Writing a domain test now sometimes requires amending the ontology first; this is friction exactly where friction is wanted (undocumented rules are the defect, not the annotation).
- Infrastructure tests need a recognized exemption so the rule stays meaningful rather than ritually applied.
- The Invariant Matrix gains its final column semantics: every row terminates in a verifying test that names its ontology ID.

## Alternatives considered

- **Tests derive from requirements documents** — rejected: requirements drift and get deleted; the ontology is versioned, governed, and permanent.
- **Traceability via external test-management tooling** — rejected: the trace must live with the code it governs and survive tool migrations (same reasoning as ADR-0001's rejection of external wikis).
- **No formal derivation for tests** — rejected: it leaves verification anchored to implementation, which is the self-confirming loop this decision exists to break.

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

**Affected Articles:** III, VII (both reinforced — self-explaining verification, reproducible scientific rigor in the test suite). Others untouched: this is a process decision with no effect on evidence handling, judgment boundaries, or uncertainty representation.

**Compliant?** YES

**Explanation:** The decision adds a derivation obligation to tests and changes no runtime behavior. Its constitutional effect is purely reinforcing: verification becomes explainable (III) and anchored to governed meaning rather than to implementation accidents (VII).
