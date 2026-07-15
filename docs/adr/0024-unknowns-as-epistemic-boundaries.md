# ADR-0024: Unknowns are epistemic boundaries, and boundary objects are kept distinct

- **Status:** Accepted (Founder Resolution 015, AGC Review Session 007 — freeze exemption per ONT-PRN-011)
- **Date:** 2026-07-13
- **Constitutional articles:** II (Human judgment is final), IX (Certainty must never exceed the evidence)
- **Supersedes:** none (sharpens ONT-UNK-001 semantics ratified in ADR-0005)

## Context

Slice 2B will build Unknown — not another entity but the first explicit representation of **negative knowledge**. Without a sharpened definition, Unknown drifts into TODO items, investigation tasks, reminders, or hypotheses-in-waiting. It must instead say exactly one thing: *this question currently has no constitutionally admissible answer.*

## Decision

### 1. Founder Resolution 015 (stable identifier ONT-PRN-020)

> **Unknowns represent the boundaries of current knowledge, never placeholders for future assumptions.**

Consequences: an Unknown is stated as a question, not a task; it carries no implied answer, no priority-as-truth, no draft hypothesis; its existence constrains reasoning without implying any conclusion; and no derived computation may treat an open Unknown as evidence, inference, or support for anything (Article IX: absence of data is never evidence of absence — nor of presence).

### 2. Boundary objects (a concept, not a table)

The negative space has structure: **Unknown bounds Interpretation** (it limits *meaning*); **Contradiction bounds Hypothesis** (it limits *explanation*). These are different limits and are kept separate forever — a limiting observation is not a contradiction (ADR-0020), and an unknown is not a conflict. The symmetry is recorded in the Ontology's negative-space section; no schema unification of the two families is ever permitted without constitutional change.

### 3. Hypothesis H5, refined

> **H5: Independent implementations preserve explicit epistemic boundaries without transforming absence into evidence, inference, or implied support for any competing interpretation.**

Slice 2B is its first experiment, connecting directly to Article IX.

## Governance review

1. **Constitutional Review** — PASS: Article IX finally gains its structural subject (explicit evidentiary boundaries rather than inferred uncertainty); Article II preserved (dispositions human-only via UnknownResolution, per the ratified spec).
2. **Domain Review** — PASS: sharpens ratified semantics; the ladder untouched; the boundary-object symmetry names what ADR-0005 already separated.
3. **Architectural Review** — PASS: reversible in wording only (the underlying separations are already constitutional); maintainable; the question-form and no-implication properties are testable.

## Consequences

- Slice 2B's validators refuse task-shaped or assumption-shaped Unknowns (a conservative question-form guard, honestly labeled a heuristic like the comparative guard).
- Interpretation's `UNRESOLVED` uncertainty status gains its intended referent: a *named* Unknown — the path by which Article IX coverage becomes legitimate.
- Contradiction (Slice 2C) inherits a clean boundary: it will bound Hypothesis, not Interpretation, and will never merge with Unknown.

## Alternatives considered

- **Unknown as a task/workflow object** — rejected: converts epistemic boundaries into project management and invites silent assumption-laundering.
- **One unified "issue" object for unknowns and contradictions** — rejected: limits on meaning and limits on explanation are different kinds; merging them collapses the negative space exactly as flattening once threatened the ladder.

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

**Affected Articles:** IX (activated structurally: knowledge boundaries become first-class), II (dispositions stay human). Others untouched.

**Compliant?** YES

**Explanation:** Defines what Unknown means before it exists in code, so the first representation of negative knowledge cannot be born as a to-do list. Nothing here answers any question; it ensures unanswered questions stay visibly unanswered.
