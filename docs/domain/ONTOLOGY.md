# The ARGUS Ontology

- **Document version:** 1.2.0 — Ratified at 1.0.0 by AGC Review Session 001, 2026-07-13; 1.1.0 added stable identifiers (ADR-0011) and the Verification rung (ADR-0010); 1.2.0 adds ONT-PRN-010 and the Derivation Specification layer (ADR-0013, ADR-0014)
- **Date:** 2026-07-13
- **Governed by:** [Engineering Constitution](../foundation/ENGINEERING_CONSTITUTION.md) 1.0.0, [Lexicon](../glossary/LEXICON.md) 1.0.0, ADR-0009 (Founder Resolution 003)
- **Derived from it:** the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md), [Entity Lifecycles](ENTITY_LIFECYCLES.md), the [Invariant Matrix](INVARIANT_MATRIX.md), and every implementation artifact thereafter

> **The ontology is the source of truth for meaning.**
> Every implementation artifact — database schemas, APIs, user interfaces, AI prompts, documentation, tests, and analytical models — must derive from the ontology rather than defining it independently.
> — Founder Resolution 003

This document is not SQL, not a data model, not an API. It is the vocabulary of reality as understood by ARGUS. SQLAlchemy models, PostgreSQL tables, OpenAPI schemas, and Pydantic models are implementations *of* this ontology. If ARGUS were rebuilt twenty years from now in a different language and database, this document should remain valid. The [Lexicon](../glossary/LEXICON.md) gives each term its canonical one-sentence definition; this document gives the terms their relations and their semantics.

---

## 1. The epistemic frame

**Reality** is the actual state of affairs an investigation seeks to reconstruct. ARGUS never contains reality — only **fragments** of it that survived: photographs, recordings, documents, traces, recollections. Truth is therefore never *generated* inside the system; it is *reconstructed* from fragments, imperfectly, by humans.

Three commitments follow, and everything else in ARGUS derives from them:

1. **The representation is not the thing.** Every object in ARGUS is a record *about* reality, never reality itself. An Entity is not a person; it is the system's handle for referring to one. An EvidenceArtifact is not the crime scene; it is a preserved fragment of it.
2. **Every step away from evidence adds inference.** The further a statement stands from the fragment that grounds it, the more human or machine inference it contains — and the more explicitly that inference must be recorded and the more visibly its uncertainty must travel with it.
3. **What the system does not know is part of what it knows.** Absence of information and conflict between information are objects, not ambient conditions.

## 2. The analytical ladder

The central structure of the ontology is an ordered progression that must never be collapsed:

```
Reality
  ↓  (fragments survive)
Evidence            — EvidenceArtifact, addressed through SourceLocator
  ↓  (+ perception: what does the fragment show?)
Observation
  ↓  (+ inference: what might that mean?)
Interpretation
  ↓  (+ synthesis: what might have happened?)
Hypothesis
  ↓  (+ human comprehension)
Understanding       — lives in the investigator, not in the system
  ↓  (+ human decision)
Human Judgment      — occurs entirely outside ARGUS
```

Each rung differs from its neighbors **in kind, not in degree**:

- An **Observation** is perceptual: it states what an addressed region of evidence shows, and nothing more. "The receipt is timestamped 23:41" is an observation. "He was there late at night" is not.
- An **Interpretation** is inferential: it assigns meaning to observations and must say *why*. Meaning enters the system here, and only here, for the first time — explicitly labeled as inference, carrying its uncertainty.
- A **Hypothesis** is synthetic: a candidate account of what happened, composed from interpretations, stated so that evidence could strengthen or weaken it. Hypotheses coexist; the ontology has no concept of a *winning* hypothesis.
- **Understanding** and **Judgment** are human. They have no object representation because representing them would invite the system to compute them. ARGUS stops at Hypothesis.

**The one-rung rule.** A record on any rung refers downward only to the rung directly beneath it. This is an ontological commitment, not a storage convention: skipping a rung would smuggle unexamined inference past the ladder, which is precisely how certainty comes to exceed evidence.

## 3. The negative space: Unknowns and Contradictions

Most systems represent only what is known. ARGUS represents the *shape of the gaps*:

- An **Unknown** is a formally recognized gap in current understanding — a question, standing as an object, connected (via **UnknownLink**) to every claim, entity, and hypothesis it undermines or conditions. An unanswered question that touches a hypothesis is part of that hypothesis's epistemic status.
- A **Contradiction** is a formally recognized incompatibility between analytical claims, its participants bound in explicitly (via **ContradictionMember**). Conflict is preserved and displayed, never averaged away.

