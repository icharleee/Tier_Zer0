# ADR-0012: Consolidate the knowledge corpus under docs/knowledge/

- **Status:** Accepted (AGC Review Session 001)
- **Date:** 2026-07-13
- **Constitutional articles:** VIII (Justice requires transparency)
- **Supersedes:** none (amends the directory table of ADR-0008 §2 as reaffirmed by ADR-0009 §5)

## Context

AGC Review Session 001 observed that `docs/academy/` is only one *consumer* of institutional knowledge, and that the repository has quietly separated engineering from knowledge — research, standards, and teaching material form a corpus distinct from both governance and implementation. The directory layout should say so.

## Decision

The institutional-knowledge directories consolidate under `docs/knowledge/`:

```
docs/knowledge/
  academy/      — self-service onboarding curriculum
  research/     — Investigation Systems Science (ISS) papers
  standards/    — implementation standards
```

**Boundaries drawn deliberately:**

- `docs/glossary/` (the Lexicon) does **not** move: it is normative governance vocabulary binding on every artifact — closer kin to the Constitution than to the knowledge corpus — and it is referenced pervasively.
- `docs/foundation/`, `docs/adr/`, `docs/domain/`, and `docs/architecture/` are governance, decision, meaning, and design layers respectively — not knowledge-corpus members.

**Link integrity:** immutable, accepted ADR-0008 links to `docs/standards/GOVERNANCE_VERSIONING_STANDARD.md`; per the remedy ADR-0008 itself prescribed for such moves, a redirect stub remains at the old path. All links in mutable documents are updated, with patch version bumps where the documents are governed.

## Governance review

1. **Constitutional Review** — No violation; a directory reorganization with preserved history and repaired references. **PASS.**
2. **Domain Review** — No contact with the ontology or the ladder. **PASS.**
3. **Architectural Review** — Reversible (a future move is another `git mv` plus stubs); maintainable (one extra path segment); operationally trivial; understandable — the tree now names the thing the session recognized: ARGUS keeps institutional knowledge, not just code. **PASS.**

## Consequences

- The repository's top-level `docs/` tree reads as its institutional structure: foundation, governance record, meaning, design, vocabulary, knowledge.
- One permanent redirect stub exists at `docs/standards/GOVERNANCE_VERSIONING_STANDARD.md` for the immutable record's sake.
- Governed documents whose links changed take patch bumps (Brief 1.1.1, Constitution 1.0.1, Lexicon 1.0.1, Governance Versioning Standard 1.0.1) — the versioning standard applied to its own relocation.

## Alternatives considered

- **Rename `academy/` to `knowledge/` and leave research/standards at top level** — rejected: the session's point is that academy, research, and standards are siblings within one corpus; renaming one directory would misstate that.
- **Move `glossary/` in as well** — rejected: the Lexicon is normative and constitutionally adjacent; burying it in a corpus of descriptive knowledge would understate its authority.
- **Defer until after implementation starts** — rejected: every day of delay adds inbound links that a later move must repair; moving before code exists is the cheapest this will ever be.

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

**Affected Articles:** VIII only, and only in spirit: the record's integrity is preserved through redirect stubs and repaired links rather than broken references.

**Compliant?** YES

**Explanation:** A file-tree reorganization touching no doctrine, no data semantics, and no behavior. The only constitutional obligation in play — keeping the immutable record's references resolvable — is met by the redirect stub.
