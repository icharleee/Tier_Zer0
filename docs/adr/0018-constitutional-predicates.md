# ADR-0018: Constitutional predicates, and eligibility versus sufficiency

- **Status:** Accepted (Founder Resolution 009, AGC Review Session 006 / Slice 1C plan review — freeze exemption per ONT-PRN-011: distinction discovered during slice design)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), VI (Privacy and legal authority), IX (Certainty must never exceed the evidence)
- **Supersedes:** none

## Context

The Slice 1C plan used "eligibility" for a single question. Review revealed three distinct concepts hiding in the word: **structural eligibility** (can this artifact *possibly* support an Observation — objective: ACTIVE, uncorrupted, constitutionally recorded), **contextual eligibility** (can it support one *in this investigation* — case open, access lawful, evidence not sealed), and **epistemic sufficiency** (does the artifact actually *contain enough information* for a particular observation — a blurred photograph is eligible and may still not support a license-plate reading). The first two are constitutional questions; the third is an evidence question that will dominate once OCR, AI, and forensics arrive.

## Decision

### 1. Founder Resolution 009 (stable identifier ONT-PRN-014)

> **Eligibility determines whether an artifact may participate in reasoning. Sufficiency determines what reasoning it can support.**
> Those are not the same thing.

Sufficiency is explicitly **out of scope for v0.1** and must never be collapsed into eligibility — an eligibility check that silently judged sufficiency would be the system exceeding the evidence (Article IX).

### 2. Constitutional predicates

Derived permission questions form a named family — **constitutional predicates** — of which observation eligibility is one member:

```
can_support_observation()    can_be_retracted()
can_be_interpreted()         can_be_sealed()
can_generate_hypothesis()    can_be_unsealed()
```

Normative properties of every predicate:

- **Derived, never stored.** The database never remembers what it can always prove (Resolution 005). No persisted eligibility flags, anywhere, ever.
- **Explains its refusals.** A predicate answers with a decision *and* canonical reason codes citing ontology rules — a refusal accompanied by rule, article, and explanation is often more valuable than success. The negative gate is the feature.
- **Independently derivable.** Each predicate is rendered in Python and in PostgreSQL from the same specification, conformance-tested for identical decisions and identical reason codes (the ODE H2 experiment).
- **Derived from existing sources where possible.** Transition-authority predicates (`can_be_retracted`, `can_be_sealed`, `can_be_unsealed`) derive mechanically from the transition registry — no second rendering of the lifecycle is created (ONT-PRN-013).

### 3. The canonical eligibility matrix is normative

[`docs/domain/CONSTITUTIONAL_PREDICATES.md`](../domain/CONSTITUTIONAL_PREDICATES.md) is established as a normative domain artifact holding the predicate definitions, the canonical reason codes, and the eligibility decision matrix (artifact state × case state → structural, contextual, reason). Implementations and tests derive from the matrix; a future generation step may consume it directly (ADR-0017's direction). The observed emergence of a predicates layer — objects answer *what exists*, predicates answer *what is permitted* — is recorded for a future ontology restructuring; **no directory reorganization now.**

### 4. The Slice 1C acceptance test, redefined

> **Can every constitutional predicate be derived identically by independent implementations?**

Observation eligibility is Experiment One of that program; interpretation eligibility, hypothesis eligibility, retraction authority, and seal authority follow the same methodology in later slices. ODE **Hypothesis H2** is registered: *behavior derived independently from a common ontology can converge across implementations without shared executable logic.*

## Governance review

1. **Constitutional Review** — No violation. Derived-never-stored protects Resolution 005; refusal-with-explanation extends Article III to negative decisions; the eligibility/sufficiency split protects Article IX. **PASS.**
2. **Domain Review** — The ladder is untouched; the predicates layer names something that already existed implicitly ("no SourceLocator against a non-ACTIVE artifact"). Sufficiency is fenced off before any component could conflate it. **PASS.**
3. **Architectural Review** — Reversible (predicates are pure derivations; renaming or restructuring them strands nothing); maintainable (one specification, two renderings, one conformance sweep — the 1B pattern reused); operationally realistic; understandable; testable by construction. **PASS.**

## Consequences

- Slice 1D's Observation INSERT can require eligibility structurally (the negative gate precedes the feature).
- Every future "may X happen?" question has a named home and a ready methodology, instead of ad-hoc service checks.
- The canonical matrix becomes a maintenance obligation and, eventually, a generation source.
- Sufficiency, when it arrives, gets its own concepts and its own ADR — it may not be bolted onto eligibility.

## Alternatives considered

- **A single `observation_eligible()` function** — rejected: the next slice would add a second one-off, and the family pattern would be discovered later at refactoring cost.
- **Stored eligibility flags maintained by triggers** — rejected: a competing source of constitutional truth that can go stale or be tampered with; the ontology already proves the answer.
- **Treating sufficiency as a stricter eligibility level** — rejected: it collapses a constitutional question into an evidentiary one, precisely the conflation Resolution 009 forbids.

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

**Affected Articles:** I, VI, IX (reinforced: reasoning participation is gated by constitutional state; sealed evidence requires authority; eligibility never overclaims into sufficiency). III extended to refusals. Others untouched.

**Compliant?** YES

**Explanation:** This ADR names and bounds a derivation pattern. It stores nothing, decides nothing by machine that was human, and its central distinction exists to prevent the system from ever answering a question the evidence has not earned.
