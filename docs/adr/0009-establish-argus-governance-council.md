# ADR-0009: Establish the ARGUS Governance Council

- **Status:** Accepted (Chief Architect decision, Founder Resolution 003)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience), VIII (Justice requires transparency); Prime Directive
- **Supersedes:** ADR-0008 (governance-body design replaced; its documentation-corpus, versioning, and Lexicon decisions are reaffirmed unchanged in §5)

## Context

ADR-0008 established an Architecture Review Board hours before this decision. On review, the Chief Architect determined the name and shape were too narrow: ARGUS governs software, research, ontology, engineering, investigation science, AI behavior, standards, and documentation — architecture is only one of these. Rather than amending the accepted ADR-0008 (accepted ADRs are immutable), this ADR supersedes it, which is itself the first demonstration of the governance mechanism working as designed.

This ADR is written for the organization ARGUS intends to become — a hundred engineers — not the two founders it has today. Good governance scales quietly because it was designed to.

## Decision

### 1. The ARGUS Governance Council (AGC)

The **ARGUS Governance Council** is established as the project's governing body. The Architecture Review Board becomes one of its standing functions:

```
ARGUS Governance Council (AGC)
├── Constitutional Review      (gate: compliance with the Constitution)
├── Domain Review Board        (gate: preservation of the ontology)
├── Architecture Review Board  (gate: sound, maintainable, reversible systems)
├── Research Review Board      (stewardship of the ISS corpus)
└── Standards Committee        (stewardship of implementation standards)
```

**Membership and scale.** Today, the founding team holds every seat. As the organization grows, each function acquires a designated lead and delegated reviewers; the council remains the union of its functions. No function may be dissolved except by an ADR superseding this one.

**Operation.** The AGC convenes asynchronously by default: the pull request carrying an ADR *is* the council session, and the ADR's recorded review outcomes are its minutes. Synchronous convening is reserved for contested proposals. All outcomes are recorded in the ADR itself — governance that is not written down did not happen (Article VIII).

### 2. Three permanent review mechanisms

Every significant proposal passes three reviews, in this order:

**2.1 Constitutional Review.**
*Does this violate the Constitution?*
If yes — **the proposal stops.** No balancing test. No majority vote. The Constitution outranks convenience. A proposal that can only proceed by amending the Constitution must do so explicitly: a separate ADR, a MAJOR version change, and its own Constitutional Review.

**2.2 Domain Review.**
*Does this preserve the ontology?*
Specifically, the analytical ladder:

```
Reality → Evidence → Observation → Interpretation → Hypothesis → Understanding → Human Judgment
```

**No ADR may collapse these layers. Ever.** Domain Review also guards the first-class status of Unknowns and Contradictions and the Lexicon's canonical meanings.

**2.3 Architectural Review.**
Questions include: Is it reversible? Is it maintainable? Is it operationally realistic for the team we actually have? Is it understandable? Is it testable?
**Architecture serves the domain — not the reverse.** An architecturally elegant proposal that bends the ontology fails Domain Review first and never reaches this one.

(The five ARB questions of ADR-0008 map into this structure: its Constitutional and Domain reviews become mechanisms 2.1 and 2.2; its Systems, Operational, and Reversibility reviews merge into 2.3.)

### 3. The Constitutional Checklist

Every ADR from this one onward **finishes** with a Constitutional Checklist auditing all nine articles — creating a constitutional audit trail across the decision record. The ADR template is updated with the format (see this ADR's final section for the first instance).

### 4. Founder Resolution 003 — the ontology is the source of truth for meaning

Recorded as a founding principle:

> **The ontology is the source of truth for meaning.**
> Every implementation artifact — database schemas, APIs, user interfaces, AI prompts, documentation, tests, and analytical models — must derive from the ontology rather than defining it independently.

This protects against the most common form of architectural drift: the database beginning to define the business instead of the business defining the database. Accordingly, `docs/domain/` is ordered **ontology first, schema second**:

```
docs/domain/
  ONTOLOGY.md                    — the vocabulary of reality as understood by ARGUS
  DOMAIN_SCHEMA_SPECIFICATION.md — the structural contract derived from the ontology
  INVARIANT_MATRIX.md            — per-entity enforcement specification (required by ADR-0006)
  ENTITY_LIFECYCLES.md           — authoritative state machines per entity
```

The Domain Invariant Matrix relocates from `docs/architecture/` (where ADR-0008 queued it) to `docs/domain/`; the ERD remains an architecture artifact. If ARGUS were rebuilt twenty years from now in a different language and database, `ONTOLOGY.md` should remain valid unchanged.

### 5. Reaffirmed from ADR-0008

Unchanged and carried forward: the expanded documentation corpus (research, standards, glossary, academy, architecture); the Governance Versioning Standard and semantic versioning of governance documents; the normative status of the Lexicon; the reservation of ADR-0007 for Evidence Ingestion and Atomic Finalization; and the Constitution's location at `docs/foundation/` with its recorded rationale.

## Governance review

**Constitutional Review** — No article violated; mechanisms 2.1–2.3 operationalize Articles VII and VIII, and the checklist strengthens the audit trail the Constitution demands. **PASS.**

**Domain Review** — The ontology is untouched and newly protected: Domain Review becomes a permanent, named gate, and Resolution 003 subordinates every implementation artifact to the ontology. **PASS.**

**Architectural Review** — Reversible (a superseding ADR can restructure the council); maintainable (asynchronous, PR-native operation adds no standing meetings); operationally realistic for two founders while shaped for a hundred engineers; understandable (three questions, fixed order); testable in the process sense (an ADR missing its checklist is mechanically detectable in review and CI). **PASS.**

## Consequences

- Governance now has a body (AGC), mechanisms (three reviews), and an audit trail (the checklist) that scale with headcount without redesign.
- ADR-0008 enters the superseded state a few hours after acceptance — visible evidence that the record is corrected by supersession, never by rewriting.
- Every future ADR grows by one mandatory section; drafting cost rises slightly and deliberately.
- The domain documentation set grows to four files with a declared derivation order; keeping schema subordinate to ontology becomes a reviewable property.

## Alternatives considered

- **Keep the ARB name and scope** — rejected: the name would misdescribe the majority of what ARGUS governs, and renaming later, after habits form, costs more than renaming now.
- **Amend ADR-0008 in place** — rejected: accepted ADRs are immutable; editing the record to look as if the ARB never existed would violate the very transparency this decision serves.
- **A governance charter outside the ADR system** — rejected: governance decisions are architectural decisions about the institution; they belong in the same immutable, superseded-not-rewritten record as everything else.

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

**Affected Articles:** VII, VIII (both reinforced: reviews add deliberate rigor; the checklist and recorded outcomes extend transparency to governance itself). Articles I–VI, IX are untouched by this process-level decision.

**Compliant?** YES

**Explanation:** This ADR changes how decisions are reviewed and recorded, not what the system may do with evidence, claims, or judgment. Its only constitutional effects are reinforcing ones: mandatory constitutional audit of every future decision (VIII) and a hard, non-negotiable constitutional gate ahead of every proposal (VII, Prime Directive).
