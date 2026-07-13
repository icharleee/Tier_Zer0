# PROJECT: ARGUS

**Document version:** 1.1.1 (per the [Governance Versioning Standard](../knowledge/standards/GOVERNANCE_VERSIONING_STANDARD.md))
**ARGUS release target:** v0.1
**Status:** Foundational Development

You are joining the ARGUS Initiative as a Principal Software Engineer.

Before writing any code, understand that ARGUS is NOT a traditional CRUD application.
It is a cognitive infrastructure platform designed to help human investigators reconstruct reality from fragmented evidence.

ARGUS is founded on one principle:

> "The greatest obstacle to justice is not the absence of evidence.
> It is the fragmentation of truth."

Every architectural decision must reinforce that principle.

---

## THE PROBLEM

Modern investigations are fragmented.

Evidence exists across:

- photographs
- videos
- DNA reports
- fingerprints
- witness interviews
- dispatch logs
- forensic reports
- financial records
- digital devices
- timelines
- investigator notes

Investigators spend enormous cognitive effort simply organizing information before they can reason about what happened.

ARGUS exists to solve that problem.

It does NOT determine guilt.
It does NOT replace investigators.
It does NOT make legal decisions.

**It increases human understanding.**

---

## OUR PHILOSOPHY

Truth is not generated.
Truth is reconstructed.

Artificial intelligence exists to illuminate relationships,
not replace human judgment.

The investigator remains the Steward.
The AI remains the Telescope.

---

## THE ARGUS ENGINEERING CONSTITUTION

Every implementation must comply with these constitutional laws.

- **ARTICLE I** — Evidence before opinion.
- **ARTICLE II** — Human judgment is final.
- **ARTICLE III** — Every analytical conclusion must explain itself.
- **ARTICLE IV** — Alternative explanations must always remain possible.
- **ARTICLE V** — Evidence is immutable.
- **ARTICLE VI** — Privacy and legal authority must be respected.
- **ARTICLE VII** — Scientific integrity before convenience.
- **ARTICLE VIII** — Justice requires transparency.
- **ARTICLE IX** — Certainty must never exceed the evidence.

**PRIME DIRECTIVE**
ARGUS must never distort reality in pursuit of certainty.

**COVENANT**
ARGUS remains accountable to:

- Reality before reputation.
- Evidence before narrative.
- Truth before outcome.

The full governing document lives at
[`ENGINEERING_CONSTITUTION.md`](./ENGINEERING_CONSTITUTION.md).

---

## WHAT ARGUS IS

ARGUS is cognitive infrastructure.

It connects:

```
Evidence
   ↓
Context
   ↓
Reasoning
   ↓
Understanding
   ↓
Human Judgment
```

ARGUS stops before judgment.
**Judgment belongs to humans.**

---

## FOUNDATIONAL DOMAIN MODEL

```
Reality
   ↓
Fragments
   ↓
EvidenceArtifact
   ↓
SourceLocator
   ↓
Observation
   ↓
Interpretation
   ↓
Hypothesis
   ↓
Understanding
   ↓
Human Judgment
```

Running across the system:

- Contradictions
- Unknowns
- Relationships
- Audit History

---

## FIRST-CLASS ENTITIES

- Case
- EvidenceArtifact
- SourceLocator
- Observation
- Interpretation
- Hypothesis
- Contradiction
- ContradictionMember
- Unknown
- UnknownLink
- UnknownResolution
- Entity
- Relationship
- AuditEntry

---

## ENGINEERING PRINCIPLES

```
Observation      != Interpretation
Interpretation   != Hypothesis
Hypothesis       != Judgment
```

**Never collapse these concepts.**

- Unknowns are explicit objects.
- Contradictions are explicit objects.
- Nothing disappears.
- Retractions replace deletions.
- History is preserved.

---

## PROVENANCE

Every analytical claim must trace back to source evidence.
Every source must have provenance.

Every AI-generated statement must include:

- source references
- model identifier
- model version
- prompt/workflow version
- uncertainty explanation
- review status

**No provenance. No claim.**

---

## AI LIMITATIONS

The AI **may**:

- organize
- summarize
- identify patterns
- suggest contradictions
- suggest unknowns
- propose hypotheses

The AI **may NOT**:

- determine guilt
- resolve contradictions
- close unknowns
- create judgments
- fabricate missing evidence
- hide uncertainty

---

## DEVELOPMENT PHILOSOPHY

We are not optimizing for feature count.
We are optimizing for **epistemic integrity**.

- When uncertainty exists, surface it.
- When evidence conflicts, display it.
- When information is missing, represent it explicitly.

---

## WHAT SUCCESS LOOKS LIKE

A detective should never wonder:
*"What evidence supports this?"*

Every claim should answer itself.

- A defense attorney should be able to audit every analytical step.
- A prosecutor should understand exactly how a hypothesis formed.
- A forensic scientist should trust the provenance.
- An engineer should understand why every table exists.

---

## YOUR ROLE

You are not building software.
You are implementing a constitutional system.

Every schema...
Every migration...
Every API...
Every validation rule...
Every database constraint...
Every test...

**Must reinforce the Engineering Constitution.**

If a requested implementation violates the Constitution:

1. stop,
2. explain why,
3. and propose a constitutionally compliant alternative.

Never optimize for convenience at the expense of integrity.
This project values trust above speed.

---

## A NORTH STAR

ARGUS is not software.
ARGUS is an institution.

Every line of code should make the pursuit of truth
more transparent than it was yesterday.

If your implementation makes the system more opaque,
more speculative,
or more difficult to audit,
**it is the wrong implementation.**

- Always choose clarity over cleverness.
- Always choose traceability over convenience.
- Always choose evidence over confidence.
- Always choose integrity over speed.

And the principle that captures all of it:

> **ARGUS is not designed to think instead of investigators.
> It is designed so investigators never have to think alone.**

---

## DOCUMENT LAYERS

This repository is governed through four documentation layers, each grounding the one below it:

```
PROJECT_BRIEF.md            (onboarding — why ARGUS exists)
        ↓
ENGINEERING_CONSTITUTION.md (governance — the laws every change must obey)
        ↓
AGENTS.md                   (behavior — how engineers and AI agents work here)
        ↓
docs/adr/                   (decisions — the architectural record)
        ↓
Implementation
```

Supporting corpora (established by ADR-0008): the [Lexicon](../glossary/LEXICON.md) (canonical vocabulary), the [knowledge corpus](../knowledge/README.md) — [Standards](../knowledge/standards/README.md), [ISS research papers](../knowledge/research/README.md), the [Academy](../knowledge/academy/README.md) — and [Architecture artifacts](../architecture/README.md).

---

## Version history

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-13 | Ratified at repository root commit. |
| 1.1.0 | 2026-07-13 | Added the closing augmentation principle to the North Star; added version header and supporting-corpora references (Founder Resolution 002 / ADR-0008). |
| 1.1.1 | 2026-07-13 | Link paths updated for the knowledge-corpus move (ADR-0012). No semantic change. |
