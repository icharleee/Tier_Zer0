# ARGUS Constitutional Predicates

- **Document version:** 0.7.0 (0.6.0 ratified with Slice 2D; 0.7.0 adds the Slice 3A reconstruction refusal condition per the Session 014 amendments)
- **Date:** 2026-07-13
- **Established by:** [ADR-0018](../adr/0018-constitutional-predicates.md) (Founder Resolution 009, ONT-PRN-014)
- **Derived from:** [The ARGUS Ontology](ONTOLOGY.md) 1.6.0, [Entity Lifecycles](ENTITY_LIFECYCLES.md) 2.0.0, ADR-0007
- **Consumed by:** the Python predicate module, the PostgreSQL predicate functions, the conformance suite (ODE Experiment H2)

Objects answer *what exists*. Predicates answer *what is permitted*. A constitutional predicate is a **derived** permission question — computed from constitutional state, stored nowhere (the database never remembers what it can always prove — Resolution 005), and answered with canonical reason codes so that every refusal explains itself (Article III applied to the negative path: **the negative gate is the feature**).

**Eligibility is not sufficiency (ONT-PRN-014).** These predicates decide whether an artifact may *participate* in reasoning. Whether it *contains enough information* for a particular claim — a blurred photograph is eligible and may still not support a plate reading — is epistemic sufficiency: out of scope for v0.1, never to be collapsed into these predicates (Article IX).

## The predicate family

| Predicate | Question | Status |
|---|---|---|
| `can_support_observation` | May this artifact ground an Observation? | **Slice 1C — Experiment One** |
| `can_be_retracted` | May this actor retract this artifact now? | Derived from the transition registry (ONT-PRN-013: no second lifecycle rendering) |
| `can_be_sealed` / `can_be_unsealed` | May this actor (un)seal this artifact now? | Derived from the transition registry |
| `can_be_interpreted` | May this Observation ground an Interpretation? | Slice 2+ |
| `can_generate_hypothesis` | May these Interpretations ground a Hypothesis? | **Slice 2D — realized as `validate_hypothesis`** |

Every predicate MUST be: derived, never stored; refusal-explaining via canonical codes; independently rendered in Python and PostgreSQL with a conformance sweep proving identical decisions and identical codes.

## Canonical reason codes

Codes are stable identifiers (ADR-0011 discipline): `<ONT-rule>:<slug>`. Wording of human explanations may evolve; codes do not.

| Code | Meaning | Layer |
|---|---|---|
| `ONT-EVA-001:unknown-artifact` | No constitutional record exists | structural |
| `ONT-EVA-001:not-yet-verified` | `PENDING_VERIFICATION` — evidence exists but is not yet claimable | structural |
| `ONT-EVA-001:integrity-unresolved` | `QUARANTINED` — awaiting human disposition | structural |
| `ONT-PRN-006:retracted` | `RETRACTED` — superseded; readable, not claimable | structural |
| `ONT-EVA-001:sealed-access-restricted` | `SEALED` — access requires legal authority (authority evaluation arrives with authenticated context, Slice 1F) | contextual |
| `ONT-CAS-001:case-closed` | Case `CLOSED` — analytical writes frozen | contextual |
| `ONT-CAS-001:case-suspended` | Case `SUSPENDED` — analytical writes paused | contextual |
| `ONT-PRN-012:no-such-transition` | Requested transition absent from the allowed-predecessor registry | transition predicates |
| `ONT-PRN-007:actor-not-permitted` | Actor class may not perform this transition (in Slice 1D also: non-human authorship of locators/observations) | transition predicates, admissibility |
| `ONT-PRN-005:missing-statement` | Observation statement empty | admissibility |
| `ONT-PRN-005:missing-method` | Method description empty (Article III applies to humans too) | admissibility |
| `ONT-PRN-004:no-grounding` | Zero SourceLocators supplied — an ungrounded claim cannot exist | admissibility |
| `ONT-PRN-004:cross-case-grounding` | Grounding locator belongs to another Case (C3) | admissibility |
| `ONT-SRC-001:unknown-locator` | Referenced locator does not exist | admissibility |
| `ONT-PRN-006:locator-retracted` | Referenced locator is retracted | admissibility |
| `ONT-SRC-001:artifact-not-active` | Locator creation against a non-ACTIVE artifact | admissibility |
| `ONT-SRC-001:unknown-scheme` | Locator scheme not in the v0.1 registry (byte-range, time-range, page-region) | admissibility |
| `ONT-SRC-001:out-of-bounds` | byte-range payload outside artifact size, or malformed | admissibility |
| `ONT-OBS-001:ungrounded` | `is_grounded()` false: no constitutionally valid locator remains | derived groundedness |

