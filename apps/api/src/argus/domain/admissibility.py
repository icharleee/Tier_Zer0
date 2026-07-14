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
