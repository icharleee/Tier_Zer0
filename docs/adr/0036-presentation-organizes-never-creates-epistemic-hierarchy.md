# ADR-0036: Presentation organizes, never creates epistemic hierarchy

- **Status:** Accepted (Founder Resolution 026, AGC Review Session 021 — freeze exemption per ONT-PRN-011: the governing constraint for Slice 1F-C, proposed at the Slice 1F-B completion review)
- **Date:** 2026-07-13
- **Constitutional articles:** IV (Alternatives remain possible), VIII (Justice requires transparency), IX (Certainty never exceeds evidence)
- **Supersedes:** none (the presentation half of the identity → authority → presentation decomposition)

## Context

The API can be constitutionally correct, the data constitutionally correct, the authority projection constitutionally correct — and the interface can still distort all of it. A large default-expanded card at the top of the page versus a collapsed one below the fold creates ranking with no ranking field anywhere. This is exactly the compositional drift O9 predicts: every lower layer remains constitutional while the presentation alone introduces preference. The interface is not neutral merely because it does not modify the database.

## Decision

Founder Resolution 026 is recorded (stable identifier **ONT-PRN-031**):

> **Presentation may organize constitutional information for comprehension, but it must not create epistemic hierarchy, certainty, preference, or conclusion that does not already exist in the underlying authorized projection.**
>
> **Corollary:** Visual prominence, ordering, color, default expansion, interaction affordances, and labels are part of the constitutional presentation surface whenever they can imply evidentiary or epistemic meaning.

Normative consequences:

1. **Presentation symmetry.** Competing Interpretations and Hypotheses render through the same component and schema, with no "Primary Hypothesis" / "Best Explanation" language, no winner badges, no confidence meters, no default-expanded favorite. Default ordering is technical and non-epistemic (citation order); any user-selected sort is labeled organizational, never evidentiary — and sorting by health as though health meant likelihood is prohibited.
2. **No truth-semantic color.** `CURRENT`/`DEGRADED`/`UNSUPPORTED` are not TRUE/QUESTIONABLE/FALSE; `CHAIN_VALID` is not "verified evidence." Green-means-true / red-means-false encodings are prohibited for health and integrity states; text labels carry the meaning, color may supplement accessibility, never replace semantics.
3. **Retractions remain visible.** Retracted records are visibly marked, never erased; if the interface permits collapsing them, the collapsed state still visibly counts them ("2 retracted records present") — collapse must not become concealment.
4. **Boundaries are relationships, not verdicts.** Unknowns and Contradictions render as explicit boundary relationships ("Limited by Unknown," "Challenged by Contradiction"), never as warning decorations implying "weak hypothesis" — the distinction between constraint and judgment survives rendering.
5. **Administrative review is not epistemic endorsement.** No interaction labeled "accept," "confirm," "approve theory," or "validated" exists; operational workflow states (reviewed / acknowledged / needs follow-up), where they ever arrive, are defined operationally behind their own gate — review-workflow mutation is NOT AUTHORIZED for H12.
6. **Accessibility semantics are constitutional.** The DOM/accessibility tree preserves the same order and labels as the visible interface; keyboard navigation and initial focus privilege no Hypothesis. A visually symmetric page that is asymmetric to a screen reader violates this principle.

## Governance review

1. **Constitutional Review** — PASS: Article IV extended to the pixel — alternatives remain possible only if the interface leaves them structurally equal; Article IX — no visual certainty beyond the evidence; Article VIII — retraction history and withholding stay visible.
2. **Domain Review** — PASS: no epistemic object added; the ladder's separations survive rendering (boundary ≠ verdict; health ≠ truth; disposition ≠ adjudication).
3. **Architectural Review** — PASS: testable — presentation constraints are assertable over the rendered DOM (component identity, ordering, labels, focus order, accessibility tree); the read-only surface adds no mutation path.

## Consequences

- The Slice 1F-C gate must present the presentation-constraint checklist as normative text before any interface code (ONT-PRN-024), and the H12 suite transcribes it (leg 3).
- Presentation joins the contamination discipline: preferred/leading/primary/confidence/accept vocabulary is prohibited on the rendered surface exactly as on schemas.

## Alternatives considered

- **Treat the UI as out of constitutional scope ("it's just display")** — rejected: ordering, prominence, and defaults create meaning; O16's whole claim is that read-only presentation is epistemically consequential.
- **Rely on designer judgment and review** — rejected alone: judgment decays and reviewers rotate; the constraints must be normative and mechanically assertable where possible, with review still judging what scanning cannot.

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

**Affected Articles:** IV, VIII, IX (the ladder's non-preference carried through to the human eye and the screen reader alike). Others untouched.

**Compliant?** YES

**Explanation:** Once the authorized truths reach a human screen, the interface must not quietly choose a story for them.