## Canonical eligibility matrix — `can_support_observation` (normative)

Structural: can the artifact *possibly* support an Observation (objective). Contextual: can it do so *in this investigation* (structural AND context). Reasons accumulate — a quarantined artifact in a closed case reports both codes. Rows are exhaustive over artifact state × case state; this table is the source the renderings and the conformance sweep derive from, and eventually a generated artifact (ADR-0017 direction).

| Artifact state | Case state | Structural | Contextual | Reason codes |
|---|---|---|---|---|
| ACTIVE | OPEN | **Yes** | **Yes** | — |
| ACTIVE | SUSPENDED | Yes | No | case-suspended |
| ACTIVE | CLOSED | Yes | No | case-closed |
| PENDING_VERIFICATION | OPEN | No | No | not-yet-verified |
| PENDING_VERIFICATION | SUSPENDED | No | No | not-yet-verified, case-suspended |
| PENDING_VERIFICATION | CLOSED | No | No | not-yet-verified, case-closed |
| QUARANTINED | OPEN | No | No | integrity-unresolved |
| QUARANTINED | SUSPENDED | No | No | integrity-unresolved, case-suspended |
| QUARANTINED | CLOSED | No | No | integrity-unresolved, case-closed |
| RETRACTED | OPEN | No | No | retracted |
| RETRACTED | SUSPENDED | No | No | retracted, case-suspended |
| RETRACTED | CLOSED | No | No | retracted, case-closed |
| SEALED | OPEN | Yes | No *(pending authority model)* | sealed-access-restricted |
| SEALED | SUSPENDED | Yes | No | sealed-access-restricted, case-suspended |
| SEALED | CLOSED | Yes | No | sealed-access-restricted, case-closed |
| *(no record)* | any | No | No | unknown-artifact |

The SEALED/OPEN row is honestly "depends on authority": v0.1 has no authenticated authority context, so the answer is **No with the reason named**, upgrading to authority-dependent evaluation in Slice 1F. An eligibility system that guessed at authority would exceed its evidence (Article IX).

## Canonical admissibility matrix — `validate_observation` (normative, Slice 1D)

Validation is distinct from persistence (ADR-0020 Amendment 2): `validate_*` produces reason codes; `create_*` is nearly mechanical. Codes accumulate; an observation is admissible iff the code set is empty. Eligibility of each grounding locator's artifact is evaluated via `can_support_observation` and its codes are inherited.

| Condition | Codes emitted |
|---|---|
| Statement empty/whitespace | `ONT-PRN-005:missing-statement` |
| Method empty/whitespace | `ONT-PRN-005:missing-method` |
| Actor class ≠ HUMAN (Slice 1D scope; AI proposals arrive with the AI-integration ADR) | `ONT-PRN-007:actor-not-permitted` |
| Zero grounding locators | `ONT-PRN-004:no-grounding` |
| Any locator nonexistent | `ONT-SRC-001:unknown-locator` |
| Any locator retracted | `ONT-PRN-006:locator-retracted` |
| Any locator from another case | `ONT-PRN-004:cross-case-grounding` |
| Any locator's artifact/case fails `can_support_observation` | that predicate's codes, inherited |

**`is_grounded()` (derived, never stored):** true iff at least one constitutionally valid SourceLocator exists — locator not retracted AND its artifact ACTIVE. Nothing more; graded groundedness was proposed and retracted in-session as sufficiency in disguise (ADR-0020 §6, ONT-PRN-014).

