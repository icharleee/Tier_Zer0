# ARGUS Derivation Specification

- **Document version:** 1.10.0 — Ratified at 1.0.0 by AGC Review Session 003, 2026-07-13; 1.10.0 adds D-PRN-029/030 (authority and protected access) per the Slice 1F-B amendments (see version history)
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

### D-PRN-018 — Semantic contamination registry (from ONT-PRN-018)

Applies to every epistemic layer. No layer's schema may carry the vocabulary of the layers above it; a release-blocking contamination test walks every epistemic table's columns against this registry, with its expectations transcribed from this table (ONT-PRN-015). Adding a stem is MINOR; removing one requires AGC review. Vocabulary scanning is the tripwire; reviews still judge semantics.

**Scope (Session 012 caution):** these guards apply to **structured surfaces** — schema identifiers, enum values, function names, structured fields. Prose lexical guards are separate, conservative, and limited to clearly adjudicative or ranking phrases (the comparative and adjudicative guards in the Constitutional Predicates). Forbidden-word scanning never *proves* semantic cleanliness.

| Layer | Forbidden column-name stems (from higher layers) |
|---|---|
| Observation (ONT-OBS-001) | confiden, infer, probab, interpret, hypoth, rank, suspic, intent, meaning, likelihood, predict, score |
| Interpretation (ONT-INT-001) | hypoth, likelihood, predict, verdict, guilt; junctions and the object additionally: rank, preferred, primary, weight (object also: confiden, probab, score) |
| SourceLocator (ONT-SRC-001) | all Observation stems plus: statement, claim |
| Unknown family (ONT-UNK-001, ONT-UNL-001, ONT-UNR-001) | priorit, deadline, task (object and links also: answer, conclusion; object and resolutions also: hypoth, likelihood, predict; links also: ground, support — a boundary can never become support) |
| Contradiction family (ONT-CON-001, ONT-CNM-001, ONT-CDP-001) | winner, prevail, surviv, adjudicat, correct, refut (object also: rank, preferred, weight, score, hypoth; members also: rank, preferred, support, challeng; dispositions also: rank, preferred) |
| Hypothesis (ONT-HYP-001) | verdict, guilt, conclu, probab, confiden, preferred, primary, leading, best, winner, accept, theory, rank, weight, score, likelihood, predict, refut, disprov, defeat, weaken, invalidat, promot |
| HypothesisGrounding / HypothesisAlternative | rank, preferred, primary, weight, score, winner, strength, better, stronger, refut |
| ContradictionLink (Contradiction → Hypothesis) | winner, prevail, surviv, adjudicat, correct, refut, disprov, defeat, weaken, invalidat, rank, preferred |

The Hypothesis row renders Resolution 018's prohibited fields (`probability`, `confidence_score`, `preferred`, `primary`, `leading`, `best_fit`, `winner`, `case_theory`, `accepted`) as stems over structured surfaces — where a stem like `theory`, `best`, or `accept` would be overly broad for prose, it is exactly right for a column name. ContradictionLink deliberately omits `hypoth`: referencing the object it bounds is the link's purpose; the Contradiction object itself still never carries hypothesis vocabulary.

### D-PRN-024 — Constraint precedes expressive power (from ONT-PRN-024)

Applies to every proposed epistemic object or capability, and to composition surfaces (read models).

- **Process:** no implementation until the ontology defines the constraints, refusal conditions, provenance obligations, validity boundaries, and non-effects limiting the new expressive power; the slice plan gate is unapprovable without this floor.
- **Tests:** the floor lands as refusal codes, Invariant Matrix rows, and negative-obligation tests before code. Cite ONT-PRN-024.

### D-PRN-025 — Historical articulation vs. current derived condition (from ONT-PRN-025)

Applies to every temporal attribute of every object, and to every read surface.

- **Schema:** each temporal attribute classifies as exactly one of *historical-immutable* (stored, content-immutable) or *current-derived* (computed, stored nowhere). A stored field that later events would need to update is a design defect.
- **Read surfaces:** expose both, side by side, labeled; no derivation overwrites or conceals a historical articulation; no historical record is presented as the current condition.
- **Tests:** per pattern instance, prove the creation-time record survives the later event that changes the derived state (the Slice 2D acceptance template). Cite ONT-PRN-025.

### D-REC — Case Reconstruction (composition obligations)

The Case Reconstruction is a transient, read-only projection with no epistemic standing of its own (Session 014; not a first-class object). Its normative surface — manifest, visibility envelope, structural non-preference, canonical serialization, ordering, refusal conditions, non-effects — lives in [CASE_RECONSTRUCTION.md](CASE_RECONSTRUCTION.md) and is verified by the H8 suite through semantic structural equality strengthened by canonical byte identity. Governing rule: composition may reveal relationships already present in the constitutional graph; it may never create a meaning that no constitutional record already carries.

### D-PRN-026 — Integrity is never truth (from ONT-PRN-026)

Applies to every comparison among stored representations of constitutional records.

