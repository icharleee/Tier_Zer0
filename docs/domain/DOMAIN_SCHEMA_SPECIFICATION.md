# ARGUS Domain Schema Specification

- **Document version:** 1.5.0 — Ratified at 1.0.0 by AGC Review Session 001, 2026-07-13; 1.5.0 refines ONT-CON-001/ONT-CNM-001 and adds ONT-CDP-001 per the Slice 2C amendments (see version history)
- **Date:** 2026-07-13
- **Governed by:** [Engineering Constitution](../foundation/ENGINEERING_CONSTITUTION.md) 1.0.0, [Lexicon](../glossary/LEXICON.md) 1.0.0, ADR-0001–0006, ADR-0009
- **Derived from:** [The ARGUS Ontology](ONTOLOGY.md) — the source of truth for meaning (Founder Resolution 003)
- **Consumed by:** [Entity Lifecycles](ENTITY_LIFECYCLES.md), the [Invariant Matrix](INVARIANT_MATRIX.md), the ERD (`docs/architecture/`), Task 001 (scaffold), Task 002 (domain implementation)

## Purpose and non-goals

This document is the **structural contract** derived from the [Ontology](ONTOLOGY.md): for each first-class object, the attributes, references, invariants, actors, and provenance obligations every implementation must faithfully represent. The Ontology defines what these objects *mean*; this document defines what a faithful representation of them must *contain and enforce*. It is the contract that Task 002 implements.

It deliberately contains **no** SQLAlchemy models, SQL DDL, table names, column types, or serialization formats. Those are implementation renderings of this specification, governed by ADR-0006 and verified against the Domain Invariant Matrix.

**Normative language:** MUST / MUST NOT / SHOULD / MAY are used in their conventional (RFC 2119) sense. All entity and epistemic terms carry their Lexicon definitions.

---

## Part I — Shared conventions

These conventions apply to every entity below unless the entity's own section says otherwise. Entity sections do not restate them.

### C1. Actors

Three actor classes may cause changes in ARGUS:

- **HumanActor** — an authenticated, authorized person. The only class permitted to make consequential state transitions (Article II).
- **AIWorkflow** — a versioned AI process (model identifier + model version + prompt/workflow version). May only create *proposals*: records whose review status is `UNREVIEWED`.
- **SystemProcess** — a named automated process (ingestion, integrity verification, reconciliation). May only perform the mechanical operations this specification explicitly grants it.

Every record and every audit event attributes its causing actor. Anonymous writes MUST be impossible.

### C2. Identity

Every record has a globally unique, stable, opaque identifier assigned at creation and never reused, recycled, or derived from mutable content. Where content addressing applies (EvidenceArtifact), the content hash is *in addition to* the identifier, never instead of it (ADR-0006, boundary 5).

### C3. Case scoping

Every record except `Case` itself belongs to exactly one Case. Cross-case sharing of evidence or analysis is out of scope for v0.1 (see Part III, U1).

### C4. Time

Records carry `created_at` (record time — when ARGUS learned it). Where an entity describes the world, **event time** (when it happened in reality) is a distinct attribute and MUST never be conflated with record time.

### C5. Immutability classes (per ADR-0006)

- **Content-immutable (CI)** — the record's substantive content can never change by any path.
- **Versioned (V)** — the record is never edited in place; corrections follow the retraction pattern (C6).
- **Controlled-transition (CT)** — specific operational fields may change, only through enumerated, authorized, audited transitions.

Each entity below declares its class(es). Per-field enforcement mechanics belong to the Domain Invariant Matrix.

### C6. Retraction pattern (for class V)

A versioned record acquires, at retraction: `retracted_at`, `retracting_actor` (HumanActor only), `retraction_reason` (required, non-empty), and optionally `superseded_by` (the replacing record). Both records remain permanently readable. Default reads exclude retracted records but MUST never conceal their existence. Retraction is terminal: a retracted record is never un-retracted (a mistaken retraction is corrected by creating a successor record).

### C7. Provenance (per ADR-0004)

Every analytical claim (Observation, Interpretation, Hypothesis) and every AI-suggested record carries provenance at creation, immutable thereafter:

- **All claims:** non-empty source references appropriate to their ladder position; creating actor; method description.
- **AI-generated records additionally:** model identifier, model version, prompt/workflow version, uncertainty explanation (non-empty prose), review status.

Writes lacking required provenance MUST be rejected at the persistence boundary. **No provenance, no claim.**

### C8. Review status

AI-generated records carry `review_status ∈ {UNREVIEWED, ACCEPTED, REJECTED}`, initialized to `UNREVIEWED`. Only a HumanActor may advance it, exactly once, in either direction; the transition records the reviewer and time. `REJECTED` records remain readable (nothing disappears). Human-authored records have no review status (they are born human-accepted).

### C9. Audit