**Locator validation:** artifact must be ACTIVE (`artifact-not-active`); scheme in registry (`unknown-scheme`); `byte-range` payload `{start,end}` integers with `0 ≤ start < end ≤ size_bytes` (`out-of-bounds`); `time-range`/`page-region` are scheme-declared, bounds-checking deferred to the locator Standard (recorded, not hidden).

**Gold-standard fixture:** the first Observation is *"Blue sedan visible."* — nothing about intent, identity, or speed; nothing inferred; only what can be directly observed.

## Canonical admissibility matrix — `validate_interpretation` (normative, Slice 2A)

**What a valid Interpretation means:** *this human-authored meaning is constitutionally admissible and traceable.* It does **not** mean correct, preferred, complete, likely, accepted by the investigation, or endorsed by ARGUS. (This disclaimer eventually reaches the UI.)

**Structured uncertainty envelope (Amendment 2 — not a confidence scale, never probability):** `uncertainty_status` ∈ `ACKNOWLEDGED` (uncertainty exists but does not prevent stating the interpretation) | `MATERIAL` (meaningfully affects how it should be understood) | `LIMITING` (available observations constrain it substantially) | `UNRESOLVED` (a named unresolved issue prevents stronger expression) — plus mandatory `uncertainty_explanation`. There is deliberately no "certain" status: ARGUS preserves the distinction between *none identified* and *none exists* (Article IX). Canonical minimum-uncertainty wording: status `ACKNOWLEDGED`, explanation "No material uncertainty has been identified from the cited observations, but the interpretation remains provisional."

**Grounding snapshot (Amendment 3):** each grounding records the observation, its `statement_fingerprint` (SHA-256 of the statement relied upon — observations are immutable, so id + fingerprint is the revision snapshot), a `grounding_role` ∈ `SUPPORTING` | `LIMITING` | `CONTEXTUAL` (no CONTRADICTING while Contradiction is out of scope — a limiting observation is not a formal contradiction), and `linked_at`. **`grounding_health`** is derived, never stored: `GROUNDED` iff ≥ 1 grounding references an unretracted, grounded Observation; else `DEGRADED` — surfaced for human disposition, never auto-retracted.

**Comparative-vocabulary guard (Amendment 1 — a conservative lexical heuristic, not a claim that semantic ranking is reliably detectable):** meaning and reasoning text may describe, distinguish, and identify evidence bearing on alternatives, but may not make quantified or ordinal comparative-strength claims. Guarded terms (case-insensitive substrings): `more likely`, `most likely`, `more probable`, `most probable`, `stronger`, `strongest`, `weaker`, `preferred`, `primary explanation`, `best explanation`. Safe fixture: *"This interpretation differs from INT-000001 because it treats the visible vehicle as stationary rather than arriving."* Comparative assessment later becomes its own governed object, never unrestricted prose.

| Condition | Codes emitted |
|---|---|
| Meaning statement empty | `ONT-INT-001:meaning-required` |
| Reasoning description empty | `ONT-INT-001:reasoning-required` |
| Uncertainty status absent/invalid | `ONT-INT-001:uncertainty-status-required` |
| Uncertainty explanation empty | `ONT-INT-001:uncertainty-explanation-required` |
| Actor class ≠ HUMAN | `ONT-INT-001:unsupported-actor` |
| Zero grounding observations | `ONT-INT-001:no-grounded-observations` |
| Referenced observation nonexistent | `ONT-INT-001:unknown-observation` |
| Referenced observation retracted | `ONT-INT-001:observation-retracted` |
| Referenced observation ungrounded | `ONT-INT-001:observation-ungrounded` |
| Grounding from another case | `ONT-INT-001:cross-case-grounding` |
| Guarded comparative vocabulary present | `ONT-INT-001:comparative-ranking-not-yet-modeled` |
| Invalid grounding role | `ONT-INT-001:invalid-grounding-role` |

## Canonical admissibility matrix — `validate_unknown` (normative, Slice 2B)

An Unknown says exactly one thing: *this question currently has no constitutionally admissible answer* (ONT-PRN-020). It is never a task, reminder, or hypothesis-in-waiting. NULL is not Unknown; missing rows are not Unknown — negative knowledge is a deliberate epistemic object.

