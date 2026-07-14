"""Explicit constitutional transitions (ONT-PRN-012, Founder Resolution 007).

Every lifecycle movement is a named operation that records the responsible
actor and timestamp, validates the allowed predecessor state, and emits the
audit event in the same transaction. There are no bare status writes, no
invisible state changes, no automatic promotion.

Two renderings of Entity Lifecycles §2 exist by design (ONT-PRN-008: the
document is authoritative; both derive from it):

- ALLOWED_ARTIFACT_TRANSITIONS below — the Python orchestration registry,
  validated BEFORE any database call so service semantics are identical on
  every backend;
- the SECURITY DEFINER functions in argus_private (migration 003) — the
  PostgreSQL enforcement rendering, which re-validates independently so that
  bypassing Python cannot corrupt constitutional state (Slice 1B).

A PostgreSQL-gated conformance test asserts the two renderings accept and
reject the same transition set.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from . import audit
from .actors import Actor, ActorClass
from .audit import _is_postgres
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


def _validate(
    artifact: EvidenceArtifact, to_status: ArtifactStatus, actor: Actor
) -> str:
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
    return action


def _perform(
    session: Session,
    artifact: EvidenceArtifact,
    to_status: ArtifactStatus,
    actor: Actor,
    *,
    pg_function: str,
    pg_params: dict,
    detail: dict | None = None,
) -> EvidenceArtifact:
    action = _validate(artifact, to_status, actor)

    if _is_postgres(session):
        # PostgreSQL enforcement path: the SECURITY DEFINER function holds the
        # global lock order (head, then artifact row), re-validates, mutates,
        # and appends the event — atomically, or neither.
        params = {
            "artifact_id": artifact.id,
            "actor_class": actor.actor_class.value,
            "actor_id": actor.actor_id,
            "ai_model_version": actor.ai_model_version,
            **pg_params,
        }
        placeholders = ", ".join(f":{k}" for k in params)
        session.execute(
            text(f"SELECT argus_private.{pg_function}({placeholders})"), params
        )
        session.expire(artifact)
        return artifact

    # Application path (test-only SQLite backend): same semantics in Python.
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
    digest the verifier actually recomputed (ADR-0007 §6)."""
    if verified_digest != artifact.hash_digest:
        raise ConstitutionalViolation(
            "ONT-EVA-001",
            "Activation requires the verifier's recomputed digest to match the "
            "recorded original hash.",
        )
    return _perform(
        session,
        artifact,
        _A.ACTIVE,
        actor,
        pg_function="activate_evidence_artifact",
        pg_params={"verified_digest": verified_digest},
        detail=None,
    )


def quarantine_artifact(
    session: Session, artifact: EvidenceArtifact, actor: Actor, *, reason: str
) -> EvidenceArtifact:
    return _perform(
        session,
        artifact,
        _A.QUARANTINED,
        actor,
        pg_function="quarantine_evidence_artifact",
        pg_params={"reason": reason},
        detail={"reason": reason},
    )


def reactivate_artifact(
    session: Session,
    artifact: EvidenceArtifact,
    actor: Actor,
    *,
    reverified_digest: str,
    rationale: str,
) -> EvidenceArtifact:
    """QUARANTINED -> ACTIVE. Human-only disposition (ONT-PRN-007), only after
    verified recovery."""
    if reverified_digest != artifact.hash_digest:
        raise ConstitutionalViolation(
            "ONT-EVA-001",
            "Reactivation requires re-verification against the original hash.",
        )
    return _perform(
        session,
        artifact,
        _A.ACTIVE,
        actor,
        pg_function="reactivate_evidence_artifact",
        pg_params={"reverified_digest": reverified_digest, "rationale": rationale},
        detail={"rationale": rationale},
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
    if not _is_postgres(session):
        artifact.retracted_at = datetime.now(timezone.utc)
        artifact.retraction_reason = reason
        artifact.superseded_by = superseded_by
    return _perform(
        session,
        artifact,
        _A.RETRACTED,
        actor,
        pg_function="retract_evidence_artifact",
        pg_params={"reason": reason, "superseded_by": superseded_by},
        detail={"reason": reason, "superseded_by": superseded_by},
    )


def seal_artifact(
    session: Session, artifact: EvidenceArtifact, actor: Actor, *, legal_basis: str
) -> EvidenceArtifact:
    return _perform(
        session,
        artifact,
        _A.SEALED,
        actor,
        pg_function="seal_evidence_artifact",
        pg_params={"legal_basis": legal_basis},
        detail={"legal_basis": legal_basis},
    )


def unseal_artifact(
    session: Session, artifact: EvidenceArtifact, actor: Actor, *, legal_basis: str
) -> EvidenceArtifact:
    return _perform(
        session,
        artifact,
        _A.ACTIVE,
        actor,
        pg_function="unseal_evidence_artifact",
        pg_params={"legal_basis": legal_basis},
        detail={"legal_basis": legal_basis},
    )
