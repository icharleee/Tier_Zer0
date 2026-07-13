# ADR-0011: Stable ontology identifiers

- **Status:** Accepted (AGC Review Session 001, Standards Committee request)
- **Date:** 2026-07-13
- **Constitutional articles:** III (Conclusions explain themselves), VIII (Justice requires transparency)
- **Supersedes:** none

## Context

AGC Review Session 001's Standards Committee passed the domain bundle with one request: the Ontology needs stable identifiers — not section numbers, not headings. APIs, tests (per ADR-0010), documentation, research papers, and ADRs all need to reference ontological concepts durably. Wording changes under the Governance Versioning Standard; section numbers shift as documents grow. References anchored to either would rot. Standards organizations solve this with immutable identifiers, and so does ARGUS.

## Decision

### Identifier scheme

`ONT-<CODE>-<NNN>` where `<CODE>` is a fixed three-letter concept code and `<NNN>` a zero-padded sequence number within that code.

- `ONT-<CODE>-001` denotes the concept itself (e.g., `ONT-OBS-001` = the Observation concept and its defining rule).
- Subsequent numbers within a code denote additional rules about that concept as they are formalized.
- Cross-cutting principles use the code `PRN`.

### Immutability rules

1. **An identifier, once assigned, never changes meaning and is never reused.** If a concept's wording changes, the identifier stays; if a concept is retired, its identifier is marked retired and points to its successor — it is not recycled.
2. **The registry lives in [`ONTOLOGY.md`](../domain/ONTOLOGY.md)** (§7 for objects, §9 for principles) and is the single authoritative allocation source. New identifiers are allocated only through an Ontology version change under AGC review.
3. **References cite identifiers, not wording or section numbers**, in APIs, tests, documentation, research, standards, and ADRs.

### Initial allocation

Objects (concept identifiers honor the session's examples):

| ID | Concept | | ID | Concept |
|---|---|---|---|---|
| ONT-CAS-001 | Case | | ONT-UNK-001 | Unknown |
| ONT-EVA-001 | EvidenceArtifact | | ONT-UNL-001 | UnknownLink |
| ONT-SRC-001 | SourceLocator | | ONT-UNR-001 | UnknownResolution |
| ONT-OBS-001 | Observation | | ONT-CON-001 | Contradiction |
| ONT-INT-001 | Interpretation | | ONT-CNM-001 | ContradictionMember |
| ONT-HYP-001 | Hypothesis | | ONT-ENT-001 | Entity |
| ONT-REL-001 | Relationship | | ONT-AUD-001 | AuditEntry |

Principles:

| ID | Principle |
|---|---|
| ONT-PRN-001 | The representation is not the thing |
| ONT-PRN-002 | Every step away from evidence adds inference |
| ONT-PRN-003 | What the system does not know is part of what it knows |
| ONT-PRN-004 | The one-rung rule (ladder references climb exactly one rung) |
| ONT-PRN-005 | No provenance, no claim |
| ONT-PRN-006 | Nothing disappears (retraction replaces deletion) |
| ONT-PRN-007 | Human judgment is final and external |
| ONT-PRN-008 | The ontology is the source of truth for meaning (Resolution 003) |
| ONT-PRN-009 | Verification is derived from ontology (Resolution 004) |

## Governance review

1. **Constitutional Review** — No violation; immutable references strengthen the audit trail (VIII) and let every claim about the system's rules explain itself durably (III). **PASS.**
2. **Domain Review** — Identifiers name existing ontology; no meaning is added, removed, or collapsed. **PASS.**
3. **Architectural Review** — Reversible only in the weak sense (abandoning IDs strands references), which is exactly the stickiness identifiers exist to provide; maintainable (a table in one governed document); operationally trivial; understandable; testable (a lint can verify that cited IDs exist in the registry). **PASS.**

## Consequences

- Tests (ADR-0010), the Invariant Matrix, API documentation, and ISS papers gain a stable reference target that survives rewording.
- Allocating an identifier acquires ceremony (Ontology version bump under AGC review) — deliberate, since an identifier is a permanent commitment.
- The Ontology gains a registry-maintenance duty; drift between registry and prose becomes a reviewable defect.

## Alternatives considered

- **Section numbers or heading anchors** — rejected: they change as documents are reorganized; the request explicitly rules them out.
- **UUIDs** — rejected: durable but unreadable; `ONT-OBS-001` carries meaning to a human reviewer, a court, or a test docstring.
- **Identifiers per document rather than per concept** — rejected: concepts outlive documents; the identifier must attach to meaning, not to files.

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

**Affected Articles:** III, VIII (reinforced — durable, self-explaining references and a stronger audit trail). Others untouched.

**Compliant?** YES

**Explanation:** A naming scheme for already-ratified meaning. It changes no behavior and no doctrine; it makes both permanently citable.