**Question-form guard (conservative lexical heuristic, like the comparative guard):** the question must be non-empty, interrogative in form (ends with `?`), and free of task vocabulary. Anti-TODO stems (case-insensitive): `todo`, `follow up`, `assign`, `remind`, `need to`, and leading action verbs `interview `, `collect `, `obtain `, `request `. Admissible gold fixture: *"Who possessed the device between 19:42 and 20:15?"* — investigative actions are refused; investigative questions are exactly what Unknown represents.

| Condition | Codes emitted |
|---|---|
| Question empty/whitespace | `ONT-UNK-001:question-required` |
| Not interrogative form (no `?`) | `ONT-UNK-001:not-a-question` |
| Task vocabulary present | `ONT-UNK-001:task-shaped-not-question` |
| Actor class ≠ HUMAN (AI suggestion deferred) | `ONT-UNK-001:unsupported-actor` |
| Link target nonexistent / cross-case | `ONT-UNK-001:unknown-target` / `ONT-UNK-001:cross-case-link` |
| Resolution `ANSWERED`/`PARTIALLY_ANSWERED` without ≥1 claim reference | `ONT-UNR-001:answer-requires-evidence` |
| Resolution rationale empty | `ONT-UNR-001:rationale-required` |
| Resolution by non-human actor | `ONT-PRN-007:actor-not-permitted` |

**The accumulated Interpretation obligation (ONT-PRN-019):** when `uncertainty_status = UNRESOLVED`, the Interpretation MUST name its Unknown — code `ONT-INT-001:unresolved-requires-named-unknown`. This is the first admissibility rule that reads the negative space: uncertainty relates to the specific evidentiary limit that produces it (Article IX). Nothing inherited is weakened; one obligation is added.

**Unknown scope (derived, never stored — recorded for the ontology, implementation deferred beyond v0.1):** an Unknown linking only Observations is *observational*; linking Interpretations, *interpretive*; later linking Hypotheses, *explanatory*. Computed from `unknown_links` targets per ONT-PRN-013.

**The H5 negative obligations:** an open Unknown changes nothing it bounds; no validator consumes Unknown state except the named-unknown rule above (which demands a *reference*, not a *conclusion*); resolving an Unknown alters no linked record — newly acquired knowledge never propagates as automated reasoning; linked Interpretations change only through explicit human reconsideration.

## Canonical admissibility matrix — `validate_contradiction` (normative, Slice 2C)

**The decisive rule:** a Contradiction may state that claims cannot all fit the same reality. It may never decide which claim reality favors. Coexistence concerns what the ledger may preserve; incompatibility concerns what reality may permit.

**Explicit incompatibility basis (Amendment 1):** two different Interpretations are not automatically contradictory — differing descriptions may concern different times, scopes, or definitions. Every Contradiction requires: `contradiction_type` ∈ {`TEMPORAL`, `SPATIAL`, `IDENTITY`, `CAUSAL`, `DESCRIPTIVE`, `NUMERIC`, `PROCEDURAL`, `PROVENANCE`, `CUSTODY`, `LOGICAL`}; `scope_definition` (the shared conditions under which the claims conflict — same vehicle, same camera, same interval, same meaning of "moving"); `incompatibility_basis` (why simultaneous truth is impossible under that scope). Mere disagreement never becomes formal contradiction.

**Member roles (Amendment 4):** every ContradictionMember in v0.1 is an `INCOMPATIBLE_CLAIM` — participation without direction. Contextual material is cited as provenance for the incompatibility basis, not as members. Directional vocabulary (supporting, refuting, prevailing, challenged, correct, false) is prohibited permanently.

**Member snapshots:** each member records `member_type`, `member_id`, the statement/meaning fingerprint at recognition time, and `linked_at` — proving which versions were judged incompatible.

**`contradiction_health` (Amendment 3 — derived, never stored):** `CURRENT` iff all members remain unretracted and grounded/available; else `DEGRADED`. Degradation is surfaced; it never auto-disposes, removes a member, promotes a claim, or alters any member's admissibility. Boundary degradation is surfaced; disposition remains human.

