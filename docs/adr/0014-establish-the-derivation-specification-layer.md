# ADR-0014: Establish the Derivation Specification layer

- **Status:** Accepted (AGC Review Session 002 directive)
- **Date:** 2026-07-13
- **Constitutional articles:** III (Conclusions explain themselves), VII (Scientific integrity before convenience)
- **Supersedes:** none (extends the document hierarchy of ADR-0009 §4)

## Context

AGC Review Session 002 identified a missing document between philosophy and engineering. The chain ratified so far — Ontology → Schema → Implementation → Verification — asserts that each layer derives from the one above, but nowhere is the *translation itself* written down: which engineering obligations each ontological rule generates. Without that document, derivation lives in the heads of whoever writes the schema, the Invariant Matrix must be composed judgmentally rather than mechanically, and "provably derived" is a claim without an artifact behind it.

## Decision

A **Derivation Specification** is established at `docs/domain/DERIVATION_SPECIFICATION.md`, between the Ontology and the Schema. The full derivation chain becomes:

```
Ontology
  → Derivation Specification    (translation: ontological rule → engineering obligations)
  → Domain Schema Specification (structure)   [with Entity Lifecycles]
  → Invariant Matrix            (enforcement)
  → Implementation
  → Verification
```

For every ontological object, the Derivation Specification states, by stable identifier:

```
ONT-XXX-001
  ↓ required schema properties
  ↓ required invariants
  ↓ required audit events
  ↓ required API behavior
  ↓ required tests
```

**Sequencing:** the Derivation Specification is written *before* the Invariant Matrix is populated; the matrix then becomes almost mechanical — each row instantiates an obligation already stated in the Derivation Specification. The pre-implementation roadmap is accordingly: Derivation Specification → Invariant Matrix → ERD → ADR-0007 → Task 001 → Task 002.

**Anti-duplication rule:** the Derivation Specification states *obligations* ("the schema MUST represent…", "a test MUST prove…") and cites the Schema Specification for structural detail; it never restates attribute lists. Where the two disagree, the Derivation Specification is the more authoritative (it sits higher in the chain), and the disagreement is a defect in the lower document.

## Governance review

1. **Constitutional Review** — No violation; Article III is extended to the engineering process: the translation from principle to obligation now explains itself in a governed artifact. **PASS.**
2. **Domain Review** — No ontology content changes; the ladder is untouched. The layer *protects* the ontology by making its downstream force explicit rather than interpretive. **PASS.**
3. **Architectural Review** — Reversible (the layer can be dissolved by a superseding ADR, its content folded downward); maintainable (one governed document, updated when the ontology changes); operationally realistic — it front-loads thinking that would otherwise be spent arguing during implementation; understandable; testable (a lint can verify every ONT identifier has a derivation section). **PASS.**

## Consequences

- Every downstream artifact becomes provably derived: schema property → derivation obligation → ontology identifier → constitutional article.
- Ontology changes acquire a propagation checklist: a new or amended ONT rule is not done until its derivation section exists.
- One more governed document to keep synchronized — the accepted cost of replacing tacit translation with recorded translation.
- ODE (ADR-0010) gains its missing middle: Axioms II and III ("Ontology defines meaning"; "Structure derives from ontology") now have a named artifact performing the derivation.

## Alternatives considered

- **Fold derivation obligations into the Ontology** — rejected: the Ontology is deliberately implementation-blind; engineering obligations would contaminate the document meant to survive a twenty-year rebuild.
- **Fold them into the Invariant Matrix** — rejected: the matrix is enforcement bookkeeping (mechanism, actor, test); deriving obligations *and* recording enforcement in one table conflates translation with verification.
- **Leave translation tacit** — rejected: that is the status quo this ADR exists to end; tacit derivation is unauditable derivation.

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

**Affected Articles:** III, VII (reinforced: self-explaining translation, rigor over expedience). Others untouched.

**Compliant?** YES

**Explanation:** A documentation-layer decision. It changes no domain semantics and no behavior; it records the previously unwritten step by which doctrine becomes engineering.
