"""Constitutional predicates (ADR-0018, ONT-PRN-014).

Objects answer "what exists"; predicates answer "what is permitted."
Every predicate here is DERIVED from constitutional state and stored nowhere
(Resolution 005: the database never remembers what it can always prove), and
every refusal names its canonical reason codes (the negative gate is the
feature — Article III applied to the negative path).

This module is the Python rendering. PostgreSQL carries an independent
rendering (argus_private.can_support_observation, migration 004) derived from
the same canonical matrix in docs/domain/CONSTITUTIONAL_PREDICATES.md; the
conformance sweep proves identical decisions and identical codes — ODE
Hypothesis H2, Experiment One.

Eligibility is not sufficiency (ONT-PRN-014): these predicates decide whether
an artifact may PARTICIPATE in reasoning, never whether it contains enough
information for a particular claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from .actors import ActorClass
from .models import ArtifactStatus, CaseStatus

# Canonical reason codes (normative registry: CONSTITUTIONAL_PREDICATES.md).
UNKNOWN_ARTIFACT = "ONT-EVA-001:unknown-artifact"
NOT_YET_VERIFIED = "ONT-EVA-001:not-yet-verified"
INTEGRITY_UNRESOLVED = "ONT-EVA-001:integrity-unresolved"
RETRACTED = "ONT-PRN-006:retracted"
SEALED_ACCESS_RESTRICTED = "ONT-EVA-001:sealed-access-restricted"
CASE_CLOSED = "ONT-CAS-001:case-closed"
CASE_SUSPENDED = "ONT-CAS-001:case-suspended"
NO_SUCH_TRANSITION = "ONT-PRN-012:no-such-transition"
ACTOR_NOT_PERMITTED = "ONT-PRN-007:actor-not-permitted"


@dataclass(frozen=True)
class PredicateDecision:
    predicate: str
    structurally_eligible: bool
    contextually_eligible: bool
    reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.contextually_eligible


def can_support_observation(
    artifact_status: ArtifactStatus | None, case_status: CaseStatus
) -> PredicateDecision:
    """May this artifact ground an Observation? (Canonical matrix,
    CONSTITUTIONAL_PREDICATES.md.)

    Structural: could it possibly (objective — verified, uncorrupted,
    constitutionally recorded). Contextual: may it, in this investigation
    (structural AND case open AND not sealed). Reasons accumulate across
    both layers. Pass artifact_status=None for a nonexistent record.
    """
    reasons: list[str] = []

    if artifact_status is None:
        return PredicateDecision(
            "can_support_observation", False, False, (UNKNOWN_ARTIFACT,)
        )

    structural = True
    if artifact_status is ArtifactStatus.PENDING_VERIFICATION:
        structural = False
        reasons.append(NOT_YET_VERIFIED)
    elif artifact_status is ArtifactStatus.QUARANTINED:
        structural = False
        reasons.append(INTEGRITY_UNRESOLVED)
    elif artifact_status is ArtifactStatus.RETRACTED:
        structural = False
        reasons.append(RETRACTED)

    # Contextual layer. SEALED is structurally sound but access-restricted:
    # v0.1 has no authenticated authority context, so the honest answer is
    # "no, with the reason named" until Slice 1F (Article IX — never guess
    # at authority).
    if artifact_status is ArtifactStatus.SEALED:
        reasons.append(SEALED_ACCESS_RESTRICTED)
    if case_status is CaseStatus.CLOSED:
        reasons.append(CASE_CLOSED)
    elif case_status is CaseStatus.SUSPENDED:
        reasons.append(CASE_SUSPENDED)

    return PredicateDecision(
        "can_support_observation",
        structurally_eligible=structural,
        contextually_eligible=not reasons,
        reasons=tuple(reasons),
    )


def _transition_predicate(
    name: str,
    from_status: ArtifactStatus,
    to_status: ArtifactStatus,
    action: str,
    actor_class: ActorClass,
) -> PredicateDecision:
    """Transition-authority predicates derive from the transition registry —
    the single derived rendering of Entity Lifecycles §2 in Python — so no
    second lifecycle source is created (ONT-PRN-013)."""
    from .transitions import ALLOWED_ARTIFACT_TRANSITIONS

    entry = ALLOWED_ARTIFACT_TRANSITIONS.get((from_status, to_status))
    if entry is None or entry[0] != action:
        return PredicateDecision(name, False, False, (NO_SUCH_TRANSITION,))
    if actor_class not in entry[1]:
        return PredicateDecision(name, True, False, (ACTOR_NOT_PERMITTED,))
    return PredicateDecision(name, True, True, ())


def can_be_retracted(
    artifact_status: ArtifactStatus, actor_class: ActorClass
) -> PredicateDecision:
    return _transition_predicate(
        "can_be_retracted",
        artifact_status,
        ArtifactStatus.RETRACTED,
        "artifact-retracted",
        actor_class,
    )


def can_be_sealed(
    artifact_status: ArtifactStatus, actor_class: ActorClass
) -> PredicateDecision:
    return _transition_predicate(
        "can_be_sealed",
        artifact_status,
        ArtifactStatus.SEALED,
        "artifact-sealed",
        actor_class,
    )


def can_be_unsealed(
    artifact_status: ArtifactStatus, actor_class: ActorClass
) -> PredicateDecision:
    return _transition_predicate(
        "can_be_unsealed",
        artifact_status,
        ArtifactStatus.ACTIVE,
        "artifact-unsealed",
        actor_class,
    )