Both share one ontological property: **they demand human disposition and cannot dispose of themselves.** No machine process resolves a contradiction or closes an unknown, because doing either is an act of judgment. An Unknown's disposition is itself a first-class object (**UnknownResolution**) — the answer to "how did we come to stop not-knowing this?" is evidence-grade information.

## 4. The world model: Entities and Relationships

Investigations are about people, places, and things. The ontology represents them cautiously:

- An **Entity** is a *referent handle* — a stable way to say "that person," "that vehicle" — and deliberately not a dossier. Everything substantive known about an entity (a name, a birthdate, a plate number) is a **claim on the ladder** that references the entity, carrying provenance like any other claim. An attribute stored on an entity without a source would be an ungrounded assertion wearing the costume of a fact.
- A **Relationship** is a typed, evidence-grounded connection between two entities. Edges in the case graph are claims too: no grounding, no edge.
- Whether two handles denote the same real-world referent is a **human determination**. The system may surface similarity; it may never merge identities on its own.

## 5. Actors and agency

Three kinds of agency exist in ARGUS, and the ontology keeps them distinct:

- The **HumanActor** — the investigator, the Steward. The only agency permitted to make consequential state transitions: accepting or rejecting proposals, resolving contradictions, closing unknowns, retracting records, transitioning cases.
- The **AIWorkflow** — the Telescope. A versioned instrument that organizes, summarizes, surfaces patterns, and proposes — always producing *proposals* that carry full provenance (model, version, workflow, uncertainty explanation) and await human review. An unreviewed AI statement is ontologically a suggestion, never a finding.
- The **SystemProcess** — mechanism, not mind. Ingestion, verification, reconciliation: permitted only mechanical operations whose correctness is checkable, never operations whose correctness is a matter of judgment.

## 6. Memory and accountability

- **Nothing disappears.** The past states of the investigation are part of the investigation. Corrections happen by **Retraction** — superseding a record while preserving it — never by deletion or in-place edit. A claim whose grounding was retracted is *flagged as degraded*, visibly, for human disposition; it does not silently vanish, and it is not silently kept.
- **Every claim explains itself.** **Provenance** is not metadata attached to knowledge; it is a condition of a statement *being* knowledge in this system. No provenance, no claim.
- **Every material act is witnessed.** The **AuditEntry** is the ontology's memory of agency: who did what, to which record, when, under what authority. The audit trail is append-only even against administrators, because a transparency mechanism that the powerful can edit is not one.

## 7. The fourteen first-class objects

The complete object vocabulary with stable identifiers (per ADR-0011; canonical definitions in the [Lexicon](../glossary/LEXICON.md); structure in the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md)). This table is the authoritative object-identifier registry:

| ID | Object | Grouping | Ontological role |
|---|---|---|---|
| ONT-CAS-001 | Case | Context | The bounded investigative world and its legal authority |
| ONT-EVA-001 | EvidenceArtifact | Evidence | A preserved fragment of reality |
| ONT-SRC-001 | SourceLocator | Evidence | A precise address into an artifact |
| ONT-OBS-001 | Observation | The ladder | Perception: what the evidence shows |
| ONT-INT-001 | Interpretation | The ladder | Inference: what it may mean |
| ONT-HYP-001 | Hypothesis | The ladder | Synthesis: what may have happened |
| ONT-UNK-001 | Unknown | Negative space | A recognized gap, standing as an object |
| ONT-UNL-001 | UnknownLink | Negative space | What a gap touches |
| ONT-UNR-001 | UnknownResolution | Negative space | The human record of a gap's disposition |
| ONT-CON-001 | Contradiction | Negative space | A recognized conflict, standing as an object |
| ONT-CNM-001 | ContradictionMember | Negative space | A claim's part in a conflict |
| ONT-ENT-001 | Entity | World model | A referent handle, not a dossier |
| ONT-REL-001 | Relationship | World model | An evidence-grounded connection |
| ONT-AUD-001 | AuditEntry | Accountability | The witnessed history of a material act |

## 8. Derivation rule

Per Founder Resolutions 003 and 004, the derivation order is one-directional and now extends through verification:

