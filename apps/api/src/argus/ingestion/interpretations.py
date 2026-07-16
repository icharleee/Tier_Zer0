"""Slice 2A service — competing Interpretations.

Validation is distinct from persistence (ONT-PRN-017): both paths validate
via argus.domain.admissibility first; creation is mechanical. The system
preserves competing human meanings; it never converts coexistence into
comparison (Article IV) — no code here orders, ranks, promotes, or prefers.
"""

from __future__ import annotations

import hashlib
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
    GroundingRole,
    Interpretation,
    InterpretationGrounding,
    Observation,
    UncertaintyStatus,
)
from .observations import observation_is_grounded


def _observation_states(
    session: Session, case_id: str, groundings: list[tuple[str, str]]
) -> tuple[adm.ObservationGroundingState, ...]:
    states = []
    for obs_id, role in groundings:
        obs = session.get(Observation, obs_id)
        if obs is None:
            states.append(adm.ObservationGroundingState(exists=False, role=role))
            continue
        states.append(
            adm.ObservationGroundingState(
                exists=True,
                retracted=obs.retracted_at is not None,
                grounded=observation_is_grounded(session, obs),
                same_case=obs.case_id == case_id,
                role=role,
            )
        )
    return tuple(states)


def create_interpretation(
    session: Session,
    *,
    case: Case,
    groundings: list[tuple[str, str]],  # (observation_id, grounding_role)
    meaning_statement: str,
    reasoning_description: str,
    uncertainty_status: str,
    uncertainty_explanation: str,
    actor: Actor,
    unresolved_unknown_id: str | None = None,
) -> Interpretation:
    # Accumulated obligation (ONT-PRN-019 / Slice 2B): UNRESOLVED names the
    # specific evidentiary limit that produces it (Article IX).
    from ..domain.models import Unknown

    named: bool | None = None
    if unresolved_unknown_id is not None:
        unk = session.get(Unknown, unresolved_unknown_id)
        named = unk is not None and unk.case_id == case.id
    codes = adm.validate_interpretation(
        meaning_statement=meaning_statement,
        reasoning_description=reasoning_description,
        uncertainty_status=uncertainty_status,
        uncertainty_explanation=uncertainty_explanation,
        actor_class=actor.actor_class,
        groundings=_observation_states(session, case.id, groundings),
        unresolved_unknown_named=named,
    )
    if codes:
        raise ConstitutionalViolation(
            codes[0].split(":")[0], f"Interpretation inadmissible: {', '.join(codes)}"
        )

    int_id = uuid.uuid4().hex
    if _is_postgres(session):
        session.execute(
            text(
                "SELECT argus_private.create_interpretation("
                ":id, :case_id, CAST(:obs AS text[]), CAST(:roles AS text[]), "
                ":meaning, :reasoning, :unc_status, :unc_expl, "
                ":actor_class, :actor_id, :ai_ver, :unresolved_unknown)"
            ),
            {
                "id": int_id,
                "case_id": case.id,
                "obs": "{" + ",".join(o for o, _ in groundings) + "}",
                "roles": "{" + ",".join(r for _, r in groundings) + "}",
                "meaning": meaning_statement,
                "reasoning": reasoning_description,
                "unc_status": uncertainty_status,
                "unc_expl": uncertainty_explanation,
                "actor_class": actor.actor_class.value,
                "actor_id": actor.actor_id,
                "ai_ver": actor.ai_model_version,
                "unresolved_unknown": unresolved_unknown_id,
            },
        )
        session.commit()
        return session.get(Interpretation, int_id)

    # SQLite path: identical semantics, citation under the head lock.
    session.get(CaseAuditHead, case.id, with_for_update=True)
    n = (
        session.execute(
            select(func.count()).select_from(Interpretation).where(
                Interpretation.case_id == case.id
            )
        ).scalar()
        or 0
    ) + 1
    interpretation = Interpretation(
        id=int_id,
        case_id=case.id,
        citation=f"INT-{n:06d}",
        meaning_statement=meaning_statement,
        reasoning_description=reasoning_description,
        uncertainty_status=UncertaintyStatus(uncertainty_status),
        uncertainty_explanation=uncertainty_explanation,
        created_by_class=actor.actor_class.value,
        created_by_id=actor.actor_id,
    )
    session.add(interpretation)
    session.flush()
    for obs_id, role in groundings:
        obs = session.get(Observation, obs_id)
        session.add(
            InterpretationGrounding(
                interpretation_id=int_id,
                observation_id=obs_id,
                statement_fingerprint=hashlib.sha256(
                    obs.statement.encode("utf-8")
                ).hexdigest(),
                grounding_role=GroundingRole(role),
            )
        )
    if unresolved_unknown_id is not None:
        from ..domain.models import UnknownLink

        session.add(UnknownLink(
            unknown_id=unresolved_unknown_id, target_type="Interpretation",
            target_id=int_id,
            nature="Named evidentiary limit for UNRESOLVED uncertainty (Article IX)",
        ))
    audit.emit(
        session,
        case_id=case.id,
        actor=actor,
        action="claim-created",
        target_type="Interpretation",
        target_id=int_id,
        detail={
            "citation": interpretation.citation,
            "observations": [o for o, _ in groundings],
            "uncertainty_status": uncertainty_status,
        },
    )
    session.commit()
    return interpretation


def retract_interpretation(
    session: Session, interpretation: Interpretation, actor: Actor, *, reason: str
) -> Interpretation:
    if actor.actor_class is not ActorClass.HUMAN:
        raise ConstitutionalViolation("ONT-PRN-007", "Interpretation retraction is human-only.")
    if not reason or not reason.strip():
        raise ConstitutionalViolation("ONT-PRN-006", "Retraction requires a non-empty reason.")
    if _is_postgres(session):
        session.execute(
            text(
                "SELECT argus_private.retract_interpretation(:id, :actor_class, :actor_id, :ai_ver, :reason)"
            ),
            {
                "id": interpretation.id,
                "actor_class": actor.actor_class.value,
                "actor_id": actor.actor_id,
                "ai_ver": actor.ai_model_version,
                "reason": reason,
            },
        )
        session.commit()
        session.expire(interpretation)
        return interpretation
    from datetime import datetime, timezone

    interpretation.retracted_at = datetime.now(timezone.utc)
    interpretation.retraction_reason = reason
    audit.emit(
        session,
        case_id=interpretation.case_id,
        actor=actor,
        action="claim-retracted",
        target_type="Interpretation",
        target_id=interpretation.id,
        detail={"reason": reason},
    )
    session.commit()
    return interpretation


def grounding_health(session: Session, interpretation: Interpretation) -> str:
    """Derived, never stored. The Python rendering; PostgreSQL carries
    argus_private.interpretation_grounding_health for conformance."""
    rows = session.execute(
        select(InterpretationGrounding).where(
            InterpretationGrounding.interpretation_id == interpretation.id
        )
    ).scalars()
    states = _observation_states(
        session,
        interpretation.case_id,
        [(g.observation_id, g.grounding_role.value) for g in rows],
    )
    return adm.interpretation_grounding_health(states)
