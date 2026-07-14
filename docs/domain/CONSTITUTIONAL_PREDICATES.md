# ARGUS Constitutional Predicates

- **Document version:** 0.2.0 (0.1.0 ratified with Slice 1C, AGC Session 007; 0.2.0 adds the Slice 1D admissibility matrix, ADR-0020)
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
| `can_generate_hypothesis` | May these Interpretations ground a Hypothesis? | Slice 3+ |

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

## Acceptance test (per ADR-0018)

> **Can every constitutional predicate be derived identically by independent implementations?**

Experiment One: `can_support_observation`, every matrix row, Python decision vs. PostgreSQL decision — identical structural verdict, contextual verdict, and reason codes. This is ODE Hypothesis H2's first data point.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative artifact: predicate family, canonical reason codes, eligibility matrix (ADR-0018, Slice 1C plan review). Ratified with Slice 1C (AGC Session 007). |
| 0.2.0 | 2026-07-13 | Slice 1D: admissibility codes and the canonical validate_observation refusal matrix; is_grounded definition; locator validation rules; gold-standard fixture (ADR-0020). |