- **Schema/surfaces:** integrity outcomes are a closed condition set; no state or field may express correctness, authenticity, authority, or a "true version"; agreement/divergence vocabulary never crosses into evidentiary claims.
- **Invariants:** no integrity result changes any epistemic record, disposition, derived epistemic state, or admissibility.
- **Tests:** the prohibited-surface scan and the negative obligation that classification alters nothing. Cite ONT-PRN-026.

### D-PRN-027 — No silent repair (from ONT-PRN-027)

Applies to every operation that can observe divergence in constitutional storage or history.

- **Process:** detection, proposed remediation, and authorized mutation are separate operations; scans hold no write path; repair (where it ever exists) enters via controlled functions with its own audit events under its own gate.
- **Tests:** a scan mutates nothing (byte-check before/after) and emits no audit entries; repeat scans over unchanged state are identical. Cite ONT-PRN-027.

### D-REC-STORAGE — Storage Reconciliation (detection obligations)

The reconciliation scan is a transient, read-only projection of storage-integrity state. Its normative surface — the storage-reference authority triple, the closed condition set with diagnostic reasons, classification precedence, sealed handling, report shape, ContentStore protocol contract — lives in [STORAGE_RECONCILIATION.md](STORAGE_RECONCILIATION.md), verified by the H9 suite (dual-rendered classification over shared observed facts; probing declared single-implementation). Governing rule: reconciliation may tell ARGUS that its representations disagree; it may never tell ARGUS what reality therefore means.

### D-PRN-028 — Identity is authenticated, never asserted (from ONT-PRN-028)

Applies to every constitutional command (any action that creates or transitions constitutional state) exposed through a transport boundary.

- **Schema:** constitutional command schemas carry no identity field; the actor is derived from an authenticated principal, never from payload. A caller-supplied identity field is refused, even when it matches (matching caller assertion is still assertion).
- **Invariants:** authentication (a single-implementation transport concern), actor attribution (the triangulated binding rule), authority (1F-B), and epistemic meaning (never) stay distinct; the principal carries no permissions; binding performs no resource authorization; attribution confers no credibility.
- **Persistence:** the principal is bound transaction-scoped (`SET LOCAL`, never a persistent pooled-connection GUC); the guard fails closed at mutation entry for the authenticated application transaction, with audit-append checking only as defense-in-depth; no fallback to caller-supplied identity for transport-originated writes.
- **Tests:** the binding matrix dual-rendered; refusal for unauthenticated / caller identity input / class mismatch / actor-principal mismatch; principal context does not leak across transactions; a record's epistemic fields are identical across different authenticated authors. Cite ONT-PRN-028. Detail in [ACTOR_CONTEXT.md](ACTOR_CONTEXT.md).

### D-PRN-029 — Authority governs actions and visibility, never truth (from ONT-PRN-029)

Applies to every action-authorization and visibility decision.

- **Schema/surfaces:** authorization is a pure decision over normalized, resource-scoped capability grants (Case scope only in 1F-B; no `*`, no inheritance); action authority and visibility authority stay distinct; no authority outcome carries a trust/credibility/preference surface.
- **Invariants:** no grant or denial changes any stored field, derived state, admissibility, or reconstruction epistemic content; two principals see identical epistemic state for fields both may view; authentication alone confers nothing; trusted-internal execution is not user authority.
- **Tests:** the `authorize` decision matrix dual-rendered; capability non-inheritance; Case-A grant refused in Case B; authority changes no derived state. Cite ONT-PRN-029. Detail in [AUTHORITY.md](AUTHORITY.md).

### D-PRN-030 — Protected access is explicit, least-privileged, auditable (from ONT-PRN-030)

Applies to every access to protected (SEALED) information.

- **Visibility:** the two-stage ladder — withholding is explicit only once existence may be disclosed (secrecy is not an existence leak); a principal without CASE_READ receives a generic resource denial, never a SEALED envelope.
- **Access accounting:** protected content is disclosed only when access attribution has been durably recorded; the evidence stays byte-identical; the access event is a new fact (the bounded refinement of read purity). `SEALED_VERIFY` returns integrity, never content, never authenticity.
- **Tests:** no existence leak without CASE_READ; content withheld if the access audit fails; SEALED_VERIFY without SEALED_CONTENT_READ; explicit withholding never absence. Cite ONT-PRN-030. Detail in [AUTHORITY.md](AUTHORITY.md).

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

- **Schema properties:** meaning statement; ≥1 grounded Observation reference, each grounding snapshotting the observation revision (statement fingerprint), role (SUPPORTING/LIMITING/CONTEXTUAL), and link time; reasoning description; the **structured uncertainty envelope** — status (ACKNOWLEDGED/MATERIAL/LIMITING/UNRESOLVED, no "certain") + mandatory explanation (Article IX). Meaning/reasoning prose passes the comparative-vocabulary lexical guard; `grounding_health` (GROUNDED/DEGRADED) is derived, never stored.
- **Invariants:** no "primary interpretation" concept anywhere — schema, API, or UI (ONT-PRN-002; Article IV); competing interpretations coexist without rank.
- **Audit events:** created; retracted; review transition; grounding-flag raised.
- **API behavior:** creation MUST reject empty uncertainty expressions; listings MUST NOT order by any stored preference.
- **Required tests:** creation without uncertainty fails; the schema exposes no ranking field to set. Cite ONT-INT-001, ONT-PRN-002.

