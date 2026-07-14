# ARGUS Derivation Specification

- **Document version:** 1.3.0 — Ratified at 1.0.0 by AGC Review Session 003, 2026-07-13; 1.1.0 aligned ONT-EVA-001 with ADR-0007 as amended; 1.2.0 added ADR-0016 chain obligations; 1.3.0 adds the constitutional-predicate gate to ONT-OBS-001 (ADR-0018)
- **Date:** 2026-07-13
- **Established by:** [ADR-0014](../adr/0014-establish-the-derivation-specification-layer.md) (AGC Review Session 002)
- **Derived from:** [The ARGUS Ontology](ONTOLOGY.md) 1.2.0
- **Consumed by:** the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md), [Entity Lifecycles](ENTITY_LIFECYCLES.md), the [Invariant Matrix](INVARIANT_MATRIX.md), implementation, and verification

This document is the bridge between philosophy and engineering: for every ontological object, it states the engineering obligations that object's rules generate — required schema properties, invariants, audit events, API behavior, and tests. Downstream artifacts instantiate these obligations; the Invariant Matrix records their enforcement almost mechanically.

**Method.** Obligations are stated with MUST/MUST NOT and cite stable identifiers (ADR-0011). This document does not restate structural detail — attribute lists, address grammars, state tables live in the [Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md) and [Entity Lifecycles](ENTITY_LIFECYCLES.md); this document states what any faithful structure *must contain and enforce*, technology-free (ONT-PRN-010: all implementations are replaceable). Where this document and a lower document disagree, this document prevails and the lower document is corrected (ADR-0014).

---

## Part I — Cross-cutting derivations

These obligations derive from the principle registry and apply to every object in the class named; per-object sections below add only object-specific obligations and do not repeat these.

### D-PRN-004 — The one-rung rule (from ONT-PRN-004)

Applies to: ONT-OBS-001, ONT-INT-001, ONT-HYP-001.

- **Schema:** each ladder claim MUST hold references only to the rung directly beneath it; reference sets MUST be non-empty at creation and immutable thereafter.
- **Invariants:** level-skipping references MUST be unrepresentable, not merely rejected.
- **API:** no endpoint may accept, create, or return a level-skipping reference; no convenience endpoint may create a higher rung directly from evidence.
- **Tests:** for each rung, a test MUST prove creation fails without the required lower-rung references, and a test MUST prove a level-skipping reference is impossible. Cite ONT-PRN-004 plus the object ID.

### D-PRN-005 — No provenance, no claim (from ONT-PRN-005)

Applies to: ONT-OBS-001, ONT-INT-001, ONT-HYP-001, ONT-REL-001, and every AI-created record of any type.

- **Schema:** provenance fields (spec C7) MUST be required and non-defaultable; AI records MUST additionally carry model identifier, model version, prompt/workflow version, uncertainty explanation, and review status.
- **Invariants:** provenance fields are immutable after write; writes lacking them MUST fail at the persistence boundary.
- **Audit:** the creation event MUST capture the creating actor and, for AI, the version triplet.
- **API:** creation endpoints MUST reject provenance-free payloads with an explicit constitutional error, and exports MUST include full provenance.
- **Tests:** one test per record type proving a provenance-free write fails at the persistence boundary (not only at the API). Cite ONT-PRN-005.

### D-PRN-006 — Nothing disappears (from ONT-PRN-006)

Applies to every class-V object (spec C5/C6): ONT-SRC-001, ONT-OBS-001, ONT-INT-001, ONT-HYP-001, ONT-UNL-001, ONT-ENT-001, ONT-REL-001, and V-classed fields of ONT-CON-001 / ONT-UNK-001.

- **Schema:** retraction fields (retracted_at, retracting actor, required reason, optional superseded_by) MUST exist; no UPDATE path for substantive content and no DELETE path at all.
- **Invariants:** retraction is terminal and human-only; default reads exclude retracted records but MUST NOT conceal their existence.
- **Audit:** every retraction MUST emit its event with the reason.
- **API:** no endpoint may edit substantive content in place or hard-delete; retraction endpoints MUST require a reason.
- **Tests:** per object, a test MUST prove in-place mutation and deletion fail at the database layer, and retraction preserves the original readable. Cite ONT-PRN-006 plus the object ID.

### D-PRN-007 — Human judgment is final (from ONT-PRN-007)