**Disposition (ADR-0027):** derived from the ContradictionDisposition record — `EXPLAINED`, `NO_LONGER_APPLICABLE`, `WITHDRAWN`, `UNRESOLVED`, `SUPERSEDED` — human-only, rationale required, terminal, and **no outcome implies a member was proven correct**. Operational state (`OPEN ⇄ UNDER_REVIEW`) is stewardship only.

| Condition | Codes emitted |
|---|---|
| Description empty | `ONT-CON-001:description-required` |
| Type absent/invalid | `ONT-CON-001:type-required` |
| Scope definition empty | `ONT-CON-001:scope-required` |
| Incompatibility basis empty | `ONT-CON-001:basis-required` |
| Fewer than 2 distinct members | `ONT-CON-001:insufficient-members` |
| Duplicate members | `ONT-CON-001:duplicate-members` |
| Actor class ≠ HUMAN | `ONT-CON-001:unsupported-actor` |
| Adjudicative language in description/basis (guard: "is wrong", "is false", "refuted", "prevails", "is correct", "should be preferred", "winner") | `ONT-CON-001:adjudicative-language` |
| Member nonexistent / retracted / cross-case | `ONT-CNM-001:unknown-member` / `ONT-CNM-001:member-retracted` / `ONT-CNM-001:cross-case-member` |
| Invalid member role | `ONT-CNM-001:invalid-member-role` |
| Disposition outcome absent/invalid | `ONT-CDP-001:outcome-required` |
| Disposition rationale empty | `ONT-CDP-001:rationale-required` |
| Disposition by non-human | `ONT-PRN-007:actor-not-permitted` |

**Gold fixture (mutually exclusive under shared scope):** A: *"The visible vehicle is stationary throughout 19:42:00–19:42:10."* B: *"The visible vehicle changes position during 19:42:00–19:42:10."* Scope: same vehicle, camera, coordinate frame, and interval.

## Canonical admissibility matrix — `validate_hypothesis` (normative, Slice 2D)

**What a valid Hypothesis means (ONT-PRN-023, verbatim disclaimer):** *a Hypothesis is a provisional, testable explanatory structure; its existence means only that it is admissible for examination — not that ARGUS considers it likely, preferred, correct, or accepted.* Hypothesis is the highest epistemic object authorized in the current ARGUS ontology; Understanding and Judgment remain human outcomes and are not represented as machine-authored epistemic objects. The governing rule: **ARGUS may preserve explanations for examination; it may never convert explanation into verdict.**

**The four conditions of Resolution 018, rendered structurally.** An explanation is admissible only when the system can state what supports it, what limits it, what could challenge it, and what remains unknown:

