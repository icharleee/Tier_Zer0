# ADR-0030: Historical articulation and current derived condition remain distinct

- **Status:** Accepted (Founder Resolution 020, AGC Review Session 013 — freeze exemption per ONT-PRN-011: a pattern implementation exposed at Slice 2D, generalized)
- **Date:** 2026-07-13
- **Constitutional articles:** V (Evidence is immutable), VIII (Justice requires transparency), IX (Certainty never exceeds evidence)
- **Supersedes:** none (generalizes the Session 012 Amendment 2 mechanism)

## Context

Session 012 required Slice 2D to separate `alternative_articulation_at_creation` (immutable historical truth) from `current_alternative_state` (derived, changing as links appear and counterparts retract). Session 013's architectural review validated the mechanism as a reusable pattern — *temporally qualified truth*: the system simultaneously preserves "at creation, no alternative was articulated" and "at present, an alternative exists," and neither statement overwrites the other. The same shape already appears in boundary disposition (a disposed Contradiction remains historically linked while its current boundary activity is derived), member health, grounding health, and every retraction-aware current state.

## Decision

Founder Resolution 020 is recorded (stable identifier **ONT-PRN-025**):

> **Historical articulation and current derived condition must be represented separately whenever later events can change the present state without invalidating what was true at creation.**

Normative consequences:

1. **Stored history, derived present.** What was recorded *then* is content-immutable; what is true *now* is computed from subsequent records and stored nowhere. A stored field that later events would need to update is a design defect (it must either be historical and immutable, or current and derived).
2. **Neither erases the other.** No derivation may overwrite, conceal, or "correct" a historical articulation; no historical record may be cited as if it were the current condition. Read surfaces expose both, labeled.
3. **The collapse this prevents:** systems that flatten *what was recorded then* into *what is currently true now* — retroactively falsifying the record or freezing the present. Both failure modes are unconstitutional (Articles V, VIII).

## Governance review

1. **Constitutional Review** — PASS: Article V extended from evidence to articulations; Article VIII served — an auditor can always ask both "what did they say at creation?" and "what is the case now?".
2. **Domain Review** — PASS: names the pattern already present in five mechanisms (alternative articulation, boundary disposition, member health, grounding health, retraction-aware states) without altering any of them.
3. **Architectural Review** — PASS: checkable at design time (every temporal field classifies as historical-immutable or current-derived); the Slice 2D acceptance test (creation-time absence explanation surviving later linking) is the reusable verification template.

## Consequences

- Slice 3A's read model must expose historical articulations and current derived states side by side, labeled, without merging them — this becomes an explicit H8 obligation.
- Future schema reviews classify every temporal attribute as one of the two kinds; a mutable "status" column that later events rewrite is refused at review.

## Alternatives considered

- **Record only current state and rely on the audit trail for history** — rejected: the audit trail witnesses acts; it is not a queryable representation of what was articulated, and reconstructing articulation from events converts transparency into archaeology.
- **Version the historical field in place** — rejected: versioning still privileges the latest value; the constitutional point is that the creation-time statement remains a first-class fact.

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

**Affected Articles:** V, VIII, IX (temporally qualified truth as a structural guarantee). Others untouched.

**Compliant?** YES

**Explanation:** Prevents the two symmetric distortions of time — rewriting the past to match the present, and presenting the past as if it were the present.
