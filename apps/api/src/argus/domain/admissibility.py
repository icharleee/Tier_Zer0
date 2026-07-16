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
