"""Slice 1D service — SourceLocator and Observation creation/retraction.

Validation is distinct from persistence (ADR-0020 Amendment 2): both paths
call the admissibility validators first; creation is nearly mechanical. On
PostgreSQL, creation and retraction go through the argus_private SECURITY
DEFINER functions (the app role cannot INSERT/UPDATE these tables at all);
the test-only SQLite path mirrors the semantics in Python.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..domain import admissibility as adm
from ..domain import audit
from ..domain.actors import Actor, ActorClass
from ..domain.audit import _is_postgres
from ..domain.exceptions import ConstitutionalViolation
from ..domain.models import (
    Case,
    CaseAuditHead,
    EvidenceArtifact,
    Observation,
    ObservationGrounding,
    SourceLocator,
)


def _raise_inadmissible(codes: tuple[str, ...], what: str) -> None:
    raise ConstitutionalViolation(
        codes[0].split(":")[0], f"{what} inadmissible: {', '.join(codes)}"
    )


def create_source_locator(
    session: Session,
    *,
    artifact: EvidenceArtifact,
    scheme: str,
    payload: dict,
    actor: Actor,
) -> SourceLocator:
    if actor.actor_class is not ActorClass.HUMAN:
        _raise_inadmissible((adm.ACTOR_NOT_PERMITTED,), "SourceLocator")
    codes = adm.validate_source_locator(
        artifact.status, scheme, payload, artifact.size_bytes
    )
    if codes:
        _raise_inadmissible(codes, "SourceLocator")

    locator_id = uuid.uuid4().hex
    if _is_postgres(session):
        import json

        session.execute(
            text(
                "SELECT argus_private.create_source_locator("
                ":id, :artifact_id, :scheme, CAST(:payload AS jsonb), "
                ":actor_class, :actor_id, :ai_ver)"
            ),
            {
                "id": locator_id,
                "artifact_id": artifact.id,
                "scheme": scheme,
                "payload": json.dumps(payload),
                "actor_class": actor.actor_class.value,
                "actor_id": actor.actor_id,
                "ai_ver": actor.ai_model_version,
            },
        )
        session.commit()
        return session.get(SourceLocator, locator_id)

    locator = SourceLocator(
        id=locator_id,
        case_id=artifact.case_id,
        artifact_id=artifact.id,
        scheme=scheme,
        payload=payload,
        created_by_class=actor.actor_class.value,
        created_by_id=actor.actor_id,
    )
    session.add(locator)
    session.flush()
    audit.emit(
        session,
        case_id=artifact.case_id,
        actor=actor,
        action="locator-created",
        target_type="SourceLocator",
        target_id=locator.id,
        detail={"artifact_id": artifact.id, "scheme": scheme},
    )
    session.commit()
    return locator


def _grounding_states(
    session: Session, case_id: str, locator_ids: list[str]
) -> tuple[adm.GroundingState, ...]:
    states = []
    for lid in locator_ids:
        locator = session.get(SourceLocator, lid)
        if locator is None:
            states.append(adm.GroundingState(exists=False))
            continue
        artifact = session.get(EvidenceArtifact, locator.artifact_id)
        states.append(
            adm.GroundingState(
                exists=True,
                retracted=locator.retracted_at is not None,
                same_case=locator.case_id == case_id,
                artifact_status=artifact.status if artifact else None,
            )
        )
    return tuple(states)


def create_observation(
    session: Session,
    *,
    case: Case,
    locator_ids: list[str],
    statement: str,
    method_description: str,
    actor: Actor,
    event_time_start=None,
    event_time_end=None,
) -> Observation:
    codes = adm.validate_observation(
        statement=statement,
        method_description=method_description,
        actor_class=actor.actor_class,
        case_status=case.status,
        groundings=_grounding_states(session, case.id, locator_ids),
    )
    if codes:
        _raise_inadmissible(codes, "Observation")

    obs_id = uuid.uuid4().hex
    if _is_postgres(session):
        session.execute(
            text(
                "SELECT argus_private.create_observation("
                ":id, :case_id, CAST(:locators AS text[]), :statement, :method, "
                ":actor_class, :actor_id, :ai_ver, :ev_start, :ev_end)"
            ),
            {
                "id": obs_id,
                "case_id": case.id,
                "locators": "{" + ",".join(locator_ids) + "}",
                "statement": statement,
                "method": method_description,
                "actor_class": actor.actor_class.value,
                "actor_id": actor.actor_id,
                "ai_ver": actor.ai_model_version,
                "ev_start": event_time_start,
                "ev_end": event_time_end,
            },
        )
        session.commit()
        return session.get(Observation, obs_id)

    # SQLite path: citation allocated under the head lock (serialization
    # mirror of the PostgreSQL function).
    session.get(CaseAuditHead, case.id, with_for_update=True)
    n = (
        session.execute(
            select(func.count()).select_from(Observation).where(
                Observation.case_id == case.id
            )
        ).scalar()
        or 0
    ) + 1
    observation = Observation(
        id=obs_id,
        case_id=case.id,
        citation=f"OBS-{n:06d}",
        statement=statement,
        method_description=method_description,
        event_time_start=event_time_start,
        event_time_end=event_time_end,
        created_by_class=actor.actor_class.value,
        created_by_id=actor.actor_id,
    )
    session.add(observation)
    session.flush()
    for lid in locator_ids:
        session.add(ObservationGrounding(observation_id=obs_id, locator_id=lid))
    audit.emit(
        session,
        case_id=case.id,
        actor=actor,
        action="claim-created",
        target_type="Observation",
        target_id=obs_id,
        detail={"citation": observation.citation, "locators": locator_ids},
    )
    session.commit()
    return observation


def _retract(
    session: Session, obj, actor: Actor, reason: str, *, pg_fn: str, action: str, target_type: str
):
    if actor.actor_class is not ActorClass.HUMAN:
        raise ConstitutionalViolation(
            "ONT-PRN-007", f"{target_type} retraction is human-only."
        )
    if not reason or not reason.strip():
        raise ConstitutionalViolation(
            "ONT-PRN-006", "Retraction requires a non-empty reason."
        )
    if _is_postgres(session):
        session.execute(
            text(
                f"SELECT argus_private.{pg_fn}(:id, :actor_class, :actor_id, :ai_ver, :reason)"
            ),
            {
                "id": obj.id,
                "actor_class": actor.actor_class.value,
                "actor_id": actor.actor_id,
                "ai_ver": actor.ai_model_version,
                "reason": reason,
            },
        )
        session.commit()
        session.expire(obj)
        return obj
    from datetime import datetime, timezone

    obj.retracted_at = datetime.now(timezone.utc)
    obj.retraction_reason = reason
    audit.emit(
        session,
        case_id=obj.case_id,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=obj.id,
        detail={"reason": reason},
    )
    session.commit()
    return obj


def retract_source_locator(session: Session, locator: SourceLocator, actor: Actor, *, reason: str):
    return _retract(
        session, locator, actor, reason,
        pg_fn="retract_source_locator", action="locator-retracted",
        target_type="SourceLocator",
    )


def retract_observation(session: Session, observation: Observation, actor: Actor, *, reason: str):
    return _retract(
        session, observation, actor, reason,
        pg_fn="retract_observation", action="claim-retracted",
        target_type="Observation",
    )


def observation_is_grounded(session: Session, observation: Observation) -> bool:
    """Derived, never stored (ADR-0020 §6). The Python rendering; PostgreSQL
    carries argus_private.is_observation_grounded for conformance."""
    lids = [
        row
        for row in session.execute(
            select(ObservationGrounding.locator_id).where(
                ObservationGrounding.observation_id == observation.id
            )
        ).scalars()
    ]
    return adm.is_grounded(_grounding_states(session, observation.case_id, lids))
