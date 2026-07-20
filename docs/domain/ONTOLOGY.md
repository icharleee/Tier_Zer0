# The ARGUS Ontology

- **Document version:** 1.18.0 — Ratified at 1.0.0 by AGC Review Session 001, 2026-07-13; subsequent minor versions add stable identifiers and principles through ONT-PRN-030 and the fifteenth object ONT-CDP-001 (see version history)
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

The negative space has structure — these are **boundary objects**, and their symmetry is deliberate: *Unknown bounds Interpretation* (it limits meaning); *Contradiction bounds Hypothesis* (it limits explanation). Different limits, kept separate forever (ADR-0024). Both share one ontological property: **they demand human disposition and cannot dispose of themselves.**

**Boundary taxonomy (normative, ADR-0026):**

| Object | Bounds | Alters automatically? |
|---|---|---|
| Unknown | Interpretation | **Never** |
| Contradiction | Hypothesis | **Never** |

The last column records one of ARGUS's deepest invariants: **boundary objects constrain reasoning; they never rewrite it.** A boundary that mutated what it bounds would be adjudication — which belongs to humans (Article II, ONT-PRN-020). No machine process resolves a contradiction or closes an unknown, because doing either is an act of judgment. An Unknown's disposition is itself a first-class object (**UnknownResolution**) — the answer to "how did we come to stop not-knowing this?" is evidence-grade information.

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
| ONT-SRC-001 | SourceLocator | Evidence | The scope of constitutional support: the smallest evidentiary region required to justify an Observation (Resolution 011) |
| ONT-OBS-001 | Observation | The ladder | Perception: what the evidence shows |
| ONT-INT-001 | Interpretation | The ladder | Inference: what it may mean |
| ONT-HYP-001 | Hypothesis | The ladder | Synthesis: what may have happened |
| ONT-UNK-001 | Unknown | Negative space | A recognized gap, standing as an object |
| ONT-UNL-001 | UnknownLink | Negative space | What a gap touches |
| ONT-UNR-001 | UnknownResolution | Negative space | The human record of a gap's disposition |
| ONT-CON-001 | Contradiction | Negative space | A formally scoped joint incompatibility, standing as an object |
| ONT-CNM-001 | ContradictionMember | Negative space | A claim's part in a conflict (snapshot at recognition) |
| ONT-CDP-001 | ContradictionDisposition | Negative space | The human record of how a conflict was disposed — never of which claim reality favors (ADR-0027) |
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
| ONT-PRN-011 | Implementation is the primary source of architectural feedback: it discovers missing ontology; it never defines meaning (Resolution 006) | §8 |
| ONT-PRN-012 | Every constitutional transition is explicit: an audit event, a responsible actor, a timestamp, an allowed predecessor state — no invisible state changes (Resolution 007) | §6 |
| ONT-PRN-013 | Authoritative lifecycle definitions exist exactly once: renderings in code and database derive from one specification and never diverge silently (Resolution 008) | §8 |
| ONT-PRN-014 | Eligibility determines whether an artifact may participate in reasoning; sufficiency determines what reasoning it can support — never collapsed (Resolution 009) | §2, §6 |
| ONT-PRN-015 | Independent derivations are triangulated whenever practical: normative specification, executable implementation, independent verification — no implementation verified only against itself (Resolution 010) | §8 |
| ONT-PRN-016 | A SourceLocator defines the exact scope of evidence upon which an Observation constitutionally depends — the smallest region required to justify it (Resolution 011) | §2, §4 |
| ONT-PRN-017 | Persistence implements admissibility, not defines it: the ontology determines what may exist; persistence ensures those conditions cannot be bypassed (Resolution 012) | §8 |
| ONT-PRN-018 | Epistemic layers reject semantic contamination from higher layers: no layer carries the vocabulary of the layers above it (Resolution 013) | §2 |
| ONT-PRN-019 | Higher epistemic layers may introduce new obligations but may never weaken the obligations inherited from lower layers — the ladder only accumulates (Resolution 014) | §2 |
| ONT-PRN-020 | Unknowns represent the boundaries of current knowledge, never placeholders for future assumptions — absence is never transformed into evidence, inference, or implied support (Resolution 015) | §3 |
| ONT-PRN-021 | Every epistemic object distinguishes the relationships that justify its existence from the relationships that limit its validity — the two families never merge or convert (Resolution 016) | §2, §3 |
| ONT-PRN-022 | Every new epistemic layer expands the dimensions through which reality may be represented, rather than merely increasing the number of representable objects (Resolution 017) | §2, §3 |
| ONT-PRN-023 | An explanation is constitutionally admissible only when the system can state what supports it, what limits it, what could challenge it, and what remains unknown (Resolution 018) | §2, §3 |
| ONT-PRN-024 | No new epistemic object or capability may be implemented until the ontology defines the constraints, refusal conditions, provenance obligations, validity boundaries, and non-effects that limit its expressive power (Resolution 019) | §8 |
| ONT-PRN-025 | Historical articulation and current derived condition are represented separately whenever later events can change the present state without invalidating what was true at creation (Resolution 020) | §2, §6 |
| ONT-PRN-026 | Reconciliation may identify divergence between representations, but it must never convert representational agreement into evidentiary truth or representational disagreement into epistemic falsity (Resolution 021) | §1, §6 |
| ONT-PRN-027 | No reconciliation operation may silently repair constitutional history: detection, proposed remediation, and authorized mutation remain separate operations (Resolution 022) | §5, §6 |
| ONT-PRN-028 | Identity is authenticated, never asserted: the actor attributed to a constitutional action derives from an authenticated principal context and is never determined by caller payload; authentication establishes attribution only — no authority, access, credibility, or epistemic standing (Resolution 023) | §5, §6 |
| ONT-PRN-029 | Authority governs permitted actions and visibility, never epistemic standing: granting or denying authority does not change the meaning, admissibility, credibility, or truth status of any constitutional record (Resolution 024) | §5, §6 |
| ONT-PRN-030 | Access to protected information is explicit, least-privileged, attributable, and auditable; absence of access is never represented as absence of evidence (Resolution 025) | §5, §6 |

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
| 1.3.0 | 2026-07-13 | Added ONT-PRN-011 (implementation as primary architectural feedback, Resolution 006 / ADR-0015), per AGC Review Session 003. |
| 1.4.0 | 2026-07-13 | Added ONT-PRN-012 (every constitutional transition is explicit, Resolution 007 / ADR-0007), per AGC Review Session 004. |
| 1.5.0 | 2026-07-13 | Added ONT-PRN-013 (single-source lifecycle definitions, Resolution 008 / ADR-0017), per AGC Review Session 005. |
| 1.6.0 | 2026-07-13 | Added ONT-PRN-014 (eligibility vs. sufficiency, Resolution 009 / ADR-0018), per the Slice 1C plan review. |
| 1.7.0 | 2026-07-13 | Added ONT-PRN-015 (triangulated derivations, Resolution 010 / ADR-0019), per AGC Review Session 007. |
| 1.8.0 | 2026-07-13 | Added ONT-PRN-016 and refined the ONT-SRC-001 role to scope-of-constitutional-support (Resolution 011 / ADR-0020), per the Slice 1D plan review. |
| 1.9.0 | 2026-07-13 | Added ONT-PRN-017 (persistence implements admissibility, Resolution 012 / ADR-0021) and ONT-PRN-018 (semantic contamination, Resolution 013 / ADR-0022), per AGC Review Session 006. |
| 1.10.0 | 2026-07-13 | Added ONT-PRN-019 (accumulating obligations, Resolution 014 / ADR-0023) and ONT-PRN-020 (Unknowns as epistemic boundaries, Resolution 015 / ADR-0024); boundary-object symmetry recorded in §3, per AGC Review Session 007. |
| 1.11.0 | 2026-07-13 | Added ONT-PRN-021 (existence vs. validity-boundary relationships, Resolution 016 / ADR-0025), per AGC Review Session 008. |
| 1.12.0 | 2026-07-13 | Added ONT-PRN-022 (dimensions over objects, Resolution 017 / ADR-0026) and the normative boundary taxonomy with the never-alters invariant, per AGC Review Session 009. |
| 1.13.0 | 2026-07-13 | Added ONT-CDP-001 (ContradictionDisposition, the fifteenth first-class object, ADR-0027); Contradiction's role refined to formally scoped joint incompatibility, per AGC Review Session 010. |
| 1.14.0 | 2026-07-13 | Added ONT-PRN-023 (an explanation must state what supports, limits, challenges, and escapes it — the governing principle for the Hypothesis layer, Resolution 018 / ADR-0028), per AGC Review Session 011. |
| 1.15.0 | 2026-07-13 | Added ONT-PRN-024 (constraint precedes expressive power, Resolution 019 / ADR-0029) and ONT-PRN-025 (historical articulation vs. current derived condition, Resolution 020 / ADR-0030), per AGC Review Session 013. |
| 1.16.0 | 2026-07-13 | Added ONT-PRN-026 (representational agreement is never evidentiary truth, Resolution 021 / ADR-0031) and ONT-PRN-027 (no silent repair — detect ≠ decide ≠ mutate, Resolution 022 / ADR-0032), per AGC Review Session 015. |
| 1.17.0 | 2026-07-13 | Added ONT-PRN-028 (identity is authenticated, never asserted; attribution only, Resolution 023 / ADR-0033), per AGC Review Session 018. |
| 1.18.0 | 2026-07-13 | Added ONT-PRN-029 (authority governs actions and visibility, never epistemic standing, Resolution 024 / ADR-0034) and ONT-PRN-030 (protected access is explicit, least-privileged, attributable, auditable; absence of access ≠ absence of evidence, Resolution 025 / ADR-0035), per AGC Review Session 019. |
