# ODE-0001: Ontology-Driven Engineering — Axioms and Method

- **Document version:** 0.1.0 (Draft)
- **Program:** Ontology-Driven Engineering (ODE)
- **Date:** 2026-07-13
- **Origin:** Named by AGC Review Session 001 (ADR-0010); axioms established by AGC Review Session 002; first implementation: ARGUS

## Abstract

Ontology-Driven Engineering (ODE) is a software engineering methodology in which the ontology defines meaning, the schema defines structure, implementation realizes behavior, and verification proves conformance. This paper states its five axioms, the derivation chain they generate, and the conditions under which the methodology applies. ODE emerged from the construction of ARGUS but is independent of it: any domain where the cost of meaning-drift is high — medicine, aviation, intelligence, finance, scientific research — is a candidate.

## 1. Two research programs

This paper marks the separation of two questions that were briefly entangled:

- **Investigation Systems Science (ISS)** asks: *how do investigations work?* It is domain science — theory about evidence, fragmentation, and epistemic integrity.
- **Ontology-Driven Engineering (ODE)** asks: *how should complex systems be engineered?* It is methodology — theory about how meaning, structure, behavior, and proof should relate in any engineered system.

The programs are related (ARGUS applies ODE to the ISS domain) but independent: neither depends on the other's results.

## 2. The five axioms

**Axiom I — Reality precedes representation.**
The system models a reality it did not create and cannot fully capture. Every artifact in the system is a representation, and no representation may be mistaken for the thing it represents. (In ARGUS: ONT-PRN-001.)

**Axiom II — Ontology defines meaning.**
There is exactly one source of truth for what the system's concepts mean, and it is a governed, versioned ontology — not a database, an API, or the accumulated habits of the codebase. Meaning changes are made in the ontology first and propagate downward, never the reverse. (In ARGUS: ONT-PRN-008, Founder Resolution 003.)

**Axiom III — Structure derives from ontology.**
Schemas, data models, and contracts are translations of ontological rules into structure. The translation itself is a recorded artifact (a derivation specification), so that "derives from" is a checkable claim, not a slogan.

**Axiom IV — Behavior implements structure.**
Code realizes the derived structure. Implementation artifacts are permanently replaceable and carry no independent authority; an implementation that disagrees with the ontology is defective by definition. (In ARGUS: ONT-PRN-010, Founder Resolution 005.)

**Axiom V — Verification proves conformance.**
Tests derive from the ontology, not from the implementation, and each declares which ontological rule it protects. Verification therefore proves conformance to meaning — not conformance of the code to itself. (In ARGUS: ONT-PRN-009, Founder Resolution 004.)

That is the methodology. Everything else is implementation.

## 3. The derivation chain

The axioms generate a one-directional chain:

```
Reality
  → Ontology                  (meaning; Axioms I–II)
  → Derivation Specification  (translation; Axiom III)
  → Schema                    (structure; Axiom III)
  → Implementation            (behavior; Axiom IV)
  → Verification              (proof; Axiom V)
  → Operation
```

Two properties distinguish ODE from requirements-driven and model-driven predecessors:

1. **Immutable referents.** Ontological concepts carry stable identifiers, so every downstream artifact — a schema constraint, a failing test, an audit finding — can cite the exact rule it serves, across decades and rewrites.
2. **A recorded translation layer.** The step from meaning to structure is itself a governed document, making derivation auditable rather than tribal.

## 4. When ODE applies

ODE's overhead is justified when meaning-drift is expensive: systems whose outputs carry legal, medical, safety, or scientific weight; systems intended to outlive their first implementation; systems built by many hands over long periods. It is unjustified for exploratory prototypes and short-lived tools, where the ontology would outweigh the product.

## 5. Hypotheses and first empirical results

ODE began as theory; ARGUS Slice 1B provides its first data. Recorded per AGC Review Session 005 — carefully, as evidence, not proof:

> **Hypothesis H1:** Independent implementations derived from a common ontology can converge on identical constitutional behavior without sharing implementation code.

Slice 1B is the first experimental data point: the Python domain layer and the PostgreSQL persistence boundary independently enforce the same constitutional rules — the same transition registry, the same actor constraints, the same audit obligations — derived separately from Entity Lifecycles 2.0.0, with a conformance suite proving behavioral agreement. One experiment is not proof. It is evidence.

**Status: Supported (n = 1).** We do not claim ODE is correct; we record that the experiment has not falsified it.

> **Hypothesis H2:** Behavior derived independently from a common ontology can converge across implementations without shared executable logic.

Slice 1B tested rule *transitions*; Slice 1C tests derived *behavior* — constitutional predicates (permission questions computed from constitutional state) rendered independently in Python and PostgreSQL against a canonical decision matrix. Different experiment, same methodology. H2 is a stronger claim than H1: not merely that implementations enforce the same rules, but that they independently arrive at the same *decisions*. It also suggests ODE may eventually distinguish structural derivation, behavioral derivation, and verification derivation.