Every material domain mutation — creation, retraction, review transition, lifecycle transition, resolution — emits an AuditEntry atomically with the mutation itself. Reads of sealed or restricted material also emit AuditEntries. The enumeration of "material" is the Domain Invariant Matrix's job; this specification marks each entity's audit events.

### C10. The analytical ladder (per ADR-0002)

References climb exactly one rung; level-skipping MUST be structurally impossible:

```
EvidenceArtifact ← SourceLocator ← Observation ← Interpretation ← Hypothesis
```

No entity may hold a reference that shortcuts this chain (e.g., a Hypothesis directly citing an EvidenceArtifact).

---

## Part II — Entity specifications

Each entity is specified as: Purpose · Identity · Required attributes · Optional attributes · Relationships · Lifecycle · Invariants · Permitted actors · Prohibited operations · Provenance requirements · Audit events · Unresolved questions.

Lifecycle sections state the immutability class and any structurally load-bearing rules; the authoritative states, transitions, per-transition actors, and audit events live in [Entity Lifecycles](ENTITY_LIFECYCLES.md).

---

### 1. Case

**Purpose.** The bounded investigative context — with its legal authority basis — within which all evidence and analysis exist. The unit of authorization, access, and audit scope (Article VI).

**Identity.** Opaque ID (C2). A human-facing case designation (e.g., agency case number) is an attribute, not the identity, and MAY change under controlled transition.

**Required attributes.** Title; legal authority basis (the recorded grounds — warrant, statute, assignment — under which investigation is authorized); responsible HumanActor; status; `created_at`.

**Optional attributes.** External case designation(s); jurisdiction; case description; classification level.

**Relationships.** Root container: every other entity instance belongs to exactly one Case. Has many EvidenceArtifacts, Observations, Interpretations, Hypotheses, Contradictions, Unknowns, Entities, Relationships, AuditEntries.

