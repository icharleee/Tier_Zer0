"""Epistemic admissibility — the Python rendering (ADR-0020, ODE H3).

Validation is distinct from persistence (Amendment 2): these are pure
functions from constitutional state to canonical reason codes, independently
testable, reused later by AI proposals, batch import, OCR, and external
integrations. PostgreSQL carries an independent rendering (migration 005);
the H3 conformance sweep compares the two against the canonical refusal
matrix in docs/domain/CONSTITUTIONAL_PREDICATES.md — the normative leg of
the triangulation (ONT-PRN-015).

An observation is admissible iff its code set is empty. Admissibility asks
whether the claim is constitutionally allowed to exist — reasoning begins at
Interpretation, not here.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import predicates
from .actors import ActorClass
from .models import ArtifactStatus, CaseStatus

# Canonical admissibility codes (normative registry: CONSTITUTIONAL_PREDICATES.md).
MISSING_STATEMENT = "ONT-PRN-005:missing-statement"
MISSING_METHOD = "ONT-PRN-005:missing-method"
ACTOR_NOT_PERMITTED = "ONT-PRN-007:actor-not-permitted"
NO_GROUNDING = "ONT-PRN-004:no-grounding"
UNKNOWN_LOCATOR = "ONT-SRC-001:unknown-locator"
LOCATOR_RETRACTED = "ONT-PRN-006:locator-retracted"
CROSS_CASE_GROUNDING = "ONT-PRN-004:cross-case-grounding"
ARTIFACT_NOT_ACTIVE = "ONT-SRC-001:artifact-not-active"
UNKNOWN_SCHEME = "ONT-SRC-001:unknown-scheme"
OUT_OF_BOUNDS = "ONT-SRC-001:out-of-bounds"
UNGROUNDED = "ONT-OBS-001:ungrounded"

LOCATOR_SCHEMES = frozenset({"byte-range", "time-range", "page-region"})


@dataclass(frozen=True)
class GroundingState:
    """The constitutional state of one referenced locator, as assembled by
    the caller (service layer or test fixture)."""

    exists: bool
    retracted: bool = False
    same_case: bool = True
    artifact_status: ArtifactStatus | None = None


def _int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def validate_source_locator(
    artifact_status: ArtifactStatus | None,
    scheme: str,
    payload: dict,
    size_bytes: int,
) -> tuple[str, ...]:
    """Locator admissibility (ONT-SRC-001): ACTIVE artifact, registered
    scheme, byte-range bounds objectively checked; time-range/page-region are
    scheme-declared with bounds deferred to the locator Standard."""
    codes: list[str] = []
    if artifact_status is not ArtifactStatus.ACTIVE:
        codes.append(ARTIFACT_NOT_ACTIVE)
    if scheme not in LOCATOR_SCHEMES:
        codes.append(UNKNOWN_SCHEME)
    elif scheme == "byte-range":
        start, end = _int(payload.get("start")), _int(payload.get("end"))
        if start is None or end is None or not (0 <= start < end <= size_bytes):
            codes.append(OUT_OF_BOUNDS)
    return tuple(sorted(set(codes)))


def validate_observation(
    *,
    statement: str,
    method_description: str,
    actor_class: ActorClass,
    case_status: CaseStatus,
    groundings: tuple[GroundingState, ...],
) -> tuple[str, ...]:
    """The canonical refusal matrix, rendered in Python. Codes are a
    deduplicated, sorted set; admissible iff empty."""
    codes: set[str] = set()

    if not statement or not statement.strip():
        codes.add(MISSING_STATEMENT)
    if not method_description or not method_description.strip():
        codes.add(MISSING_METHOD)
    if actor_class is not ActorClass.HUMAN:
        # Slice 1D scope: AI proposals arrive with the AI-integration ADR.
        codes.add(ACTOR_NOT_PERMITTED)

    if not groundings:
        codes.add(NO_GROUNDING)
    for g in groundings:
        if not g.exists:
            codes.add(UNKNOWN_LOCATOR)
            continue
        if g.retracted:
            codes.add(LOCATOR_RETRACTED)
        if not g.same_case:
            codes.add(CROSS_CASE_GROUNDING)
            continue  # eligibility is inherited for same-case groundings only
        eligibility = predicates.can_support_observation(g.artifact_status, case_status)
        codes.update(eligibility.reasons)

    return tuple(sorted(codes))


# ---- Interpretation admissibility (Slice 2A; ONT-INT-001) ----

MEANING_REQUIRED = "ONT-INT-001:meaning-required"
REASONING_REQUIRED = "ONT-INT-001:reasoning-required"
UNCERTAINTY_STATUS_REQUIRED = "ONT-INT-001:uncertainty-status-required"
UNCERTAINTY_EXPLANATION_REQUIRED = "ONT-INT-001:uncertainty-explanation-required"
UNSUPPORTED_ACTOR = "ONT-INT-001:unsupported-actor"
NO_GROUNDED_OBSERVATIONS = "ONT-INT-001:no-grounded-observations"
UNKNOWN_OBSERVATION = "ONT-INT-001:unknown-observation"
OBSERVATION_RETRACTED = "ONT-INT-001:observation-retracted"
OBSERVATION_UNGROUNDED = "ONT-INT-001:observation-ungrounded"
INT_CROSS_CASE = "ONT-INT-001:cross-case-grounding"
COMPARATIVE_RANKING = "ONT-INT-001:comparative-ranking-not-yet-modeled"
INVALID_GROUNDING_ROLE = "ONT-INT-001:invalid-grounding-role"

# Conservative lexical guard (Amendment 1): a heuristic tripwire, not a claim
# that semantic ranking is reliably detectable. Transcribed from the
# normative matrix (CONSTITUTIONAL_PREDICATES.md 0.3.0).
COMPARATIVE_GUARD_TERMS = (
    "more likely", "most likely", "more probable", "most probable",
    "stronger", "strongest", "weaker", "preferred",
    "primary explanation", "best explanation",
)

VALID_UNCERTAINTY_STATUSES = frozenset(
    {"ACKNOWLEDGED", "MATERIAL", "LIMITING", "UNRESOLVED"}
)
VALID_GROUNDING_ROLES = frozenset({"SUPPORTING", "LIMITING", "CONTEXTUAL"})


@dataclass(frozen=True)
class ObservationGroundingState:
    """The constitutional state of one observation an Interpretation would
    rely on, as assembled by the caller."""

    exists: bool
    retracted: bool = False
    grounded: bool = False  # is_grounded() at evaluation time
    same_case: bool = True
    role: str = "SUPPORTING"


def validate_interpretation(
    *,
    meaning_statement: str,
    reasoning_description: str,
    uncertainty_status: str | None,
    uncertainty_explanation: str,
    actor_class: ActorClass,
    groundings: tuple[ObservationGroundingState, ...],
    unresolved_unknown_named: bool | None = None,
) -> tuple[str, ...]:
    """The canonical interpretation refusal matrix, rendered in Python.
    Admissible iff empty. A valid Interpretation means only: this
    human-authored meaning is constitutionally admissible and traceable."""
    codes: set[str] = set()

    if not meaning_statement or not meaning_statement.strip():
        codes.add(MEANING_REQUIRED)
    if not reasoning_description or not reasoning_description.strip():
        codes.add(REASONING_REQUIRED)
    if uncertainty_status not in VALID_UNCERTAINTY_STATUSES:
        codes.add(UNCERTAINTY_STATUS_REQUIRED)
    if not uncertainty_explanation or not uncertainty_explanation.strip():
        codes.add(UNCERTAINTY_EXPLANATION_REQUIRED)
    if actor_class is not ActorClass.HUMAN:
        codes.add(UNSUPPORTED_ACTOR)

    prose = f"{meaning_statement or ''} {reasoning_description or ''}".lower()
    if any(term in prose for term in COMPARATIVE_GUARD_TERMS):
        codes.add(COMPARATIVE_RANKING)

    # Accumulated obligation (ONT-PRN-019 / Slice 2B): UNRESOLVED uncertainty
    # must name the specific evidentiary limit that produces it (Article IX).
    # unresolved_unknown_named: None = no unknown supplied; False = supplied
    # but nonexistent/cross-case; True = a valid same-case Unknown is named.
    if uncertainty_status == "UNRESOLVED" and unresolved_unknown_named is not True:
        codes.add(UNRESOLVED_REQUIRES_UNKNOWN)

    if not groundings:
        codes.add(NO_GROUNDED_OBSERVATIONS)
    for g in groundings:
        if g.role not in VALID_GROUNDING_ROLES:
            codes.add(INVALID_GROUNDING_ROLE)
        if not g.exists:
            codes.add(UNKNOWN_OBSERVATION)
            continue
        if g.retracted:
            codes.add(OBSERVATION_RETRACTED)
            continue
        if not g.same_case:
            codes.add(INT_CROSS_CASE)
            continue
        if not g.grounded:
            codes.add(OBSERVATION_UNGROUNDED)

    return tuple(sorted(codes))


# ---- Unknown admissibility (Slice 2B; ONT-UNK-001, ONT-PRN-020) ----

QUESTION_REQUIRED = "ONT-UNK-001:question-required"
NOT_A_QUESTION = "ONT-UNK-001:not-a-question"
TASK_SHAPED = "ONT-UNK-001:task-shaped-not-question"
UNK_UNSUPPORTED_ACTOR = "ONT-UNK-001:unsupported-actor"
UNKNOWN_TARGET = "ONT-UNK-001:unknown-target"
CROSS_CASE_LINK = "ONT-UNK-001:cross-case-link"
ANSWER_REQUIRES_EVIDENCE = "ONT-UNR-001:answer-requires-evidence"
RATIONALE_REQUIRED = "ONT-UNR-001:rationale-required"
UNRESOLVED_REQUIRES_UNKNOWN = "ONT-INT-001:unresolved-requires-named-unknown"

# Anti-TODO guard (conservative lexical heuristic, ADR-0024): Unknown is a
# question, never an investigative task. Transcribed from the normative
# matrix (CONSTITUTIONAL_PREDICATES.md 0.4.0).
TASK_STEMS = ("todo", "follow up", "assign", "remind", "need to")
TASK_LEADING_VERBS = ("interview ", "collect ", "obtain ", "request ")


def validate_unknown(question: str, actor_class: ActorClass) -> tuple[str, ...]:
    """Question-form admissibility: non-empty, interrogative, no task
    vocabulary. 'Who possessed the device between 19:42 and 20:15?' is
    exactly what Unknown represents; 'Interview the neighbor.' is not."""
    codes: set[str] = set()
    q = (question or "").strip()
    if not q:
        codes.add(QUESTION_REQUIRED)
    else:
        if not q.endswith("?"):
            codes.add(NOT_A_QUESTION)
        low = q.lower()
        if any(s in low for s in TASK_STEMS) or any(
            low.startswith(v) for v in TASK_LEADING_VERBS
        ):
            codes.add(TASK_SHAPED)
    if actor_class is not ActorClass.HUMAN:
        codes.add(UNK_UNSUPPORTED_ACTOR)
    return tuple(sorted(codes))


def validate_unknown_resolution(
    resolution_type: str,
    rationale: str,
    answering_claims: tuple[str, ...],
    actor_class: ActorClass,
) -> tuple[str, ...]:
    """Disposition admissibility: human-only, rationale required, and an
    answer without evidence is not an answer (Article I)."""
    codes: set[str] = set()
    if actor_class is not ActorClass.HUMAN:
        codes.add(ACTOR_NOT_PERMITTED)
    if not rationale or not rationale.strip():
        codes.add(RATIONALE_REQUIRED)
    if resolution_type in ("ANSWERED", "PARTIALLY_ANSWERED") and not answering_claims:
        codes.add(ANSWER_REQUIRES_EVIDENCE)
    return tuple(sorted(codes))


# ---- Contradiction admissibility (Slice 2C; ONT-CON/CNM/CDP-001) ----

CON_DESCRIPTION_REQUIRED = "ONT-CON-001:description-required"
CON_TYPE_REQUIRED = "ONT-CON-001:type-required"
CON_SCOPE_REQUIRED = "ONT-CON-001:scope-required"
CON_BASIS_REQUIRED = "ONT-CON-001:basis-required"
CON_INSUFFICIENT_MEMBERS = "ONT-CON-001:insufficient-members"
CON_DUPLICATE_MEMBERS = "ONT-CON-001:duplicate-members"
CON_UNSUPPORTED_ACTOR = "ONT-CON-001:unsupported-actor"
CON_ADJUDICATIVE_LANGUAGE = "ONT-CON-001:adjudicative-language"
CNM_UNKNOWN_MEMBER = "ONT-CNM-001:unknown-member"
CNM_MEMBER_RETRACTED = "ONT-CNM-001:member-retracted"
CNM_CROSS_CASE_MEMBER = "ONT-CNM-001:cross-case-member"
CNM_INVALID_ROLE = "ONT-CNM-001:invalid-member-role"
CDP_OUTCOME_REQUIRED = "ONT-CDP-001:outcome-required"
CDP_RATIONALE_REQUIRED = "ONT-CDP-001:rationale-required"

CONTRADICTION_TYPES = frozenset({
    "TEMPORAL", "SPATIAL", "IDENTITY", "CAUSAL", "DESCRIPTIVE",
    "NUMERIC", "PROCEDURAL", "PROVENANCE", "CUSTODY", "LOGICAL",
})
DISPOSITION_OUTCOMES = frozenset({
    "EXPLAINED", "NO_LONGER_APPLICABLE", "WITHDRAWN", "UNRESOLVED", "SUPERSEDED",
})
# Conservative adjudicative-language guard (heuristic tripwire): a
# Contradiction states joint impossibility; it never says who is right.
ADJUDICATIVE_GUARD_TERMS = (
    "is wrong", "is false", "refuted", "prevails", "is correct",
    "should be preferred", "winner",
)


@dataclass(frozen=True)
class MemberState:
    """The constitutional state of one proposed contradiction member."""

    exists: bool
    retracted: bool = False
    same_case: bool = True
    role: str = "INCOMPATIBLE_CLAIM"


def validate_contradiction(
    *,
    description: str,
    contradiction_type: str | None,
    scope_definition: str,
    incompatibility_basis: str,
    actor_class: ActorClass,
    members: tuple[MemberState, ...],
    distinct_member_count: int | None = None,
) -> tuple[str, ...]:
    """The canonical contradiction refusal matrix: at least two claims plus
    an explicit account of the shared scope and incompatibility that prevents
    their simultaneous truth. Mere disagreement never becomes formal
    contradiction."""
    codes: set[str] = set()
    if not description or not description.strip():
        codes.add(CON_DESCRIPTION_REQUIRED)
    if contradiction_type not in CONTRADICTION_TYPES:
        codes.add(CON_TYPE_REQUIRED)
    if not scope_definition or not scope_definition.strip():
        codes.add(CON_SCOPE_REQUIRED)
    if not incompatibility_basis or not incompatibility_basis.strip():
        codes.add(CON_BASIS_REQUIRED)
    if actor_class is not ActorClass.HUMAN:
        codes.add(CON_UNSUPPORTED_ACTOR)

    prose = f"{description or ''} {incompatibility_basis or ''}".lower()
    if any(t in prose for t in ADJUDICATIVE_GUARD_TERMS):
        codes.add(CON_ADJUDICATIVE_LANGUAGE)

    n_distinct = distinct_member_count if distinct_member_count is not None else len(members)
    if n_distinct < 2:
        codes.add(CON_INSUFFICIENT_MEMBERS)
    if distinct_member_count is not None and distinct_member_count < len(members):
        codes.add(CON_DUPLICATE_MEMBERS)
    for m in members:
        if m.role != "INCOMPATIBLE_CLAIM":
            codes.add(CNM_INVALID_ROLE)
        if not m.exists:
            codes.add(CNM_UNKNOWN_MEMBER)
            continue
        if m.retracted:
            codes.add(CNM_MEMBER_RETRACTED)
        if not m.same_case:
            codes.add(CNM_CROSS_CASE_MEMBER)
    return tuple(sorted(codes))


def validate_contradiction_disposition(
    outcome: str | None, rationale: str, actor_class: ActorClass
) -> tuple[str, ...]:
    codes: set[str] = set()
    if actor_class is not ActorClass.HUMAN:
        codes.add(ACTOR_NOT_PERMITTED)
    if outcome not in DISPOSITION_OUTCOMES:
        codes.add(CDP_OUTCOME_REQUIRED)
    if not rationale or not rationale.strip():
        codes.add(CDP_RATIONALE_REQUIRED)
    return tuple(sorted(codes))


# ---- Hypothesis admissibility (Slice 2D; ONT-HYP-001, ONT-PRN-023) ----
#
# An explanation is constitutionally admissible only when the system can
# state what supports it, what limits it, what could challenge it, and what
# remains unknown (Resolution 018). ARGUS may preserve explanations for
# examination; it may never convert explanation into verdict.

HYP_STATEMENT_REQUIRED = "ONT-HYP-001:statement-required"
HYP_REASONING_REQUIRED = "ONT-HYP-001:reasoning-required"
HYP_UNCERTAINTY_STATUS_REQUIRED = "ONT-HYP-001:uncertainty-status-required"
HYP_UNCERTAINTY_EXPLANATION_REQUIRED = "ONT-HYP-001:uncertainty-explanation-required"
HYP_TESTABILITY_REQUIRED = "ONT-HYP-001:testability-required"
HYP_CHALLENGE_CONDITION_REQUIRED = "ONT-HYP-001:challenge-condition-required"
HYP_UNSUPPORTED_ACTOR = "ONT-HYP-001:unsupported-actor"
HYP_DERIVATION_REQUIRED = "ONT-HYP-001:derivation-required"
HYP_INVALID_GROUNDING_ROLE = "ONT-HYP-001:invalid-grounding-role"
HYP_UNKNOWN_INTERPRETATION = "ONT-HYP-001:unknown-interpretation"
HYP_INTERPRETATION_RETRACTED = "ONT-HYP-001:interpretation-retracted"
HYP_INTERPRETATION_DEGRADED = "ONT-HYP-001:interpretation-degraded"
HYP_CROSS_CASE = "ONT-HYP-001:cross-case-grounding"
HYP_DUPLICATE_GROUNDING = "ONT-HYP-001:duplicate-grounding"
HYP_ALT_ARTICULATION_REQUIRED = "ONT-HYP-001:alternative-articulation-required"
HYP_ALT_ARTICULATION_CONFLICT = "ONT-HYP-001:alternative-articulation-conflict"
HYP_UNK_ARTICULATION_REQUIRED = "ONT-HYP-001:unknown-boundary-articulation-required"
HYP_UNK_ARTICULATION_CONFLICT = "ONT-HYP-001:unknown-boundary-articulation-conflict"
HYP_CON_ARTICULATION_REQUIRED = "ONT-HYP-001:contradiction-boundary-articulation-required"
HYP_CON_ARTICULATION_CONFLICT = "ONT-HYP-001:contradiction-boundary-articulation-conflict"
HYP_COMPARATIVE_LANGUAGE = "ONT-HYP-001:comparative-language"

ALT_SELF_LINK = "ONT-HYP-001:alt-self-link"
ALT_UNKNOWN_HYPOTHESIS = "ONT-HYP-001:alt-unknown-hypothesis"
ALT_CROSS_CASE = "ONT-HYP-001:alt-cross-case"
ALT_DUPLICATE = "ONT-HYP-001:alt-duplicate"
ALT_EXPLANATION_REQUIRED = "ONT-HYP-001:alt-explanation-required"
ALT_COMPARATIVE_LANGUAGE = "ONT-HYP-001:alt-comparative-language"

CONLINK_TARGET_NOT_FOUND = "ONT-CON-001:link-target-not-found"
CONLINK_CROSS_CASE = "ONT-CON-001:link-cross-case"
CONLINK_DUPLICATE = "ONT-CON-001:link-duplicate"
CONLINK_EXPLANATION_REQUIRED = "ONT-CON-001:link-explanation-required"
CONLINK_INVALID_RELATIONSHIP = "ONT-CON-001:link-invalid-relationship"

VALID_HYPOTHESIS_GROUNDING_ROLES = frozenset({"DERIVED_FROM", "CONTEXTUALIZED_BY"})
CHALLENGED_BY_CONTRADICTION = "CHALLENGED_BY_CONTRADICTION"


@dataclass(frozen=True)
class InterpretationGroundingState:
    """The constitutional state of one Interpretation a Hypothesis would
    rely on, as assembled by the caller."""

    exists: bool
    retracted: bool = False
    grounded: bool = False  # interpretation grounding_health == GROUNDED
    same_case: bool = True
    role: str = "DERIVED_FROM"


def _articulate(
    codes: set[str], link_count: int, explanation: str | None,
    required_code: str, conflict_code: str,
) -> None:
    """The Resolution 018 articulation rule: boundary link XOR explicit
    absence explanation. Silence is a refusal; contradiction of record
    (both at once) is a refusal."""
    has_explanation = bool(explanation and explanation.strip())
    if link_count <= 0 and not has_explanation:
        codes.add(required_code)
    if link_count > 0 and has_explanation:
        codes.add(conflict_code)


def validate_hypothesis(
    *,
    explanatory_statement: str,
    reasoning_description: str,
    uncertainty_status: str | None,
    uncertainty_explanation: str,
    testability_statement: str,
    challenge_condition: str,
    actor_class: ActorClass,
    groundings: tuple[InterpretationGroundingState, ...],
    distinct_grounding_count: int | None = None,
    alternative_link_count: int = 0,
    alternative_absence_explanation: str | None = None,
    unknown_link_count: int = 0,
    no_current_unknowns_explanation: str | None = None,
    contradiction_link_count: int = 0,
    no_current_contradictions_explanation: str | None = None,
) -> tuple[str, ...]:
    """The canonical hypothesis refusal matrix, rendered in Python.
    Admissible iff empty. A valid Hypothesis is admissible for
    examination — never likely, preferred, correct, or accepted."""
    codes: set[str] = set()

    if not explanatory_statement or not explanatory_statement.strip():
        codes.add(HYP_STATEMENT_REQUIRED)
    if not reasoning_description or not reasoning_description.strip():
        codes.add(HYP_REASONING_REQUIRED)
    if uncertainty_status not in VALID_UNCERTAINTY_STATUSES:
        codes.add(HYP_UNCERTAINTY_STATUS_REQUIRED)
    if not uncertainty_explanation or not uncertainty_explanation.strip():
        codes.add(HYP_UNCERTAINTY_EXPLANATION_REQUIRED)
    if not testability_statement or not testability_statement.strip():
        codes.add(HYP_TESTABILITY_REQUIRED)
    if not challenge_condition or not challenge_condition.strip():
        codes.add(HYP_CHALLENGE_CONDITION_REQUIRED)
    if actor_class is not ActorClass.HUMAN:
        # AI authorship NOT AUTHORIZED (Session 012 formal decision).
        codes.add(HYP_UNSUPPORTED_ACTOR)

    prose = f"{explanatory_statement or ''} {reasoning_description or ''}".lower()
    if any(term in prose for term in COMPARATIVE_GUARD_TERMS):
        codes.add(HYP_COMPARATIVE_LANGUAGE)

    # Supports: only DERIVED_FROM satisfies the minimum (Amendment 5).
    if not any(g.role == "DERIVED_FROM" for g in groundings):
        codes.add(HYP_DERIVATION_REQUIRED)
    if (
        distinct_grounding_count is not None
        and distinct_grounding_count < len(groundings)
    ):
        codes.add(HYP_DUPLICATE_GROUNDING)
    for g in groundings:
        if g.role not in VALID_HYPOTHESIS_GROUNDING_ROLES:
            codes.add(HYP_INVALID_GROUNDING_ROLE)
        if not g.exists:
            codes.add(HYP_UNKNOWN_INTERPRETATION)
            continue
        if g.retracted:
            codes.add(HYP_INTERPRETATION_RETRACTED)
            continue
        if not g.same_case:
            codes.add(HYP_CROSS_CASE)
            continue
        if not g.grounded:
            codes.add(HYP_INTERPRETATION_DEGRADED)

    # Limits, challenge, alternatives: articulation is mandatory — a
    # Hypothesis is never admitted merely because its author omitted every
    # limitation (Session 012, Amendment 3).
    _articulate(codes, alternative_link_count, alternative_absence_explanation,
                HYP_ALT_ARTICULATION_REQUIRED, HYP_ALT_ARTICULATION_CONFLICT)
    _articulate(codes, unknown_link_count, no_current_unknowns_explanation,
                HYP_UNK_ARTICULATION_REQUIRED, HYP_UNK_ARTICULATION_CONFLICT)
    _articulate(codes, contradiction_link_count, no_current_contradictions_explanation,
                HYP_CON_ARTICULATION_REQUIRED, HYP_CON_ARTICULATION_CONFLICT)

    return tuple(sorted(codes))


def validate_hypothesis_alternative(
    *,
    self_link: bool,
    both_exist: bool,
    same_case: bool,
    duplicate: bool,
    relation_explanation: str,
    actor_class: ActorClass,
) -> tuple[str, ...]:
    """The alternative-link refusal matrix (Session 012, Amendment 4).
    Naming an alternative confers no status on either side."""
    codes: set[str] = set()
    if actor_class is not ActorClass.HUMAN:
        codes.add(ACTOR_NOT_PERMITTED)
    if self_link:
        codes.add(ALT_SELF_LINK)
    if not both_exist:
        codes.add(ALT_UNKNOWN_HYPOTHESIS)
    elif not same_case:
        codes.add(ALT_CROSS_CASE)
    if duplicate:
        codes.add(ALT_DUPLICATE)
    if not relation_explanation or not relation_explanation.strip():
        codes.add(ALT_EXPLANATION_REQUIRED)
    elif any(t in relation_explanation.lower() for t in COMPARATIVE_GUARD_TERMS):
        codes.add(ALT_COMPARATIVE_LANGUAGE)
    return tuple(sorted(codes))


def validate_contradiction_link(
    *,
    both_exist: bool,
    same_case: bool,
    duplicate: bool,
    relationship_type: str,
    explanation: str,
    actor_class: ActorClass,
) -> tuple[str, ...]:
    """The boundary-link refusal matrix: a Contradiction challenges a
    Hypothesis; it never refutes, disproves, defeats, weakens, or
    invalidates it — no such relationship exists or may ever be added."""
    codes: set[str] = set()
    if actor_class is not ActorClass.HUMAN:
        codes.add(ACTOR_NOT_PERMITTED)
    if not both_exist:
        codes.add(CONLINK_TARGET_NOT_FOUND)
    elif not same_case:
        codes.add(CONLINK_CROSS_CASE)
    if duplicate:
        codes.add(CONLINK_DUPLICATE)
    if relationship_type != CHALLENGED_BY_CONTRADICTION:
        codes.add(CONLINK_INVALID_RELATIONSHIP)
    if not explanation or not explanation.strip():
        codes.add(CONLINK_EXPLANATION_REQUIRED)
    return tuple(sorted(codes))


def hypothesis_health(groundings: tuple[InterpretationGroundingState, ...]) -> str:
    """Derived, never stored (Amendment 5, three states): computed over
    DERIVED_FROM groundings only. CURRENT — every one unretracted and
    grounded; DEGRADED — at least one degraded, at least one current;
    UNSUPPORTED — none current: the historical explanation remains
    recorded, but its current derivational foundation no longer satisfies
    admission conditions. Even UNSUPPORTED never auto-retracts — human
    review remains required (Article II)."""
    derived = [g for g in groundings if g.role == "DERIVED_FROM"]
    current = [g for g in derived if g.exists and not g.retracted and g.grounded]
    if derived and len(current) == len(derived):
        return "CURRENT"
    if current:
        return "DEGRADED"
    return "UNSUPPORTED"


def current_alternative_state(counterpart_active: tuple[bool, ...]) -> str:
    """Derived, never stored (Amendment 2): the CURRENT state, kept apart
    from the immutable creation-time articulation which it never erases.
    One flag per alternative link: is the counterpart unretracted?"""
    if not counterpart_active:
        return "NO_CURRENT_ALTERNATIVES"
    if any(counterpart_active):
        return "ALTERNATIVES_CURRENT"
    return "ALTERNATIVES_DEGRADED"


def unknown_boundary_state(link_unresolved: tuple[bool, ...]) -> str:
    """Derived, never stored: one flag per unretracted LIMITED_BY_UNKNOWN
    link — is the linked Unknown still unresolved? Links are never silently
    removed; resolution changes only this derived value."""
    if not link_unresolved:
        return "NONE_ARTICULATED"
    if any(link_unresolved):
        return "LIMITS_CURRENT"
    return "LIMITS_RESOLVED"


def contradiction_boundary_state(link_undisposed: tuple[bool, ...]) -> str:
    """Derived, never stored: one flag per unretracted
    CHALLENGED_BY_CONTRADICTION link — is the linked Contradiction still
    undisposed? A disposed Contradiction remains historically linked."""
    if not link_undisposed:
        return "NONE_ARTICULATED"
    if any(link_undisposed):
        return "CHALLENGES_CURRENT"
    return "CHALLENGES_DISPOSED"


def contradiction_health(members: tuple[MemberState, ...]) -> str:
    """Derived, never stored (Amendment 3): CURRENT iff all members remain
    unretracted and available; else DEGRADED. Degradation is surfaced;
    disposition remains human — no auto-disposition, no member removal,
    no promotion, no admissibility change."""
    return (
        "CURRENT"
        if members and all(m.exists and not m.retracted for m in members)
        else "DEGRADED"
    )


def interpretation_grounding_health(
    groundings: tuple[ObservationGroundingState, ...],
) -> str:
    """Derived, never stored (Amendment 3): GROUNDED iff at least one
    grounding references an unretracted, grounded Observation; else DEGRADED.
    The system surfaces degradation; it never retracts or rewrites the
    Interpretation (Article II)."""
    return (
        "GROUNDED"
        if any(g.exists and not g.retracted and g.grounded for g in groundings)
        else "DEGRADED"
    )


def is_grounded(groundings: tuple[GroundingState, ...]) -> bool:
    """The only groundedness predicate (ADR-0020 §6): at least one
    constitutionally valid SourceLocator exists — not retracted, artifact
    ACTIVE. Nothing more; grading groundedness would be sufficiency in
    disguise (ONT-PRN-014). Derived, never stored; degradation is surfaced
    for human disposition, never auto-retracted (Article II)."""
    return any(
        g.exists and not g.retracted and g.artifact_status is ArtifactStatus.ACTIVE
        for g in groundings
    )