**Status: Supported (n = 1)** — Slice 1C's conformance sweep: 16/16 canonical-matrix rows derived identically (structural verdict, contextual verdict, reason codes) by two renderings sharing no executable logic.

> **Hypothesis H3 (refined per AGC Session 008):** Independent implementations of epistemic admissibility converge when derived from a shared ontology and provenance model.

Registered ahead of Slice 1D, which introduces the first **epistemic object** — an Observation is the first entity that makes a claim about reality. The refinement matters: Observation creation is about *admissibility* ("this claim is constitutionally allowed to exist"), not reasoning — reasoning begins at Interpretation. The experimental surface is the validator pair (Python and PostgreSQL renderings of the admissibility rules), testing SourceLocator grounding, provenance enforcement, eligibility enforcement, and audit emission as epistemic behaviors.

**Status: Supported (n = 1)** — Slice 1D: the canonical refusal matrix (ten scenarios) derived identically by both validators, zero divergences; verdict confirmed by AGC Session 006.

> **Observation O3:** Separating admissibility from persistence reduced implementation complexity while increasing independent verifiability — validators became pure, creation became mechanical, database functions became smaller, tests became simpler (Resolution 012 / ONT-PRN-017: persistence implements admissibility, not defines it).

> **Hypothesis H4 (refined at the Slice 2A plan review, for falsifiability):** Independent implementations can preserve multiple admissible Interpretations over the same grounded Observations without assigning epistemic priority, comparative strength, or preferred status to any Interpretation.

The refinement distinguishes *technical ordering* (creation order, citation identifiers, indexes — unavoidable and non-evidentiary) from *epistemic preference* (ranking fields, preferred constraints, promotion on retraction, asymmetric exposure — forbidden). Article IV is not about having an interpretation but about protecting alternatives; the experiment requires at least two admissible interpretations of the same grounded observations, exposed symmetrically. The prior experiments each tested a different derivation category — transitions (H1), predicates (H2), admissibility (H3) — and H4 adds preservation of plurality. **Status: Untested.**

> **Observation O2:** Independent verification derived directly from the ontology detected implementation divergence without sharing executable logic.

In Slice 1C, the test suite transcribed the canonical matrix as its own literal — a third derivation, independent of both implementations (**triangulation**, formalized as Resolution 010 / ONT-PRN-015: normative specification, executable implementation, independent verification; no implementation verified only against itself). The H2 sweep caught a real PostgreSQL parsing defect (`array || 'literal'` read as an array literal) precisely because its expectations came from the transcribed matrix rather than from the function under test.

> **Observation O1:** During the implementation of Slice 1B, multiple architectural refinements emerged from executable constraints rather than design discussion — a real PostgreSQL syntax error caught by the live database, a lock-order inconsistency exposed by concurrency design, and a three-way lifecycle duplication identified before drift (leading to Resolution 008) — supporting the hypothesis that implementation is an effective source of ontology validation when governed by a one-directional derivation chain.

## 6. Open questions

- How does an ODE system evolve its ontology under live load — what is the migration discipline when meaning (not just structure) changes?
- What tooling makes derivation checkable mechanically (ontology-to-schema linting, test-annotation verification)?
- Can derivation specifications be partially generated, and where must human translation judgment remain?
- What does ODE conformance certification look like for a third party auditing a system's claim to be ontology-driven?

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft: program separation, the five axioms (AGC Session 002), derivation chain, applicability, open questions. |
| 0.2.0 | 2026-07-13 | Added Hypothesis H1 and Observation O1 with Slice 1B as the first experimental data point (AGC Review Session 005). |
| 0.3.0 | 2026-07-13 | Registered Hypothesis H2 (behavioral convergence via constitutional predicates), Slice 1C as its first experiment (Slice 1C plan review / ADR-0018). |
| 0.4.0 | 2026-07-13 | H1 and H2 marked Supported (n = 1 each); Observation O2 (triangulated verification detects divergence) and Hypothesis H3 (epistemic-constraint convergence, untested) registered per AGC Review Session 007 / ADR-0019. |
| 0.5.0 | 2026-07-13 | H3 refined to epistemic admissibility (AGC Session 008 / ADR-0020): the experiment targets the validator pair, not insertion. |
| 0.6.0 | 2026-07-13 | H3 marked Supported (n = 1); Observation O3 (admissibility/persistence separation) and Hypothesis H4 (preservation of competing interpretations, untested) registered per AGC Review Session 006. |
| 0.7.0 | 2026-07-13 | H4 refined for falsifiability at the Slice 2A plan review: technical ordering distinguished from epistemic preference. |
