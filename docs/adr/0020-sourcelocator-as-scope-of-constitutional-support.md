# ADR-0020: SourceLocator is the scope of constitutional support

- **Status:** Accepted (Founder Resolution 011, AGC Review Session 008 / Slice 1D plan review — freeze exemption per ONT-PRN-011)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), III (Conclusions explain themselves), IX (Certainty must never exceed the evidence)
- **Supersedes:** none (refines the meaning of ONT-SRC-001; the identifier is unchanged per ADR-0011)

## Context

Slice 1D planning revealed that SourceLocator performs two jobs that are not identical: it *identifies where evidence exists* (video, 00:00:07–00:00:09), and it *defines what portion supports a claim*. Three observations over one video may claim three different windows — three different epistemic scopes over the same physical evidence. The locator is not merely an address; it is the boundary of what an Observation constitutionally rests on.

## Decision

Founder Resolution 011 is recorded (stable identifier **ONT-PRN-016**):

> **A SourceLocator defines the exact scope of evidence upon which an Observation constitutionally depends.**
> Not "where the evidence is," but "the smallest region required to justify this Observation."

Consequences, normative:

1. The Lexicon and Ontology definitions of SourceLocator are updated to scope-of-support language (Lexicon → MAJOR version per its own rules; the ONT-SRC-001 identifier is untouched).
2. Locator creation SHOULD capture the minimal justifying region; over-broad locators are not structurally rejectable in v0.1 (minimality is not machine-decidable) but reviewers treat "smallest region required" as the drafting standard.
3. **Amendment 2 (same session): validation is architected as an independently testable capability distinct from persistence** — `validate_*` produces admissibility reason codes; `create_*` is nearly mechanical and calls it; both occur in one transaction today. AI, batch import, OCR, and external integrations later reuse the same validator, and H3 conformance compares *validation*, not insertion.
4. **Amendment 3: Hypothesis H3 is refined** — *Independent implementations of epistemic admissibility converge when derived from a shared ontology and provenance model.* Observation creation is about admissibility ("this claim is constitutionally allowed to exist"); reasoning begins at Interpretation.
5. Observations carry **two identities**: the operational citation (`OBS-000001`, sequential per case) and the ontological class (`ONT-OBS-001`, derived, never stored) — for the citations research will eventually need.
6. **`is_grounded()` is the only groundedness predicate**: at least one constitutionally valid SourceLocator exists. Nothing more. Grading of groundedness (minimally/fully) was proposed and retracted *within the session* as sufficiency in disguise (ONT-PRN-014) — recorded deliberately, because the architecture correcting its own architect is the discipline working.

## Governance review

1. **Constitutional Review** — PASS: scope-of-support strengthens Articles I and III (claims cite exactly what justifies them); the retracted grading predicate is Article IX protecting itself.
2. **Domain Review** — PASS: a meaning refinement of an existing object; the ladder and one-rung rule are untouched; heterogeneous grounding (one Observation over video + transcript + photo) is anticipated by the junction design, not added.
3. **Architectural Review** — PASS: reversible (wording and a validator split); maintainable (the validator split *reduces* future duplication); operationally realistic; understandable; testable — validation becomes a pure, triangulable surface.

## Consequences

- H3's experimental surface is the validator pair, making the epistemic experiment sharper than an insertion test.
- The Lexicon takes its first MAJOR version — the versioning standard applied honestly to a meaning change.
- Future sufficiency work inherits a clean boundary: scope (locator) and adequacy (sufficiency) are already distinct concepts.

## Alternatives considered

- **Locator as plain address** — rejected: it undersells what the object does constitutionally and would invite Observations grounded on whole artifacts "for convenience."
- **Graded groundedness predicates** — proposed and self-retracted in session: sufficiency wearing eligibility's clothes (ONT-PRN-014).
- **Storing the ontological class per row** — rejected: derivable constants are never stored (Resolution 005 pattern); the class is exposed as a derived property.

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

**Affected Articles:** I, III (reinforced — claims bounded by their exact evidentiary scope); IX (reinforced by the in-session retraction of graded groundedness). Others untouched.

**Compliant?** YES

**Explanation:** A meaning refinement plus a validation architecture. Nothing gains authority over the ontology; the one rejected idea was rejected precisely because it would have let a predicate quietly answer a sufficiency question.
