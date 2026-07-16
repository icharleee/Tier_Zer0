# ADR-0027: ContradictionDisposition as a first-class object

- **Status:** Accepted (AGC Review Session 010, Amendment 2 — freeze exemption per ONT-PRN-011: the gap was discovered when Slice 2C's plan proposed a "symmetry extension" that was in fact an ontology change)
- **Date:** 2026-07-13
- **Constitutional articles:** II (Human judgment is final), III (Conclusions explain themselves), VIII (Transparency)
- **Supersedes:** none (extends the first-class object registry of ADR-0011; sharpens ADR-0005 §7 semantics)

## Context

The Slice 2C plan proposed deriving Contradiction's epistemic disposition from a resolution record, "following the Session 008 pattern." The review correctly refused the silence: Unknown had `UnknownResolution` ratified as first-class from Phase 1; Contradiction has no equivalent object, and inventing one during migration design would let implementation define ontology (ONT-PRN-010 violated at the process level). The governance decision comes first.

## Decision

The **preferred path** is taken: **ContradictionDisposition** is introduced as a new first-class ontology object.

1. **"Disposition," not "Resolution"** — some outcomes preserve the incompatibility rather than resolve its underlying facts. Controlled outcomes:
   - `EXPLAINED` — the apparent incompatibility is accounted for (e.g., differing scopes discovered on review), with rationale and provenance;
   - `NO_LONGER_APPLICABLE` — the shared scope or conditions no longer obtain;
   - `WITHDRAWN` — raised in error, with rationale;
   - `UNRESOLVED` — formally recorded as standing: the incompatibility persists and no disposition of its facts is currently possible;
   - `SUPERSEDED` — replaced by a better-scoped Contradiction, linked.
   **No outcome exists, or may ever be added, that implies a member was proven correct** — adjudication and survivor selection are prohibited (Session 010 formal authorization).
2. **Registry entries:** stable identifier **ONT-CDP-001**; Ontology §7 object table row (grouping: negative space; role: *the human record of how a conflict was disposed — never of which claim reality favors*); Lexicon definition (MINOR). The first-class object count becomes fifteen.
3. **Structure:** human-only author; owning Contradiction (at most one active disposition); outcome; mandatory rationale; optional provenance references (claims or artifacts informing the disposition — *informing*, never *vindicating*); content-immutable; terminal (a mistaken disposition is superseded by a successor, mirroring UnknownResolution).
4. Epistemic disposition of a Contradiction is **derived** from this record; operational state (`OPEN ⇄ UNDER_REVIEW`) remains a separate CT column per the Session 008 pattern, now legitimately reusable because the underlying object exists.

## Governance review

1. **Constitutional Review** — PASS: Article II (disposition human-only, structurally), III (dispositions explain themselves), VIII (the conflict's full history — raised, reviewed, disposed — is durable). The prohibited-outcome rule protects Article IV permanently.
2. **Domain Review** — PASS: the negative space gains its second disposition object with semantics parallel to UnknownResolution but vocabulary deliberately distinct (disposition ≠ resolution); the boundary taxonomy's never-alters invariant is untouched.
3. **Architectural Review** — PASS: reversible before implementation ships; maintainable (mirrors an existing pattern); the alternative (append-only record owned by Contradiction, not first-class) was genuinely considered and rejected below.

## Consequences

- Slice 2C implements the object with the same machinery as UnknownResolution (human-only DEFINER function, terminal, audited, derived status).
- Future boundary objects, if any, inherit a decided pattern: boundary + membership/links + human disposition object, all first-class.
- The Lexicon, Ontology, Schema Specification, Lifecycles, and Derivation Specification all take coordinated bumps — the cost of doing this in governance rather than in a migration, paid once, visibly.

## Alternatives considered

- **Append-only disposition record owned by Contradiction, not first-class** — rejected: less extensible, and it would make Contradiction's disposition history structurally weaker than Unknown's for no principled reason; the asymmetry would invite later "cleanup" that is really an ontology change in disguise.
- **Reusing UnknownResolution polymorphically** — rejected: ONT-PRN-021 discipline — different boundaries, different disposition semantics, never merged.
- **Deferring disposition entirely to Slice 2D** — rejected: a Contradiction that cannot be disposed accumulates as permanent noise, and Article II requires the human path to exist wherever the boundary does.

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

**Affected Articles:** II, III, VIII (reinforced); IV (protected permanently by the prohibited-outcome rule). Others untouched.

**Compliant?** YES

**Explanation:** Adds the human disposition path for conflicts as governed ontology rather than invented implementation. Its strongest clause is negative: no outcome may ever say who was right.