### ONT-HYP-001 — Hypothesis

Refined per ONT-PRN-023 (Resolution 018 / ADR-0028) and the Session 012 amendments. A Hypothesis is a provisional, testable explanatory structure — the highest epistemic object authorized in the current ARGUS ontology (Understanding and Judgment remain human outcomes, never machine-authored objects; extending the ladder would require explicit constitutional review). Admissible only when the system can state what supports it, what limits it, what could challenge it, and what remains unknown.

- **Schema properties:** explanatory statement; reasoning description; the inherited uncertainty envelope (status + mandatory explanation); mandatory **testability statement** and **challenge condition** (declarations of what future evidence would matter — Article VII, never predictions); grounding snapshots to ≥1 same-case Interpretation with role `DERIVED_FROM` | `CONTEXTUALIZED_BY`, interpretation fingerprint v2, and link time — only `DERIVED_FROM` satisfies the minimum, and rung-skipping MUST be unrepresentable; the immutable creation-time alternative articulation (`alternative_articulation_at_creation` + absence explanation when none linked); Unknown and Contradiction articulation at creation (boundary link or explicit no-current explanation — silence is a refusal).
- **Invariants:** no terminal confirmed/true state exists to reach; no preference, probability, confidence, promotion, or refutation surface exists anywhere (contamination registry, structured surfaces); `hypothesis_health` (CURRENT/DEGRADED/UNSUPPORTED), `current_alternative_state`, `unknown_boundary_state`, and `contradiction_boundary_state` are derived, never stored; resolving/disposing/linking any boundary and retracting any sibling alter no stored Hypothesis field — even UNSUPPORTED never auto-retracts (Article II).
- **Validity boundaries are boundary-owned:** Unknown bounds via UnknownLink (target set extended to Hypothesis); Contradiction challenges via ContradictionLink (`CHALLENGED_BY_CONTRADICTION` only — no refutation relationship may ever be added). The positive epistemic object never owns its own constraints.
- **Audit events:** claim-created; claim-retracted; hypothesis-alternative-linked; contradiction-linked; unknown-linked (boundary side); grounding-flag raised (derived surfacing).
- **API behavior:** no endpoint may promote, rank, confirm, refute, or auto-close a hypothesis; the disclaimer, open Unknowns, Contradictions, alternatives, and all derived states MUST be retrievable with it (Articles III, IV, IX).
- **Required tests:** the canonical refusal matrix (CONSTITUTIONAL_PREDICATES.md) dual-rendered and conformance-swept; creation without testability/challenge/articulation fails; boundary resolution and sibling retraction leave hypotheses byte-identical; the creation-time absence explanation survives later alternative linking. Cite ONT-HYP-001, ONT-PRN-023, ONT-PRN-007.

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
| 1.4.0 | 2026-07-13 | D-PRN-018: semantic contamination registry with per-layer forbidden vocabulary and the release-blocking test obligation (Resolution 013 / ADR-0022). |
| 1.5.0 | 2026-07-13 | ONT-INT-001 obligations refined per Slice 2A amendments: uncertainty envelope, grounding snapshot/roles, comparative guard, derived grounding_health. |
| 1.6.0 | 2026-07-13 | ONT-HYP-001 obligations refined per ONT-PRN-023 (ADR-0028) and the five Session 012 amendments: four structural conditions, creation-time vs. derived alternative state, boundary-owned validity links, versioned fingerprints, three-state health. D-PRN-018 registry extended through the Hypothesis layer (recording the Unknown/Contradiction rows shipped with Slices 2B/2C) with the structured-surface scope caution. |
| 1.7.0 | 2026-07-13 | Added D-PRN-024 (constraint precedes expressive power, ADR-0029), D-PRN-025 (historical vs. current, ADR-0030), and D-REC (Case Reconstruction composition obligations, deferring to CASE_RECONSTRUCTION.md), per the Slice 3A gate (AGC Session 014). |
| 1.8.0 | 2026-07-13 | Added D-PRN-026 (integrity is never truth, ADR-0031), D-PRN-027 (no silent repair, ADR-0032), and D-REC-STORAGE (reconciliation detection obligations, deferring to STORAGE_RECONCILIATION.md), per the Slice 1E gate (AGC Session 016). |
| 1.9.0 | 2026-07-13 | Added D-PRN-028 (identity is authenticated, never asserted; the authentication/attribution/authority/epistemic separation, deferring to ACTOR_CONTEXT.md), per the Slice 1F-A gate (AGC Session 018). |
| 1.10.0 | 2026-07-13 | Added D-PRN-029 (authority governs actions and visibility, never truth) and D-PRN-030 (protected access explicit, least-privileged, auditable; two-stage visibility; audit before disclosure), deferring to AUTHORITY.md, per the Slice 1F-B gate (AGC Session 020). |
