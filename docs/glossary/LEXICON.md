# The ARGUS Lexicon

- **Document version:** 1.0.0
- **Status:** Normative
- **Established by:** [ADR-0008](../adr/0008-establish-arb-and-documentation-governance.md), Founder Resolution 002

This is the canonical vocabulary of ARGUS. Words drift over time; these must not. Every ADR, API, database schema, UI label, documentation page, and AI prompt uses these terms with exactly these meanings. **One canonical definition. Always.**

Semantic changes to a definition are MAJOR version changes and require Architecture Review Board review (see the [Governance Versioning Standard](../standards/GOVERNANCE_VERSIONING_STANDARD.md)). Adding a term is MINOR.

---

## Epistemic terms

**Reality**
The actual state of affairs that an investigation seeks to reconstruct. Reality is never stored in ARGUS; only fragments of it are.

**Fragment**
Any surviving trace of reality available to an investigation, prior to its formal capture as evidence.

**Evidence**
Fragments that have been collected and preserved under investigative authority. In ARGUS, evidence is always represented as one or more EvidenceArtifacts.

**Claim**
Any analytical statement recorded in ARGUS — an Observation, Interpretation, or Hypothesis. Every claim carries provenance. No provenance, no claim.

**Provenance**
The complete, stored account of where a claim came from: its source references and, for AI-generated claims, model identifier, model version, prompt/workflow version, uncertainty explanation, and review status.

**Understanding**
The human investigator's evolving comprehension of a case, supported — never replaced — by the system. Understanding is not a stored object.

**Judgment**
A consequential human determination (guilt, charging, resolution). Judgment occurs outside ARGUS and is never computed, stored, or emitted by it.

**Retraction**
The formal act of superseding a record with a replacement while preserving the original. Retraction replaces deletion; nothing disappears.

**Analytical ladder**
The ordered, never-collapsed progression: Reality → Evidence → Observation → Interpretation → Hypothesis → Understanding → Human Judgment.

---

## First-class entities

**Case**
The bounded investigative context — with its legal authority basis — within which evidence is collected and analysis occurs.

**EvidenceArtifact**
A digitally represented immutable record corresponding to a collected source of information preserved for investigative purposes. ("Artifact," unqualified, always means EvidenceArtifact.)

**SourceLocator**
A precise, immutable address of a region within a single EvidenceArtifact (a page, a timestamp range, a bounding box, a byte range, a transcript span) through which Observations anchor to evidence.

**Observation**
A source-grounded statement directly supported by one or more SourceLocators. Observations state what evidence shows and contain no meaning-making.

**Interpretation**
A derived meaning inferred from one or more Observations.

**Hypothesis**
A testable explanatory model evaluated against available evidence. Hypotheses over the same evidence coexist; none is structurally privileged, and none is ever system-declared true.

**Unknown**
A formally recognized gap in current understanding.

**UnknownLink**
The explicit connection between an Unknown and a record it affects.

**UnknownResolution**
The human-authored record of how an Unknown was resolved, withdrawn, or determined unresolvable, with provenance for any resolving evidence.

**Contradiction**
A formally recognized incompatibility between two or more analytical claims.

**ContradictionMember**
The explicit link binding one analytical claim into a Contradiction.

**Entity**
An investigatively significant actor or object in the world of the case — a person, organization, vehicle, location, object, or account — as represented in the system, distinct from the reality it denotes.

**Relationship**
An evidence-grounded, typed connection between two Entities.

**AuditEntry**
The append-only, immutable record of a single material action in the system: who did what, to which record, when. AuditEntries are never retracted; corrections are new entries.

---

## Version history

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-13 | Initial canonical vocabulary, ratified by Founder Resolution 002. |