**Lifecycle.** Class CT. All transitions HumanActor-only with recorded reason; `CLOSED` freezes analytical writes but never deletes or conceals anything. States and transitions: [Entity Lifecycles §1](ENTITY_LIFECYCLES.md#1-case-ct).

**Invariants.** A Case is never deleted. Legal authority basis is required at creation and versioned (V) thereafter — authority changes are new authority records, not edits. No analytical record may exist outside a Case.

**Permitted actors.** Create/transition: HumanActor. AIWorkflow and SystemProcess: read-only with respect to Case state.

**Prohibited operations.** Deletion; merging (v0.1); silent alteration of the legal authority basis; any AI- or system-initiated status transition.

**Provenance requirements.** Creating actor and authority basis recorded at creation.

**Audit events.** Created; status transition (with reason); authority basis added/superseded; classification changed; reopened.

**Unresolved questions.** Case merging and case linking (related cases) — deferred. Multi-jurisdiction authority representation — needs legal review (standing flag from ADR-0006).

---

### 2. EvidenceArtifact

**Purpose.** A digitally represented immutable record corresponding to a collected source of information preserved for investigative purposes (Lexicon). The system's only anchor to reality.

**Identity.** Opaque ID (C2) **plus** original cryptographic content hash computed at ingestion. Identity never depends solely on a storage provider URI (ADR-0006, boundary 5).

**Required attributes.** Content hash (algorithm + digest); media type; size; ingestion timestamp; ingesting actor; acquisition description (how/where/when the fragment was collected, as declared at ingest); storage reference (replaceable pointer, non-authoritative); status.

**Optional attributes.** Original filename; device/source identifiers; chain-of-custody references to external custody records; extracted technical metadata (EXIF and similar — stored as *observations about the artifact* when analytically used, see Invariants).

**Relationships.** Belongs to one Case. Referenced by SourceLocators (only path by which analysis touches it, C10). May be superseded by another EvidenceArtifact (retraction pattern).

**Lifecycle.** Content CI; operational fields CT. Pre-`ACTIVE` records (`PENDING_VERIFICATION`, `QUARANTINED`) are invisible to analysis (no SourceLocator may reference a non-`ACTIVE` artifact); activation requires passed integrity verification (ADR-0007). `SEALED` restricts content access with read auditing while existence stays visible to authorized queries. States and transitions: [Entity Lifecycles §2](ENTITY_LIFECYCLES.md#2-evidenceartifact-ci-content-ct-operational-fields).

**Invariants.** Content bytes and original hash: content-immutable (CI) — no mutation path exists at any layer. Ingestion record: CI. Operational fields (status, access classification, storage reference re-homing): CT. Technical metadata used in analysis MUST enter the ladder as Observations with SourceLocators, not as bare artifact attributes — metadata is evidence *about* evidence and needs the same provenance.

**Permitted actors.** Ingest: HumanActor or authorized SystemProcess (pipeline), always attributing the responsible human authority. `PENDING → ACTIVE`: SystemProcess (verification) — this is mechanical, not judgmental, hence permitted. Retract/seal: HumanActor only.

**Prohibited operations.** Content update; deletion; hash recomputation that replaces the original; sealing or retraction by AIWorkflow or SystemProcess; any operation that leaves a claim referencing content that no longer exists.

**Provenance requirements.** Acquisition description, ingesting actor, and hash at creation. Retraction requires reason and superseding linkage where applicable.

**Audit events.** Ingested; verified/activated; verification failed; retracted; sealed/unsealed; sealed-content read (every read); storage re-homed; classification changed.

**Unresolved questions.** Hash algorithm selection and algorithm-migration policy — needs its own standard. Very large artifacts (device images): chunked hashing and partial-access semantics — defer to ADR-0007. Physical-evidence representation (the artifact is a *record of* a physical item) — needs ISS-0004.

---

### 3. SourceLocator

**Purpose.** A precise, immutable address of a region within a single EvidenceArtifact (Lexicon) — the joint through which every Observation anchors to evidence.

**Identity.** Opaque ID (C2).

**Required attributes.** Target EvidenceArtifact reference; locator scheme (e.g., page-region, time-range, byte-range, transcript-span); scheme-specific address payload; creating actor; `created_at`.

**Optional attributes.** Human-readable excerpt or rendering hint (convenience only — never authoritative over the addressed content).

**Relationships.** Belongs to exactly one EvidenceArtifact (and its Case). Referenced by one or more Observations.

**Lifecycle.** Class V (pattern C6). Created only against an `ACTIVE` artifact. States and transitions: [Entity Lifecycles §3](ENTITY_LIFECYCLES.md#3-sourcelocator-v).

**Invariants.** Scheme + address: immutable after creation — a wrong locator is retracted and replaced, never edited. A SourceLocator MUST resolve within the bounds of its artifact's content (validated at creation). Retracting an artifact does not delete its locators; they become flagged as referencing retracted evidence, and every claim above them surfaces that flag (Article IX — the epistemic status of downstream claims visibly degrades).

**Permitted actors.** Create: HumanActor or AIWorkflow (an AI-created locator is part of an AI proposal and shares its review status). Retract: HumanActor.

**Prohibited operations.** Editing address or retargeting to a different artifact; referencing any non-`ACTIVE` (at creation time) or foreign-case artifact; deletion.

**Provenance requirements.** Creating actor; AI-created locators carry the full AI provenance block (C7) via their owning proposal.

**Audit events.** Created; retracted; downstream-flag raised (owning artifact retracted or sealed).

**Unresolved questions.** The locator scheme registry (canonical schemes per media type, address payload grammar) — needs the planned Evidence Naming/locator Standard. Locator stability across artifact re-encodings — defer to ADR-0007.

---

### 4. Observation

**Purpose.** A source-grounded statement directly supported by one or more SourceLocators (Lexicon). States what evidence shows; contains no meaning-making.

**Identity.** Opaque ID (C2).

**Required attributes.** Statement text; references to ≥1 SourceLocator; creating actor; method description (how the observation was made: manual review, transcription, measurement, automated extraction); `created_at`; event time where the statement is about a temporal fact (C4); AI provenance block if AIWorkflow-created (C7, C8).

**Optional attributes.** Uncertainty qualifiers on the statement (e.g., legibility limits); structured payload (measurements, coordinates) alongside the prose statement.

**Relationships.** Belongs to one Case. References ≥1 SourceLocator (its only downward references — C10). Referenced upward by Interpretations. May be a ContradictionMember; may be linked by UnknownLinks.

**Lifecycle.** Class V; review status per C8 orthogonal for AI proposals. States and transitions: [Entity Lifecycles §4–6](ENTITY_LIFECYCLES.md#46-observation-interpretation-hypothesis-v).

**Invariants.** ≥1 SourceLocator reference at creation, non-removable, non-substitutable (corrections = retraction and replacement). The statement MUST be observational: it describes artifact content, not meaning. (Enforced by review discipline and AI prompt design; the schema enforces the reference topology.) An Observation whose every SourceLocator is retracted is automatically flagged as ungrounded and MUST be surfaced for human disposition — never auto-retracted (Article II).

**Permitted actors.** Create: HumanActor, AIWorkflow (as proposal). Retract: HumanActor. Review transition: HumanActor.

**Prohibited operations.** Editing statement or references in place; referencing EvidenceArtifacts directly (must pass through SourceLocator); deletion; AI retraction or review of its own output.

**Provenance requirements.** Full C7. Method description is required even for human observations (Article III).

**Audit events.** Created; retracted; review transition; ungrounded-flag raised.

**Unresolved questions.** Canonical uncertainty vocabulary for observational qualifiers — blocked on the uncertainty representation decision (U2, Part III).

---

### 5. Interpretation

**Purpose.** A derived meaning inferred from one or more Observations (Lexicon). The first rung where meaning enters the system — explicitly marked as inference.

**Identity.** Opaque ID (C2).

**Required attributes.** Meaning statement; references to ≥1 grounded Observation, each grounding carrying a revision snapshot (statement fingerprint), a grounding role (SUPPORTING/LIMITING/CONTEXTUAL), and link time; reasoning description (why these observations support this meaning — Article III); creating actor; `created_at`; the structured uncertainty envelope — `uncertainty_status` (ACKNOWLEDGED/MATERIAL/LIMITING/UNRESOLVED; deliberately no "certain") plus mandatory `uncertainty_explanation` (Article IX; not a confidence scale); AI provenance block if applicable. A valid Interpretation means only: *this human-authored meaning is constitutionally admissible and traceable* — not correct, preferred, complete, likely, or endorsed.

**Optional attributes.** Explicit assumptions relied upon; references to competing Interpretations of the same Observations (cross-links, not exclusions).

**Relationships.** Belongs to one Case. References ≥1 Observation (only downward — C10). Referenced upward by Hypotheses. May be a ContradictionMember; may be linked by UnknownLinks. May ground a Relationship (entity graph).

**Lifecycle.** Class V; review status per C8 orthogonal. States and transitions: [Entity Lifecycles §4–6](ENTITY_LIFECYCLES.md#46-observation-interpretation-hypothesis-v).

**Invariants.** ≥1 Observation reference, immutable set after creation. Uncertainty expression non-empty — an Interpretation claiming certainty must say so explicitly and attribute why. Multiple Interpretations over the same Observations coexist without rank (Article IV); the schema has no "primary interpretation" concept.

**Permitted actors.** Create: HumanActor, AIWorkflow (proposal). Retract/review: HumanActor.

**Prohibited operations.** In-place edits; referencing SourceLocators or EvidenceArtifacts directly (level-skip); deletion; any operation that deletes or demotes competing Interpretations as a side effect.

**Provenance requirements.** Full C7 plus reasoning description.

**Audit events.** Created; retracted; review transition; grounding-flag raised (a referenced Observation retracted or ungrounded).

**Unresolved questions.** Uncertainty representation (U2). Whether assumptions should be first-class linkable records rather than prose — revisit after v0.1 usage.

---

### 6. Hypothesis

**Purpose.** A testable explanatory model evaluated against available evidence (Lexicon). A candidate account of what happened — never a verdict.

**Identity.** Opaque ID (C2).

**Required attributes.** Explanatory narrative; references to ≥1 Interpretation; reasoning description; explicit statement of what evidence would strengthen or weaken it (testability — Article VII); uncertainty expression (Article IX); creating actor; `created_at`; AI provenance block if applicable.

**Optional attributes.** Links to open Unknowns and Contradictions it touches (surfaced limitations); event-time frame the hypothesis addresses.

**Relationships.** Belongs to one Case. References ≥1 Interpretation (only downward — C10). May be a ContradictionMember; may be linked by UnknownLinks.

**Lifecycle.** Class V; review status per C8 orthogonal. **There is no terminal "confirmed" or "true" state** — a Hypothesis is never system-promoted to fact; conviction lives in human Understanding, outside the schema (Article II). States and transitions: [Entity Lifecycles §4–6](ENTITY_LIFECYCLES.md#46-observation-interpretation-hypothesis-v).

**Invariants.** ≥1 Interpretation reference, immutable set. Competing Hypotheses coexist without structural privilege (Article IV): no "leading hypothesis" field, no exclusivity constraint, no ranking stored as fact. Testability statement non-empty.

**Permitted actors.** Create: HumanActor, AIWorkflow (proposal). Retract/review: HumanActor.

**Prohibited operations.** In-place edits; level-skipping references; deletion; system- or AI-side promotion, ranking, or confirmation; deleting alternatives.

**Provenance requirements.** Full C7 plus reasoning and testability statements.

**Audit events.** Created; retracted; review transition; grounding-flag raised.

**Unresolved questions.** Whether investigator-recorded confidence assessments (human, attributed, versioned) belong on Hypothesis or in a future working-notes construct — deliberately deferred; risks importing judgment into the schema.

---

### 7. Contradiction

**Purpose.** A formally recognized incompatibility between two or more analytical claims (Lexicon). Conflict made durable and impossible to ignore.

**Identity.** Opaque ID (C2).

**Required attributes.** Description of the incompatibility; `contradiction_type` (TEMPORAL/SPATIAL/IDENTITY/CAUSAL/DESCRIPTIVE/NUMERIC/PROCEDURAL/PROVENANCE/CUSTODY/LOGICAL); `scope_definition` (the shared conditions under which the claims conflict); `incompatibility_basis` (why simultaneous truth is impossible under that scope — mere disagreement never becomes formal contradiction); ≥2 ContradictionMembers (each an `INCOMPATIBLE_CLAIM` with a recognition-time snapshot); operational state; creating actor; `created_at`; AI provenance block if AI-suggested. A Contradiction is admissible — not necessarily true; `contradiction_health` (CURRENT/DEGRADED) is derived, never stored.

**Optional attributes.** Severity/priority annotation (triage aid, not truth signal).

**Relationships.** Belongs to one Case. Composed of ContradictionMembers. May be linked by UnknownLinks (a contradiction often implies an unknown).

**Lifecycle.** Disposition transitions HumanActor-only with rationale; both terminal (recurrence = new Contradiction referencing the old). Description corrections: class V (retract/replace the description, not the Contradiction's history). States and transitions: [Entity Lifecycles §7](ENTITY_LIFECYCLES.md#7-contradiction-v-description-terminal-disposition).

**Invariants.** ≥2 members at all times. AI may suggest (status `OPEN`, review status `UNREVIEWED`) but no AI or system path may set `RESOLVED` or `WITHDRAWN` (Article II; ADR-0005). Resolution never deletes or retracts the conflicting claims themselves — they remain, with the resolution recorded alongside.

**Permitted actors.** Create: HumanActor, AIWorkflow (suggestion). Resolve/withdraw: HumanActor only.

**Prohibited operations.** AI/system resolution or withdrawal; deletion; member removal that would drop the count below 2; auto-resolution when a member is retracted (retraction of a member surfaces the fact for human disposition).

**Provenance requirements.** C7 for the identification itself; resolution records resolving actor, rationale, time, and evidence references.

**Audit events.** Created/suggested; member added; resolved (with rationale); withdrawn; member-retracted flag raised; review transition.

**Unresolved questions.** Whether resolution rationales should themselves be ladder claims (Interpretations) rather than attached prose — leans yes, revisit at implementation.

---

### 8. ContradictionMember

**Purpose.** The explicit link binding one analytical claim into a Contradiction (Lexicon).

**Identity.** Opaque ID (C2).

**Required attributes.** Owning Contradiction; member claim reference (Observation, Interpretation, or Hypothesis); the member's role in the conflict (e.g., which side/aspect); creating actor; `created_at`.

**Optional attributes.** Per-member note explaining this claim's part in the incompatibility.

**Relationships.** Belongs to exactly one Contradiction (and its Case). References exactly one claim.

**Lifecycle.** Class CI once created; erroneous membership is handled by withdrawing/superseding the Contradiction description, never by silently deleting members (the historical fact of "these were held incompatible" is preserved). See [Entity Lifecycles §8](ENTITY_LIFECYCLES.md#8-contradictionmember-ci).

**Invariants.** Member claim must belong to the same Case as the Contradiction. A claim may belong to many Contradictions.

**Permitted actors.** Create: whoever creates/extends the Contradiction (HumanActor, or AIWorkflow as suggestion).

**Prohibited operations.** Deletion; retargeting to a different claim; cross-case membership.

**Provenance requirements.** Inherits the owning Contradiction's provenance; records its own creating actor.

**Audit events.** Created (as "member added" on the Contradiction).

**Unresolved questions.** Whether Entities/Relationships (not just ladder claims) can be contradiction members — excluded in v0.1; conflicting entity data should surface as conflicting *claims about* entities.

---

### 8b. ContradictionDisposition (ADR-0027 — the fifteenth first-class object)

**Purpose.** The human record of how a conflict was disposed — never of which claim reality favors (ONT-CDP-001).

**Identity.** Opaque ID (C2).

**Required attributes.** Owning Contradiction (at most one active disposition); outcome ∈ {`EXPLAINED`, `NO_LONGER_APPLICABLE`, `WITHDRAWN`, `UNRESOLVED`, `SUPERSEDED`}; rationale (non-empty); disposing HumanActor; `created_at`. **No outcome exists, or may ever be added, that implies a member was proven correct.**

**Optional attributes.** Informing provenance references (claims/artifacts that informed — never vindicated — the disposition); for `SUPERSEDED`: the replacing Contradiction.

**Relationships.** Belongs to exactly one Contradiction (and its Case).

**Lifecycle.** Content-immutable once created; terminal; a mistaken disposition is superseded by a successor (Lifecycles §7).

**Invariants.** Author structurally HumanActor-only (Article II); disposition alters no member, retracts nothing, promotes nothing.

**Permitted actors.** Create/supersede: HumanActor only.

**Prohibited operations.** AI/system authorship; editing; deletion; any adjudicative outcome.

**Provenance requirements.** Disposing actor, rationale, informing references.

**Audit events.** contradiction-disposed (outcome in detail); disposition-superseded.

**Unresolved questions.** None currently.

---

### 9. Unknown

**Purpose.** A formally recognized gap in current understanding (Lexicon). Missing information as a durable object that demands disposition — absence of data is never silently treated as evidence of absence (Article IX).

**Identity.** Opaque ID (C2).

**Required attributes.** The question, stated as a question; status; creating actor; `created_at`; AI provenance block if AI-suggested.

**Optional attributes.** Why the gap matters (impact statement); candidate avenues of inquiry (prose, not tasking).

**Relationships.** Belongs to one Case. Connected to affected records via UnknownLinks. Disposed via at most one active UnknownResolution.

**Lifecycle.** Two independent families (AGC Session 008): the operational state (`OPEN ⇄ UNDER_REVIEW`, human-only, reversible, carrying no conclusion) and the epistemic disposition (derived solely from the UnknownResolution record — `ANSWERED`, `PARTIALLY_ANSWERED`, `UNRESOLVABLE`, `WITHDRAWN`; never a bare status flip; all terminal, with a partially answered question's remaining gap re-stated as a new Unknown). Question-text corrections: class V. States and transitions: [Entity Lifecycles §9](ENTITY_LIFECYCLES.md#9-unknown-v-question-text-operational-state-ct-terminal-disposition-via-unknownresolution).

**Invariants.** No AI or system path may transition an Unknown (Article II; ADR-0005). Status and its UnknownResolution are always consistent (status is derived from the resolution's existence and type).

**Permitted actors.** Create: HumanActor, AIWorkflow (suggestion). Transition: HumanActor via UnknownResolution.

**Prohibited operations.** AI/system closure; deletion; status change without an UnknownResolution record.

**Provenance requirements.** C7 for the identification.

**Audit events.** Created/suggested; linked/unlinked; resolved/withdrawn/marked-unresolvable (via resolution); review transition.

**Unresolved questions.** Prioritization semantics (triage without implying importance = truth) — defer to UX phase.

---

### 10. UnknownLink

**Purpose.** The explicit connection between an Unknown and a record it affects (Lexicon) — making "what does this gap touch?" a first-class query.

**Identity.** Opaque ID (C2).

**Required attributes.** Owning Unknown; target record reference (Observation, Interpretation, Hypothesis, Entity, Relationship, or Contradiction); nature of the dependency (how the gap affects the target); creating actor; `created_at`.

**Optional attributes.** None beyond a clarifying note.

**Relationships.** Belongs to one Unknown (and its Case); references one target record in the same Case.

**Lifecycle.** Class V — a link created in error is retracted with reason. States and transitions: [Entity Lifecycles §10](ENTITY_LIFECYCLES.md#10-unknownlink-v).

**Invariants.** Same-case only. Duplicate links (same Unknown, same target, same nature) SHOULD be rejected.

**Permitted actors.** Create: HumanActor, AIWorkflow (as part of a suggestion). Retract: HumanActor.

**Prohibited operations.** Deletion; retargeting.

**Provenance requirements.** Creating actor; inherits AI provenance from the owning suggestion where applicable.

**Audit events.** Created; retracted.

**Unresolved questions.** Whether resolving an Unknown should require re-attestation of linked claims — leans no (surfacing, not forcing); confirm at implementation.

---

### 11. UnknownResolution

**Purpose.** The human-authored record of how an Unknown was resolved, withdrawn, or determined unresolvable, with provenance for any resolving evidence (Lexicon).

**Identity.** Opaque ID (C2).

**Required attributes.** Owning Unknown; resolution type ∈ {`ANSWERED`, `PARTIALLY_ANSWERED`, `WITHDRAWN`, `UNRESOLVABLE`}; rationale (non-empty); resolving HumanActor; `created_at`; for `ANSWERED` and `PARTIALLY_ANSWERED`: references to the claims (Observations/Interpretations) that answer the question — an answer without evidence is not an answer (Article I).

**Optional attributes.** For `UNRESOLVABLE`: what would have been required to answer it.

**Relationships.** Belongs to exactly one Unknown (and its Case); `ANSWERED` resolutions reference ≥1 claim.

**Lifecycle.** Class CI once created. A mistaken resolution is superseded: a HumanActor creates a successor resolution that explicitly supersedes it, and the persisting question reopens as a new Unknown. See [Entity Lifecycles §11](ENTITY_LIFECYCLES.md#11-unknownresolution-ci).

**Invariants.** Author MUST be a HumanActor — no AI or system path exists (Article II; ADR-0005). `ANSWERED` without claim references MUST be rejected (an answer without evidence is not an answer — Article I).

**Permitted actors.** Create/supersede: HumanActor only.

**Prohibited operations.** AI/system authorship; editing; deletion.

**Provenance requirements.** Resolving actor, rationale, evidence references (for `ANSWERED`).

**Audit events.** Created; superseded.

**Unresolved questions.** None currently.

---

### 12. Entity

**Purpose.** An investigatively significant actor or object in the world of the case — person, organization, vehicle, location, object, or account — as represented in the system, distinct from the reality it denotes (Lexicon).

**Identity.** Opaque ID (C2). **The Entity record is a referent handle, not a truth claim**: what is *known about* an entity lives in the ladder as claims that reference it.

**Required attributes.** Entity class (from the future Entity Classification Standard; provisional enumeration in v0.1); working designation (a label for human reference, explicitly non-authoritative); creating actor; `created_at`.

**Optional attributes.** None as bare attributes. Descriptive properties (name, DOB, plate number, address) MUST enter as Observations/Interpretations referencing the Entity — an unsourced attribute on an Entity would be an ungrounded claim (Article I).

**Relationships.** Belongs to one Case. Referenced by claims (claims MAY reference Entities they concern, in addition to their ladder references). Connected to other Entities via Relationships. May be linked by UnknownLinks.

**Lifecycle.** Class V (working designation: CT) — retired when created in error (e.g., duplicate); retraction records the surviving duplicate as `superseded_by` where applicable. States and transitions: [Entity Lifecycles §12](ENTITY_LIFECYCLES.md#12-entity-v-designation-ct).

**Invariants.** The working designation carries no evidentiary weight and is CT (may be refined as understanding grows, with audit). Entity class is immutable after creation (a mis-classed entity is retracted and replaced). Distinctness is a human determination: the system never auto-merges entities (Article II).

**Permitted actors.** Create: HumanActor, AIWorkflow (proposal). Retract, designation change: HumanActor.

**Prohibited operations.** Deletion; auto-merge or system-side identity resolution; storing unsourced descriptive facts as attributes.

**Provenance requirements.** Creating actor; AI proposals carry C7. The Entity itself is thin; its substance is claims, which carry their own provenance.

**Audit events.** Created; retracted/superseded; designation changed; review transition.

**Unresolved questions.** **Entity identity resolution** (same-person determination across artifacts) is the hardest open problem: v0.1 keeps it fully human via retract-and-supersede; a future ADR must address assisted matching without violating Article II. Cross-case entity identity — out of scope with C3.

---

### 13. Relationship

**Purpose.** An evidence-grounded, typed connection between two Entities (Lexicon) — the edges of the case's entity graph.

**Identity.** Opaque ID (C2).

**Required attributes.** Source Entity; target Entity; relationship type (future Entity Classification Standard; provisional v0.1 enumeration); directionality flag (directed/undirected); grounding references to ≥1 Observation or Interpretation supporting the connection; creating actor; `created_at`; uncertainty expression; AI provenance block if applicable.

**Optional attributes.** Event-time validity interval (when the relationship held in reality — C4).

**Relationships (meta).** Belongs to one Case; connects exactly two Entities in that Case; grounded in ladder claims; may be linked by UnknownLinks.

**Lifecycle.** Class V; review status per C8 orthogonal. States and transitions: [Entity Lifecycles §13](ENTITY_LIFECYCLES.md#13-relationship-v).

**Invariants.** ≥1 grounding claim — an ungrounded edge is an ungrounded claim (Article I). Both endpoints in the same Case. Grounding-flag raised if supporting claims are retracted; never auto-retracted (Article II). Multiple Relationships of different types (or times) between the same pair coexist.

**Permitted actors.** Create: HumanActor, AIWorkflow (proposal). Retract/review: HumanActor.

**Prohibited operations.** In-place edits (retype, re-endpoint); deletion; grounding-free creation; self-loops unless the type explicitly permits them (standard to define).

**Provenance requirements.** Full C7 via its grounding claims plus its own creating-actor record.

**Audit events.** Created; retracted; review transition; grounding-flag raised.

**Unresolved questions.** Temporal validity modeling (intervals vs. event-anchored) — decide with the Timeline Standard. N-ary relationships (meetings, transactions among 3+ entities) — v0.1 decomposes into pairwise edges; revisit with ISS input.

---

### 14. AuditEntry

**Purpose.** The append-only, immutable record of a single material action in the system: who did what, to which record, when (Lexicon). The transparency substrate for Article VIII.

**Identity.** Opaque ID (C2), plus a strictly monotonically ordered position within its Case's audit history.

**Required attributes.** Acting actor (class + identity + relevant version fields for AIWorkflow); action type (from the future Audit Event Standard; provisional enumeration = the audit events named throughout this document); target record reference(s); `occurred_at`; outcome (succeeded/rejected — constitutional rejections are themselves audited); hash-chain fields per ADR-0016: `chain_version`, `canonical_payload` (the immutable hashed text derived exactly once at insertion from the queryable payload), `previous_event_hash`, `event_hash`. Each Case's chain is rooted in a `case_audit_heads` record (`last_sequence`, `last_event_hash`) created with the Case.

**Optional attributes.** Structured action detail (e.g., the retraction reason, the transition made); the authorization context under which the actor acted (Article VI).

**Relationships.** Belongs to one Case; references the record(s) acted upon.

**Lifecycle.** None. Created once; content-immutable (CI) forever; never retracted, never superseded. A wrong audit entry is corrected by a subsequent *compensating* entry that references it. See [Entity Lifecycles §14](ENTITY_LIFECYCLES.md#14-auditentry-ci--strongest-guarantee-in-the-system).

**Invariants.** Emitted atomically with the mutation it records (ADR-0006 validation criterion 2) — an unaudited material mutation must be impossible, and an AuditEntry for a mutation that did not occur equally so. Reads of sealed/restricted material emit entries. The audit history is complete per Case: ordering gaps are detectable.

**Permitted actors.** Created only by the system as a side effect of actor-attributed operations — no actor writes AuditEntries directly.

**Prohibited operations.** Direct creation, update, deletion, retraction — by anyone, including administrators, at every layer (this is the strongest immutability guarantee in the system).

**Provenance requirements.** The AuditEntry *is* provenance; it carries full actor attribution including AI version fields.

**Audit events.** Not applicable (audit of audit is the compensating-entry mechanism).

**Unresolved questions.** ~~Tamper-evidence beyond database controls (hash-chaining entries)~~ — **resolved by ADR-0016** (per-case hash chain, tamper-evident within the trust boundary). Retention interaction with jurisdictional requirements — legal review flag (ADR-0006).

---

## Part III — Global unresolved questions

Tracked here so no gap hides inside an entity section (the specification obeys its own philosophy):

- **U1 — Cross-case evidence and entities.** v0.1 is strictly case-scoped (C3). Real investigations share evidence and people across cases; a future ADR must reconcile sharing with Article VI authority scoping.
- **U2 — Uncertainty representation.** Uncertainty expressions are mandatory prose in v0.1. Whether ARGUS adopts a structured vocabulary or scale (and how to avoid false precision — Article IX) needs ISS-0003 before schematization.
- **U3 — Sealing, expungement, retention.** Legal-lifecycle semantics vary by jurisdiction; v0.1 models only `SEALED` visibility restriction. Standing legal-review flag carried from ADR-0006; no compliance claim is made.
- **U4 — Ingestion protocol.** `PENDING → ACTIVE` finalization semantics reserved for ADR-0007.
- **U5 — Working notes.** Investigators need scratch thinking that is not yet claims; v0.1 omits it deliberately rather than model it badly. Revisit after first investigator feedback.

## Ratification record (AGC Review Session 001, 2026-07-13)

Ratified as one constitutional package with [ONTOLOGY.md](ONTOLOGY.md) and [ENTITY_LIFECYCLES.md](ENTITY_LIFECYCLES.md); the full verdicts are recorded in the [Ontology's ratification record](ONTOLOGY.md#ratification-record-agc-review-session-001-2026-07-13).

- [x] Constitutional Review — **PASS**
- [x] Domain Review — **PASS**
- [x] Architectural Review — **PASS** (with the session's Verification directive → ADR-0010)

The [Invariant Matrix](INVARIANT_MATRIX.md) population and the ERD (`docs/architecture/`) are now unblocked.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft for review. |
| 0.2.0 | 2026-07-13 | Restructured under the Ontology-first hierarchy (ADR-0009 / Founder Resolution 003): meaning layer extracted to ONTOLOGY.md; authoritative state machines extracted to ENTITY_LIFECYCLES.md; Invariant Matrix relocated to docs/domain/; review checklist updated to AGC mechanisms. |
| 1.0.0 | 2026-07-13 | Ratified by AGC Review Session 001. |
| 1.1.0 | 2026-07-13 | EvidenceArtifact lifecycle references aligned with ADR-0007 as amended by AGC Session 004 (PENDING_VERIFICATION, QUARANTINED; SourceLocator prohibition restated as non-ACTIVE). |
| 1.2.0 | 2026-07-13 | AuditEntry gains the ADR-0016 hash-chain attributes and the case_audit_heads chain root; hash-chaining unresolved question closed. |
| 1.3.0 | 2026-07-13 | ONT-INT-001 refined per Slice 2A amendments: structured uncertainty envelope, grounding revision snapshot with roles, admissibility disclaimer (U2 remains open — the envelope is not a confidence scale). |
| 1.4.0 | 2026-07-13 | ONT-UNK-001: operational state (UNDER_REVIEW) separated from derived epistemic disposition; ONT-UNR-001 gains PARTIALLY_ANSWERED with mandatory claim references (AGC Session 008, Amendment 1). |
| 1.5.0 | 2026-07-13 | ONT-CON-001 gains the explicit incompatibility basis (type/scope/basis) and derived health; ONT-CNM-001 becomes INCOMPATIBLE_CLAIM with recognition-time snapshots; ONT-CDP-001 added as §8b (ADR-0027, AGC Session 010). |
