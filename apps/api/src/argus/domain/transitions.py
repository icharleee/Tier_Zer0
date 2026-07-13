"""Explicit constitutional transitions (ONT-PRN-012, Founder Resolution 007).

Every lifecycle movement is a named operation that records the responsible
actor and timestamp, validates the allowed predecessor state, and emits the
audit event in the same transaction. There are no bare status writes, no
invisible state changes, no automatic promotion.

The ALLOWED_ARTIFACT_TRANSITIONS registry is the executable rendering of the
allowed-predecessor tables in docs/domain/ENTITY_LIFECYCLES.md §2 — the
document is authoritative; this dict derives from it (ONT-PRN-008).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import audit
from .actors import Actor, ActorClass
from .exceptions import ConstitutionalViolation
from .models import ArtifactStatus, EvidenceArtifact

_A = ArtifactStatus

# (from, to) -> (audit action, actor classes permitted)
ALLOWED_ARTIFACT_TRANSITIONS: dict[
    tuple[ArtifactStatus, ArtifactStatus], tuple[str, frozenset[ActorClass]]
] = {
    (_A.PENDING_VERIFICATION, _A.ACTIVE): (
        "artifact-activated",
        frozenset({ActorClass.SYSTEM}),
    ),
    (_A.PENDING_VERIFICATION, _A.QUARANTINED): (
        "artifact-quarantined",
        frozenset({ActorClass.SYSTEM}),
    ),
    (_A.ACTIVE, _A.QUARANTINED): (
        "artifact-quarantined",
        frozenset({ActorClass.SYSTEM}),
    ),
    (_A.QUARANTINED, _A.RETRACTED): (
        "artifact-retracted",
        frozenset({ActorClass.HUMAN}),
    ),
    (_A.QUARANTINED, _A.ACTIVE): (
        "artifact-reactivated",
        frozenset({ActorClass.HUMAN}),
    ),
    (_A.ACTIVE, _A.RETRACTED): ("artifact-retracted", frozenset({ActorClass.HUMAN})),
    (_A.ACTIVE, _A.SEALED): ("artifact-sealed", frozenset({ActorClass.HUMAN})),
    (_A.SEALED, _A.ACTIVE): ("artifact-unsealed", frozenset({ActorClass.HUMAN})),
}


def _transition(
    session: Session,
    artifact: EvidenceArtifact,
    to_status: ArtifactStatus,
    actor: Actor,
    detail: dict | None = None,
) -> EvidenceArtifact:
    key = (artifact.status, to_status)
    if key not in ALLOWED_ARTIFACT_TRANSITIONS:
        raise ConstitutionalViolation(
            "ONT-PRN-012",
            f"No explicit transition {artifact.status.value} -> {to_status.value} "
            "exists in the allowed-predecessor registry (Entity Lifecycles §2).",
        )
    action, allowed_actors = ALLOWED_ARTIFACT_TRANSITIONS[key]
    if actor.actor_class not in allowed_actors:
        raise ConstitutionalViolation(
            "ONT-PRN-007",
            f"Actor class {actor.actor_class.value} may not perform "
            f"{action} (human judgment is final; permitted: "
            f"{sorted(a.value for a in allowed_actors)}).",
        )
    artifact.status = to_status
    audit.emit(
        session,
        case_id=artifact.case_id,
        actor=actor,
        action=action,
        target_type="EvidenceArtifact",
        target_id=artifact.id,
        detail=detail,
    )
    return artifact


def activate_artifact(
    session: Session,
    artifact: EvidenceArtifact,
    actor: Actor,
    *,
    verified_digest: str,
) -> EvidenceArtifact:
    """PENDING_VERIFICATION -> ACTIVE. SystemProcess only, and only with the
    digest the verifier actually recomputed (ADR-0007 §6: no activation
    without passed integrity verification)."""
    if verified_digest != artifact.hash_digest:
        raise ConstitutionalViolation(
            "ONT-EVA-001",
            "Activation requires the verifier's recomputed digest to match the "
            "recorded original hash.",
        )
    return _transition(session, artifact, _A.ACTIVE, actor)


def quarantine_artifact(
    session: Session, artifact: EvidenceArtifact, actor: Actor, *, reason: str
) -> EvidenceArtifact:
    return _transition(session, artifact, _A.QUARANTINED, actor, {"reason": reason})


def reactivate_artifact(
    session: Session,
    artifact: EvidenceArtifact,
    actor: Actor,
    *,
    reverified_digest: str,
    rationale: str,
) -> EvidenceArtifact:
    """QUARANTINED -> ACTIVE. Human-only disposition (ONT-PRN-007), and only
    after verified recovery."""
    if reverified_digest != artifact.hash_digest:
        raise ConstitutionalViolation(
            "ONT-EVA-001",
            "Reactivation requires re-verification against the original hash.",
        )
    return _transition(
        session, artifact, _A.ACTIVE, actor, {"rationale": rationale}
    )


def retract_artifact(
    session: Session,
    artifact: EvidenceArtifact,
    actor: Actor,
    *,
    reason: str,
    superseded_by: str | None = None,
) -> EvidenceArtifact:
    """-> RETRACTED. Human-only; a reason is mandatory; nothing disappears —
    the record stays permanently readable (ONT-PRN-006)."""
    if not reason or not reason.strip():
        raise ConstitutionalViolation(
            "ONT-PRN-006", "Retraction requires a non-empty reason."
        )
    artifact.retracted_at = datetime.now(timezone.utc)
    artifact.retraction_reason = reason
    artifact.superseded_by = superseded_by
    return _transition(
        session,
        artifact,
        _A.RETRACTED,
        actor,
        {"reason": reason, "superseded_by": superseded_by},
    )


def seal_artifact(
    session: Session, artifact: EvidenceArtifact, actor: Actor, *, legal_basis: str
) -> EvidenceArtifact:
    return _transition(session, artifact, _A.SEALED, actor, {"legal_basis": legal_basis})


def unseal_artifact(
    session: Session, artifact: EvidenceArtifact, actor: Actor, *, legal_basis: str
) -> EvidenceArtifact:
    return _transition(session, artifact, _A.ACTIVE, actor, {"legal_basis": legal_basis})
