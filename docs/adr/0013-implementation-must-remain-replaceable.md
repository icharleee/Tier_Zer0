# ADR-0013: Implementation must remain replaceable

- **Status:** Accepted (Founder Resolution 005, AGC Review Session 002)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience), VIII (Justice requires transparency); Prime Directive
- **Supersedes:** none

## Context

AGC Review Session 002 closed the governance foundation with one final founding resolution. Resolution 003 established that the ontology is the source of truth for *meaning*. Its counterpart was still unstated: what that implies for every artifact *downstream* of meaning. Without it, the oldest failure mode in software remains open — an implementation detail (a table, a contract, a prompt) quietly hardens into de facto doctrine because changing it is expensive, and the system starts meaning whatever its code happens to do.

## Decision

Founder Resolution 005 is recorded as a founding principle:

> **Implementation must remain replaceable.**
> No implementation artifact may become more authoritative than the ontology from which it derives.

This binds, without exception: SQLAlchemy models, PostgreSQL schemas, API contracts, UI components, AI prompts, JSON schemas, test fixtures, and migration scripts. **All are replaceable. None define meaning. Only the ontology does.**

Normative consequences:

1. **Authority test.** If discarding an artifact and re-deriving it from the ontology (via the Derivation Specification, ADR-0014) would produce a *different* system, the artifact has been defining meaning — that is a defect in the artifact, resolved by re-deriving it, never by amending the ontology to match it.
2. **Meaning changes flow one way.** A change of meaning is made in the ontology first (AGC review, version change) and propagated downward; it is never introduced in an implementation artifact and back-filled.
3. **Resolutions 003 and 005 together complete the derivation chain:** 003 governs meaning; 005 governs implementation.
4. The principle receives stable identifier **ONT-PRN-010** in the Ontology registry.

With this resolution, the Chief Architect declares the governance foundation **complete**. The standing order of authority is:

```
The Constitution governs.
The Governance Council decides.
The Ontology defines meaning.
The Derivation Specification explains translation.   (ADR-0014)
The Schema defines structure.
The Invariant Matrix defines enforcement.
The Code implements.
The Tests verify.
```

**Nothing skips a layer.**

## Governance review

1. **Constitutional Review** — No violation; the resolution operationalizes the Prime Directive at the engineering level: reality (as modeled in the ontology) may never be redefined by the convenience of an implementation. **PASS.**
2. **Domain Review** — The ontology's authority is strengthened, not altered; no ladder contact. **PASS.**
3. **Architectural Review** — Reversible only by superseding ADR (appropriately sticky for a founding principle); maintainable (it removes work: implementation debates end at "re-derive it"); operationally realistic; understandable; testable in review (the authority test in §1 is a concrete question a reviewer can ask). **PASS.**

## Consequences

- Vendor, framework, and language choices stay demoted forever: ADR-0006's stack is confirmed as replaceable machinery, and every future stack ADR inherits that status.
- Migration and rewrite decisions become tractable: what must be preserved is exactly the ontology and its derivations, nothing else.
- Implementation shortcuts that would be cheaper to canonize than to fix are constitutionally unavailable — a deliberate cost.

## Alternatives considered

- **Leave it implicit in Resolution 003** — rejected: 003 says where meaning lives; it does not say what happens when an artifact starts accumulating authority. The failure mode this resolution targets thrives precisely in that silence.
- **Enumerate protected artifacts case-by-case** — rejected: the list would trail reality; the principle covers whatever implementation artifacts come to exist.

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

**Affected Articles:** VII, VIII, and the Prime Directive (all reinforced). Others untouched — this is a principle about artifact authority, not about evidence handling or judgment.

**Compliant?** YES

**Explanation:** The resolution constrains the engineering process only: implementation may never outrank derived meaning. Its constitutional effect is protective — it prevents the slow, silent transfer of authority from governed documents to ungoverned code.