```
ONTOLOGY.md
  → DERIVATION_SPECIFICATION.md      (translation: ontological rule → engineering obligations)
  → DOMAIN_SCHEMA_SPECIFICATION.md   (structure: attributes, references, invariants)
  → ENTITY_LIFECYCLES.md             (state machines and permitted transitions)
  → INVARIANT_MATRIX.md              (per-entity enforcement specification)
  → implementation                   (schemas, APIs, UIs, prompts)
  → verification                     (tests proving conformance to ontological rules)
  → operation
```

**Verification is derived from ontology, not from implementation** (Resolution 004 / ADR-0010): every domain-protecting test declares, by stable identifier, which ontological rule it protects. A test that cannot name its rule is either infrastructure plumbing or evidence of an undocumented rule — and undocumented rules are fixed here first.

A conflict between an implementation artifact and this document is a defect in the artifact. A needed change of *meaning* is made here first — under Governance Council review and a MAJOR version change — and only then propagated downward. This methodology is named **Ontology-Driven Engineering (ODE)**: the ontology defines meaning, the schema defines structure, implementation realizes behavior, and verification proves conformance (research treatment planned as ISS-0005).

## 9. Stable principle identifiers (ONT-PRN registry)

Cross-cutting principles carry stable identifiers alongside the object registry in §7 (scheme and immutability rules: ADR-0011). Identifiers never change meaning and are never reused; wording may evolve under versioning, the ID does not.

| ID | Principle | Anchored in |
|---|---|---|
| ONT-PRN-001 | The representation is not the thing | §1 |
| ONT-PRN-002 | Every step away from evidence adds inference | §1, §2 |
| ONT-PRN-003 | What the system does not know is part of what it knows | §1, §3 |
| ONT-PRN-004 | The one-rung rule: ladder references climb exactly one rung | §2 |
| ONT-PRN-005 | No provenance, no claim | §6 |
| ONT-PRN-006 | Nothing disappears: retraction replaces deletion | §6 |
| ONT-PRN-007 | Human judgment is final and external | §2, §5 |
| ONT-PRN-008 | The ontology is the source of truth for meaning (Resolution 003) | §8 |
| ONT-PRN-009 | Verification is derived from ontology (Resolution 004) | §8 |
| ONT-PRN-010 | Implementation must remain replaceable: no implementation artifact may become more authoritative than the ontology it derives from (Resolution 005) | §8 |

## 10. Unresolved ontological questions

- **The nature of uncertainty.** Uncertainty is mandatory on inferential claims, but its representation (prose, vocabulary, scale) is unsettled; a scale invites false precision (Article IX). Requires ISS-0003 before schematization.
- **Identity of entities.** When are two handles the same referent? Human-determined in v0.1; any future assistance must not transfer the determination to a machine.
- **Cross-case reality.** Reality is not case-shaped; evidence and people span cases. Reconciling that with authority-scoped access (Article VI) is open.
- **Working thought.** Investigators think in drafts that are not yet claims. The ontology deliberately excludes working notes rather than model them badly; unmodeled is honest, badly modeled is dangerous.

## Ratification record (AGC Review Session 001, 2026-07-13)

- [x] Constitutional Review — **PASS** ("no document has become more authoritative than the Constitution; the hierarchy is clean")
- [x] Domain Review — **PASS** (Founder Resolution 003 identified as the philosophical bridge preventing database-first design)
- [x] Architectural Review — **PASS with one new directive**: the derivation chain must extend to Verification (Founder Resolution 004 → ADR-0010)

Additional function verdicts from the session: Research Review Board — PASS; Standards Committee — PASS with one request: stable ontology identifiers (→ ADR-0011).

Ratified as one constitutional package with the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md) and [Entity Lifecycles](ENTITY_LIFECYCLES.md).

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft, extracted as the meaning layer above the Domain Schema Specification per ADR-0009 / Founder Resolution 003. |
| 1.0.0 | 2026-07-13 | Ratified by AGC Review Session 001. |
| 1.1.0 | 2026-07-13 | Added stable identifier registries for objects (§7) and principles (§9) per ADR-0011; extended the derivation chain through Verification and Operation and named Ontology-Driven Engineering per ADR-0010 / Founder Resolution 004. |
| 1.2.0 | 2026-07-13 | Added ONT-PRN-010 (implementation replaceability, Resolution 005 / ADR-0013) and inserted the Derivation Specification into the derivation chain (ADR-0014), per AGC Review Session 002. |