1. **Supports (existence relationships):** ≥1 `DERIVED_FROM` grounding referencing an unretracted, currently-grounded same-case Interpretation. `CONTEXTUALIZED_BY` groundings are optional and never satisfy the minimum — a Hypothesis containing only contextual links is inadmissible. Rung-skipping is structurally unrepresentable (groundings reference `interpretations.id` by foreign key); an attempt to ground on any other object surfaces as `unknown-interpretation`.
2. **Limits (Unknown articulation):** either ≥1 Unknown linked `LIMITED_BY_UNKNOWN` (an `UnknownLink` targeting the Hypothesis, created by the boundary object's own mechanism) **or** a non-empty `no_current_unknowns_explanation`. The explanation states that no specific unresolved gap is *presently articulated* — never that no unknowns exist.
3. **Challenge (Contradiction articulation + falsifiability):** either ≥1 Contradiction linked `CHALLENGED_BY_CONTRADICTION` (a `ContradictionLink`) **or** a non-empty `no_current_contradictions_explanation` (absence means no formal contradiction is currently linked — not that the Hypothesis is uncontradicted in reality). Plus the mandatory `testability_statement` and `challenge_condition` — declarations of what future evidence would matter, not predictions.
4. **Unknown (the inherited envelope):** `uncertainty_status` (same envelope as Interpretation, no "certain") plus mandatory `uncertainty_explanation`.

**Alternative articulation (Article IV, Session 012 Amendment 2 — creation-time record separated from current derived state):** at creation the author either links ≥1 existing same-case Hypothesis as a symmetric alternative or supplies a non-empty `alternative_absence_explanation` (what alternative space was considered and why none is currently articulable). The immutable `alternative_articulation_at_creation` ∈ `ALTERNATIVE_LINKED_AT_CREATION` | `NONE_CURRENTLY_ARTICULATED_AT_CREATION` records the historical fact; **`current_alternative_state`** is derived, never stored: `ALTERNATIVES_CURRENT` (≥1 link whose counterpart is unretracted) | `NO_CURRENT_ALTERNATIVES` (no links) | `ALTERNATIVES_DEGRADED` (links exist, every counterpart retracted). A later link changes the derived state without touching the original Hypothesis's bytes; the creation-time absence explanation remains historical truth.

**Grounding snapshots (interpretation fingerprint v2 — exact, versioned; implementations may not choose field sets silently):** each grounding records `hypothesis_id`, `interpretation_id`, `interpretation_fingerprint`, `grounding_role` ∈ `DERIVED_FROM` | `CONTEXTUALIZED_BY`, `linked_at`. Fingerprint v2 = SHA-256 over the UTF-8 encoding of `meaning_statement` ‖ 0x1F ‖ `reasoning_description` ‖ 0x1F ‖ `uncertainty_status` ‖ 0x1F ‖ `uncertainty_explanation` (U+001F unit separator; fields in exactly this order). The Slice 2A single-field statement fingerprint remains v1 where already deployed.

**Hypothesis fingerprint v1 (for ContradictionLink snapshots):** SHA-256 over the UTF-8 encoding of `explanatory_statement` ‖ 0x1F ‖ `reasoning_description` ‖ 0x1F ‖ `uncertainty_status` ‖ 0x1F ‖ `uncertainty_explanation` ‖ 0x1F ‖ `testability_statement` ‖ 0x1F ‖ `challenge_condition`.

**`hypothesis_health` (derived, never stored — three states per Session 012 Amendment 5):** `CURRENT` — every `DERIVED_FROM` Interpretation remains unretracted and grounded; `DEGRADED` — at least one has degraded but at least one remains current; `UNSUPPORTED` — no `DERIVED_FROM` Interpretation remains current (the historical explanation remains recorded, but its current derivational foundation no longer satisfies admission conditions). Even `UNSUPPORTED` never auto-retracts anything; human review remains required. `CONTEXTUALIZED_BY` groundings never enter the computation.

**Boundary states (derived, never stored; links are never silently removed):** `unknown_boundary_state` ∈ `LIMITS_CURRENT` (≥1 unretracted link whose Unknown is unresolved) | `LIMITS_RESOLVED` (≥1 unretracted link, all linked Unknowns resolved) | `NONE_ARTICULATED` (no unretracted links; the creation-time explanation stands as history). `contradiction_boundary_state` ∈ `CHALLENGES_CURRENT` | `CHALLENGES_DISPOSED` | `NONE_ARTICULATED`, identically over ContradictionLinks and dispositions. Resolving an Unknown or disposing a Contradiction changes only these derived values — never any stored Hypothesis field (no automatic revision, promotion, or refutation).

**Prohibited surfaces (Resolution 018; contamination registry, structured surfaces only per the Session 012 caution):** no field, enum value, function name, or constraint may carry `probability`, `confidence_score`, `preferred`, `primary`, `leading`, `best_fit`, `winner`, `case_theory`, `accepted`, or any refutation vocabulary (`refuted`, `disproven`, `defeated`, `weakened`, `invalidated`). Prose passes only the conservative comparative guard below; forbidden-word scanning is a tripwire, never proof of semantic cleanliness.

**Comparative-language guard (inherited from Slice 2A, same conservative term list):** explanatory and reasoning prose may describe and distinguish; it may not make quantified or ordinal comparative-strength claims. Same guarded terms as `validate_interpretation`; the alternative-link `relation_explanation` passes the same guard (naming an alternative confers no status on either side).

| Condition | Codes emitted |
|---|---|
| Explanatory statement empty | `ONT-HYP-001:statement-required` |
| Reasoning description empty | `ONT-HYP-001:reasoning-required` |
| Uncertainty status absent/invalid | `ONT-HYP-001:uncertainty-status-required` |
| Uncertainty explanation empty | `ONT-HYP-001:uncertainty-explanation-required` |
| Testability statement empty | `ONT-HYP-001:testability-required` |
| Challenge condition empty | `ONT-HYP-001:challenge-condition-required` |
| Actor class ≠ HUMAN (AI authorship NOT AUTHORIZED) | `ONT-HYP-001:unsupported-actor` |
| Zero `DERIVED_FROM` groundings (incl. contextual-only) | `ONT-HYP-001:derivation-required` |
| Invalid grounding role | `ONT-HYP-001:invalid-grounding-role` |
| Referenced interpretation nonexistent (incl. rung-skip attempts) | `ONT-HYP-001:unknown-interpretation` |
| Referenced interpretation retracted | `ONT-HYP-001:interpretation-retracted` |
| Referenced interpretation ungrounded (grounding_health DEGRADED) | `ONT-HYP-001:interpretation-degraded` |
| Grounding from another case | `ONT-HYP-001:cross-case-grounding` |
| Duplicate interpretation reference | `ONT-HYP-001:duplicate-grounding` |
| Neither alternative link nor absence explanation | `ONT-HYP-001:alternative-articulation-required` |
| Both alternative link and absence explanation | `ONT-HYP-001:alternative-articulation-conflict` |
| Neither Unknown link nor no-current-unknowns explanation | `ONT-HYP-001:unknown-boundary-articulation-required` |
| Both Unknown link and explanation | `ONT-HYP-001:unknown-boundary-articulation-conflict` |
| Neither Contradiction link nor no-current-contradictions explanation | `ONT-HYP-001:contradiction-boundary-articulation-required` |
| Both Contradiction link and explanation | `ONT-HYP-001:contradiction-boundary-articulation-conflict` |
| Guarded comparative vocabulary in statement/reasoning | `ONT-HYP-001:comparative-language` |

**Alternative-link operation (`link_hypothesis_alternative` — Session 012 Amendment 4):** human actor; no self-link; both Hypotheses same-case; normalized unordered pair (lexicographically smaller id first); no duplicate pair; non-empty `relation_explanation` free of the guarded comparative terms; audit event `hypothesis-alternative-linked` appended atomically; neither Hypothesis modified; the link survives either side's retraction (a retracted alternative never silently vanishes from history).

| Condition | Codes emitted |
|---|---|
| Non-human actor | `ONT-PRN-007:actor-not-permitted` |
| Self-link | `ONT-HYP-001:alt-self-link` |
| Either hypothesis nonexistent | `ONT-HYP-001:alt-unknown-hypothesis` |
| Cross-case pair | `ONT-HYP-001:alt-cross-case` |
| Duplicate pair | `ONT-HYP-001:alt-duplicate` |
| Relation explanation empty | `ONT-HYP-001:alt-explanation-required` |
| Guarded comparative vocabulary in relation explanation | `ONT-HYP-001:alt-comparative-language` |

**Contradiction-link operation (`link_contradiction` — boundary-owned, Contradiction → Hypothesis):** `relationship_type` = `CHALLENGED_BY_CONTRADICTION` only (`refuted`/`disproven`/`defeated`/`weakened`/`invalidated` do not exist and may never be added); human actor; same-case; hypothesis fingerprint v1 snapshot; non-empty explanation; audit event `contradiction-linked`; alters neither the Contradiction nor the Hypothesis. A disposed Contradiction remains historically linked — its current boundary activity is derived, the link never silently removed. Link errors follow the retract pattern (class V), mirroring UnknownLink.

| Condition | Codes emitted |
|---|---|
| Non-human actor | `ONT-PRN-007:actor-not-permitted` |
| Contradiction or Hypothesis nonexistent | `ONT-CON-001:link-target-not-found` |
| Cross-case link | `ONT-CON-001:link-cross-case` |
| Duplicate link (same contradiction, same hypothesis) | `ONT-CON-001:link-duplicate` |
| Explanation empty | `ONT-CON-001:link-explanation-required` |
| Relationship type ≠ CHALLENGED_BY_CONTRADICTION | `ONT-CON-001:link-invalid-relationship` |

**UnknownLink target extension:** `Hypothesis` joins the permitted target set (`LIMITED_BY_UNKNOWN` semantics); existing codes `ONT-UNK-001:unknown-target` / `ONT-UNK-001:cross-case-link` apply unchanged.

**Gold fixtures:** explanatory statement *"The sedan visible at 19:42 was already parked before the recording interval began."* — canonical absence explanations: alternatives — *"No alternative explanation is currently articulated: the alternative space considered (arrival or departure during the interval) is not yet supported by any grounded Interpretation."*; unknowns — *"No specific unresolved gap is presently articulated for this explanation; unknowns may exist that have not been recognized."*; contradictions — *"No formal contradiction is currently linked; this does not assert the explanation is uncontradicted in reality."*

## Case reconstruction refusal (Slice 3A)

The Case Reconstruction is a transient, read-only projection — not a predicate and not an epistemic object (see [CASE_RECONSTRUCTION.md](CASE_RECONSTRUCTION.md), which carries its manifest, visibility envelope, structural non-preference rules, and prohibited-key registry). Its single refusal condition:

| Condition | Code |
|---|---|
| Case does not exist | `ONT-CAS-001:unknown-case` |

An empty case reconstructs validly; emptiness is not an error. `audit_chain.integrity_status` ∈ `CHAIN_VALID` | `CHAIN_INVALID` | `CHAIN_NOT_VERIFIED` means chain integrity only — never that evidence, claims, or the case are "verified" — and `CHAIN_INVALID` never prevents reconstruction.

## Acceptance test (per ADR-0018)

> **Can every constitutional predicate be derived identically by independent implementations?**

Experiment One: `can_support_observation`, every matrix row, Python decision vs. PostgreSQL decision — identical structural verdict, contextual verdict, and reason codes. This is ODE Hypothesis H2's first data point.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative artifact: predicate family, canonical reason codes, eligibility matrix (ADR-0018, Slice 1C plan review). Ratified with Slice 1C (AGC Session 007). |
| 0.2.0 | 2026-07-13 | Slice 1D: admissibility codes and the canonical validate_observation refusal matrix; is_grounded definition; locator validation rules; gold-standard fixture (ADR-0020). Ratified with Slice 1D (AGC Session 006). |
| 0.3.0 | 2026-07-13 | Slice 2A: interpretation admissibility matrix, structured uncertainty envelope, grounding snapshot + roles + derived grounding_health, comparative-vocabulary guard, the admissibility disclaimer (Slice 2A plan review amendments). Ratified with Slice 2A (AGC Session 007). |
| 0.4.0 | 2026-07-13 | Slice 2B: unknown admissibility matrix, question-form/anti-TODO guard, resolution evidence requirements, derived unknown scope (deferred), UNRESOLVED-names-its-Unknown accumulated obligation, H5 negative obligations (AGC Session 008 amendments). Ratified with Slice 2B (AGC Session 009). |
| 0.5.0 | 2026-07-13 | Slice 2C: contradiction admissibility matrix — explicit incompatibility basis (type/scope/basis), INCOMPATIBLE_CLAIM member role, member snapshots, derived contradiction_health, ADR-0027 disposition outcomes, adjudicative-language guard (AGC Session 010 amendments). |
| 0.6.0 | 2026-07-13 | Slice 2D: hypothesis admissibility matrix per ONT-PRN-023 (ADR-0028) and the five Session 012 amendments — four structural conditions, creation-time vs. derived alternative state, mandatory Unknown/Contradiction articulation, versioned fingerprints (interpretation v2, hypothesis v1), three-state hypothesis_health, alternative-link and contradiction-link operations. |
| 0.7.0 | 2026-07-13 | Slice 3A: reconstruction refusal condition (unknown-case), audit-chain integrity enum semantics, pointer to the Case Reconstruction Specification (AGC Session 014 amendments). |