Applies to every consequential state transition: case transitions, retractions, review-status changes, contradiction and unknown dispositions, sealing, entity supersession.

- **Schema:** transition records MUST attribute an authenticated HumanActor; actor-class MUST be structurally checkable.
- **Invariants:** no AIWorkflow or SystemProcess path may execute these transitions (SystemProcess exceptions are exactly those the Schema Specification enumerates as mechanical, e.g. artifact activation).
- **API:** transition endpoints MUST require human authentication and authorization context (Article VI).
- **Tests:** per transition, a test MUST prove the transition fails for non-human actors. Cite ONT-PRN-007 plus the object ID.

### D-AUD — Atomic audit (from ONT-AUD-001 semantics)

Applies to every material mutation of every object.

- **Schema/Invariants:** the audit entry MUST be committed in the same transaction as the mutation; an unaudited material mutation and an audit entry for a non-occurred mutation MUST both be impossible.
- **Tests:** a test MUST prove a forced failure between mutation and audit write rolls back both. Cite ONT-AUD-001.

---

## Part II — Per-object derivations

### ONT-CAS-001 — Case

- **Schema properties:** legal authority basis required at creation and versioned; responsible HumanActor; status; every non-Case record MUST carry exactly one Case reference (spec C3).
- **Invariants:** no deletion path; CLOSED freezes analytical writes without concealing anything; authority changes append, never overwrite.
- **Audit events:** created; every status transition with reason; authority superseded; classification changed; reopened ([Lifecycles §1](ENTITY_LIFECYCLES.md#1-case-ct)).
- **API behavior:** all data access MUST be case-scoped and authority-checked before any read or write (Article VI); no cross-case query surface in v0.1.
- **Required tests:** creation without authority basis fails; analytical write into a CLOSED case fails; every transition audits. Cite ONT-CAS-001.

### ONT-EVA-001 — EvidenceArtifact

- **Schema properties:** original content hash (algorithm + digest) and ingestion record, both content-immutable; status; acquisition description; storage reference explicitly non-authoritative (identity MUST NOT depend on a provider URI).
- **Invariants:** no mutation path for content bytes or original hash at any layer, including administrative; pre-`ACTIVE` records (`PENDING_VERIFICATION`, `QUARANTINED`) invisible to analysis; analytically used technical metadata MUST enter as Observations, never as bare attributes.
- **Audit events:** ingested; activated; quarantined; reactivated; retracted; sealed/unsealed; every sealed-content read; storage re-homed ([Lifecycles §2](ENTITY_LIFECYCLES.md#2-evidenceartifact-ci-content-ct-operational-fields)).
- **API behavior:** content reads MUST verify against the original hash; sealed content MUST require elevated authorization and audit each read; activation is SystemProcess-only upon verification (protocol: ADR-0007).
- **Required tests:** content/hash mutation fails at the database layer; a SourceLocator against a non-ACTIVE artifact fails; hash mismatch on read is surfaced, never silently served. Cite ONT-EVA-001, ONT-PRN-001.

### ONT-SRC-001 — SourceLocator

- **Schema properties:** exactly one owning artifact; scheme + address payload immutable after creation; human-readable excerpt non-authoritative.
- **Invariants:** address MUST resolve within artifact bounds at creation; retargeting impossible; owning-artifact retraction/sealing raises a downstream flag rather than transitioning the locator.
- **Audit events:** created; retracted; downstream-flag raised ([Lifecycles §3](ENTITY_LIFECYCLES.md#3-sourcelocator-v)).
- **API behavior:** creation validates bounds against actual artifact content; responses MUST carry the owning artifact's status so degraded grounding is always visible.
- **Required tests:** out-of-bounds and non-ACTIVE-artifact creation fail; artifact retraction flags dependent locators. Cite ONT-SRC-001.

### ONT-OBS-001 — Observation

- **Schema properties:** statement; ≥1 SourceLocator reference; method description required for human and AI creators alike (Article III); event time distinct from record time (spec C4).
- **Invariants:** an Observation whose every locator is retracted MUST be flagged ungrounded and surfaced — never auto-retracted.
- **Audit events:** created; retracted; review transition; ungrounded-flag raised ([Lifecycles §4–6](ENTITY_LIFECYCLES.md#46-observation-interpretation-hypothesis-v)).
- **API behavior:** creation MUST reject empty statements and missing method; unreviewed AI observations MUST be visibly marked in every representation; creation MUST be gated by the `can_support_observation` constitutional predicate ([CONSTITUTIONAL_PREDICATES.md](CONSTITUTIONAL_PREDICATES.md), ADR-0018) — derived never stored, rendered independently in Python and PostgreSQL, refusals explained by canonical reason codes.
- **Required tests:** `test_observation_requires_source_locator` (the canonical ADR-0010 example) and the D-PRN cross-cutting set. Cite ONT-OBS-001, ONT-PRN-004.

### ONT-INT-001 — Interpretation

- **Schema properties:** meaning statement; ≥1 Observation reference; reasoning description; **mandatory** uncertainty expression (Article IX).
- **Invariants:** no "primary interpretation" concept anywhere — schema, API, or UI (ONT-PRN-002; Article IV); competing interpretations coexist without rank.
- **Audit events:** created; retracted; review transition; grounding-flag raised.
- **API behavior:** creation MUST reject empty uncertainty expressions; listings MUST NOT order by any stored preference.
- **Required tests:** creation without uncertainty fails; the schema exposes no ranking field to set. Cite ONT-INT-001, ONT-PRN-002.

### ONT-HYP-001 — Hypothesis

- **Schema properties:** narrative; ≥1 Interpretation reference; reasoning; **testability statement** (what would strengthen or weaken it — Article VII); uncertainty expression.
- **Invariants:** no terminal confirmed/true state exists to reach; no "leading hypothesis" field; competing hypotheses structurally unprivileged.
- **Audit events:** created; retracted; review transition; grounding-flag raised.
- **API behavior:** no endpoint may promote, rank, confirm, or auto-close a hypothesis; open Unknowns and Contradictions touching a hypothesis MUST be retrievable with it (Article IX).
- **Required tests:** creation without a testability statement fails; no confirmation transition exists (attempted transition fails structurally). Cite ONT-HYP-001, ONT-PRN-007.

### ONT-UNK-001 — Unknown

- **Schema properties:** question stated as a question; status derived from the existence and type of its UnknownResolution — never independently settable.
- **Invariants:** no AI or system disposition path exists; a bare status flip without a resolution record MUST be impossible.
- **Audit events:** created/suggested; linked/unlinked; disposed (via resolution); review transition ([Lifecycles §9](ENTITY_LIFECYCLES.md#9-unknown-v-question-text-terminal-disposition-via-unknownresolution)).
- **API behavior:** "what don't we know?" MUST be a first-class case query; disposition endpoints accept only UnknownResolution creation by humans.
- **Required tests:** status flip without resolution fails; AI disposition fails. Cite ONT-UNK-001, ONT-PRN-003, ONT-PRN-007.

### ONT-UNL-001 — UnknownLink

- **Schema properties:** owning Unknown; same-case target; nature of dependency.
- **Invariants:** cross-case links impossible; duplicates (same unknown, target, nature) rejected.
- **Audit events:** created; retracted.
- **API behavior:** records retrieved through any read surface MUST be able to expose the open Unknowns linked to them.
- **Required tests:** cross-case link fails; linked Unknowns are queryable from the target side. Cite ONT-UNL-001.

### ONT-UNR-001 — UnknownResolution

- **Schema properties:** resolution type (ANSWERED / WITHDRAWN / UNRESOLVABLE); rationale; resolving HumanActor; ANSWERED MUST reference ≥1 answering claim.
- **Invariants:** content-immutable; author structurally human-only; ANSWERED without claim references fails (an answer without evidence is not an answer — Article I).
- **Audit events:** created; superseded ([Lifecycles §11](ENTITY_LIFECYCLES.md#11-unknownresolution-ci)).
- **API behavior:** supersession creates a successor record and reopens the question as a new Unknown; no edit endpoint exists.
- **Required tests:** AI/system authorship fails; ANSWERED without claims fails. Cite ONT-UNR-001, ONT-PRN-007.

### ONT-CON-001 — Contradiction

- **Schema properties:** incompatibility description; ≥2 members at all times; disposition rationale required on resolution.
- **Invariants:** resolution and withdrawal human-only and terminal; resolution never retracts the conflicting claims; member retraction raises a flag, never auto-resolves.
- **Audit events:** created/suggested; member added; resolved; withdrawn; member-retracted flag; review transition ([Lifecycles §7](ENTITY_LIFECYCLES.md#7-contradiction-v-description-terminal-disposition)).
- **API behavior:** "what conflicts?" MUST be a first-class case query; open contradictions touching any claim MUST be visible wherever that claim is displayed.
- **Required tests:** creation with <2 members fails; AI resolution fails; resolving preserves both claims. Cite ONT-CON-001, ONT-PRN-003, ONT-PRN-007.

### ONT-CNM-001 — ContradictionMember

- **Schema properties:** owning Contradiction; exactly one same-case claim reference; role in the conflict.
- **Invariants:** content-immutable; never removed or retargeted; a claim may belong to many contradictions.
- **Audit events:** member-added (on the owning Contradiction).
- **API behavior:** membership is queryable from both directions (contradiction → claims, claim → contradictions).
- **Required tests:** member deletion/retargeting fails; membership count below 2 unreachable. Cite ONT-CNM-001.

### ONT-ENT-001 — Entity

- **Schema properties:** entity class (immutable); working designation explicitly non-evidentiary and controlled-transition; **no descriptive-fact attributes** — names, dates, plates enter as claims referencing the entity.
- **Invariants:** no auto-merge or system identity resolution exists; duplicates resolved by human retract-and-supersede with linkage.
- **Audit events:** created; retracted/superseded; designation changed; review transition ([Lifecycles §12](ENTITY_LIFECYCLES.md#12-entity-v-designation-ct)).
- **API behavior:** entity reads MUST present descriptive facts as the sourced claims they are, with provenance, never as flat attributes (ONT-PRN-001).
- **Required tests:** storing a descriptive fact as a bare attribute is structurally impossible; system-initiated merge fails. Cite ONT-ENT-001, ONT-PRN-001, ONT-PRN-007.

### ONT-REL-001 — Relationship

- **Schema properties:** two same-case endpoints; type; directionality; ≥1 grounding claim; uncertainty expression; optional event-time validity.
- **Invariants:** groundless edges unrepresentable; grounding degradation flags, never auto-retracts; multiple typed edges between one pair coexist.
- **Audit events:** created; retracted; review transition; grounding-flag raised.
- **API behavior:** graph queries MUST carry grounding and uncertainty with every edge returned — no bare adjacency surface.
- **Required tests:** groundless creation fails; returned edges include grounding references. Cite ONT-REL-001, ONT-PRN-005.

### ONT-AUD-001 — AuditEntry

- **Schema properties:** actor (with AI version fields where applicable); action type; target reference(s); outcome (rejections audited too); strictly monotonic per-case ordering rooted in a per-case audit head; hash-chain fields per ADR-0016 (`chain_version`, `canonical_payload` derived exactly once at insertion, `previous_event_hash`, `event_hash`), all immutable.
- **Invariants:** the strongest immutability in the system — no create/update/delete path for any actor including administrators; corrections are compensating entries; ordering gaps detectable.
- **Audit events:** not applicable (compensating-entry mechanism).
- **API behavior:** the audit trail MUST be readable end-to-end by an authorized external auditor without internal tooling (Article VIII); sealed-material reads appear in it; a chain-verification operation MUST report sequence continuity, hash linkage, and recomputed-hash validity (tamper-evident within the trust boundary — ADR-0016).
- **Required tests:** direct write/update/delete fails for the application role at the database layer; the D-AUD atomicity test; gap detection works; chain verification passes on valid appends and identifies deliberately corrupted rows. Cite ONT-AUD-001.

---

## Ratification record (AGC Review Session 003, 2026-07-13)

- [x] Ratified to 1.0.0 by Chief Architect executive decision, with the stated rationale: *"I no longer think it needs to become more complete. I think it now needs to become tested."*

Under the vertical-slice strategy (ADR-0015), the [Invariant Matrix](INVARIANT_MATRIX.md) instantiates these obligations incrementally — the rows for a slice's entities exist before that slice's code.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft per ADR-0014 (AGC Review Session 002). |
| 1.0.0 | 2026-07-13 | Ratified by AGC Review Session 003. |
| 1.1.0 | 2026-07-13 | ONT-EVA-001 derivation aligned with the explicit lifecycle of ADR-0007 as amended by AGC Session 004. |
| 1.2.0 | 2026-07-13 | ONT-AUD-001 obligations extended with the ADR-0016 hash chain (head-rooted ordering, immutable chain fields, verification). |
| 1.3.0 | 2026-07-13 | ONT-OBS-001 creation gated by the can_support_observation constitutional predicate (ADR-0018 / Resolution 009). |
