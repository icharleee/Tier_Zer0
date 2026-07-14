# ADR-0017: Authoritative lifecycle definitions shall exist exactly once

- **Status:** Accepted (Founder Resolution 008, AGC Review Session 005 — freeze exemption per ONT-PRN-011: duplication discovered by implementation before it became drift)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience), VIII (Justice requires transparency)
- **Supersedes:** none

## Context

Slice 1B produced the first independent enforcement of constitutional rules: the same EvidenceArtifact lifecycle now exists in three hand-maintained renderings — the Entity Lifecycles document, the Python transition registry (`ALLOWED_ARTIFACT_TRANSITIONS`), and the PostgreSQL transition functions. Their agreement today is the product of care, not structure. Care does not survive five years, headcount growth, or deadlines. The duplication was identified *before* drift occurred — the correct moment to record its resolution.

## Decision

Founder Resolution 008 is recorded as a founding principle (stable identifier **ONT-PRN-013**):

> **Authoritative lifecycle definitions shall exist exactly once.**

The lifecycle shall not be handwritten in documentation, Python, and SQL. The target architecture:

```
Ontology
    ↓
Lifecycle Specification        (single machine-readable source)
    ↓
Generated Python registry
Generated PostgreSQL transition table
Generated diagrams
Generated tests
```

**This is a long-term architectural direction, not a Slice 1 task.** It is recorded now so the target is fixed while the duplication is still synchronized.

**Interim obligations (binding until generation exists):**

1. The Entity Lifecycles document remains the single *authoritative* rendering (ONT-PRN-008); Python and SQL are derived renderings that must cite it.
2. A **conformance test** MUST prove, against real PostgreSQL, that the Python registry and the SQL functions accept and reject the same transition set (every wrapper × every predecessor state × every actor class). Divergence is a release-blocking constitutional failure, not a bug.
3. Any change to the lifecycle touches all three renderings *and* the conformance test in the same change set.

## Governance review

1. **Constitutional Review** — No violation; the decision protects Articles VII and VIII by making rule-agreement structural rather than diligent. **PASS.**
2. **Domain Review** — No ontology content changes; the ladder untouched; the Lifecycle Specification will be a derivation-layer artifact under the existing chain (Ontology → Derivation Specification → …). **PASS.**
3. **Architectural Review** — Reversible (generation can be abandoned; the renderings remain valid); maintainable (it removes triple maintenance); operationally realistic because it is explicitly deferred — only the conformance test is a present-day obligation; understandable; testable (the conformance test *is* the test). **PASS.**

## Consequences

- The next slice that touches lifecycle definitions must budget for the conformance suite (the first instance ships with this ADR's enactment).
- A future Lifecycle Specification format (and its generator) requires its own engineering-design ADR before adoption.
- Until generation exists, lifecycle changes carry a documented four-place checklist (document, Python, SQL, conformance test) — friction accepted deliberately.

## Alternatives considered

- **Accept triplication with review discipline** — rejected: this is governance by convention, which ADR-0002 already rejected as an enforcement mechanism; conventions fail exactly when pressure is highest.
- **Generate now, in Slice 1** — rejected: premature; one entity's lifecycle is not enough signal to design the specification format, and the freeze prioritizes constitutional capability over tooling.
- **Make Python or SQL the single source** — rejected: implementation artifacts may not define meaning (ONT-PRN-010); the source must sit in the derivation chain above both.

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

**Affected Articles:** VII, VIII (reinforced: reproducible, single-sourced rules; drift becomes structurally detectable). Others untouched — a process/architecture decision with no effect on evidence handling or judgment boundaries.

**Compliant?** YES

**Explanation:** The resolution constrains how lifecycle rules are *authored and propagated*, not what they say. Its constitutional effect is protective: three renderings that quietly diverge would eventually enforce three different constitutions; this ADR makes that failure mode structurally impossible in the target state and mechanically detectable in the interim.
