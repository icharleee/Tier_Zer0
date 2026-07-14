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

> **Hypothesis H2:** Behavior derived independently from a common ontology can converge across implementations without shared executable logic.

Slice 1B tested rule *transitions*; Slice 1C tests derived *behavior* — constitutional predicates (permission questions computed from constitutional state) rendered independently in Python and PostgreSQL against a canonical decision matrix. Different experiment, same methodology. H2 is a stronger claim than H1: not merely that implementations enforce the same rules, but that they independently arrive at the same *decisions*. It also suggests ODE may eventually distinguish structural derivation, behavioral derivation, and verification derivation.

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
