"""Slice 2B service — Unknowns and evidentiary limits (ADR-0024/0025).

NULL is not Unknown; missing rows are not Unknown. These functions create
deliberate epistemic objects that bound reasoning without concluding
anything. Resolving an Unknown alters no linked record: knowledge changes,
the system does not, humans decide what to do next (ONT-PRN-020 / H5).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

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
    Hypothesis,
    Interpretation,
    Observation,
    ResolutionType,
    Unknown,
    UnknownLink,
    UnknownOperationalState,
    UnknownResolution,
)

_TARGETS = {
    "Observation": Observation,
    "Interpretation": Interpretation,
    "EvidenceArtifact": EvidenceArtifact,
    # Slice 2D (Session 012): Unknown bounds Hypothesis (LIMITED_BY_UNKNOWN).
    "Hypothesis": Hypothesis,
}


def _raise(codes: tuple[str, ...], what: str) -> None:
    raise ConstitutionalViolation(
        codes[0].split(":")[0], f"{what} inadmissible: {', '.join(codes)}"
    )


def create_unknown(
    session: Session,
    *,
    case: Case,
    question: str,
    actor: Actor,
    impact_statement: str | None = None,
) -> Unknown:
    codes = adm.validate_unknown(question, actor.actor_class)
    if codes:
        _raise(codes, "Unknown")
    unk_id = uuid.uuid4().hex
    if _is_postgres(session):
        session.execute(
            text(
                "SELECT argus_private.create_unknown(:id, :case_id, :q, :impact, :ac, :aid, :ver)"
            ),
            {"id": unk_id, "case_id": case.id, "q": question, "impact": impact_statement,
             "ac": actor.actor_class.value, "aid": actor.actor_id, "ver": actor.ai_model_version},
        )
        session.commit()
        return session.get(Unknown, unk_id)
    session.get(CaseAuditHead, case.id, with_for_update=True)
    n = (session.execute(select(func.count()).select_from(Unknown).where(
        Unknown.case_id == case.id)).scalar() or 0) + 1
    unknown = Unknown(
        id=unk_id, case_id=case.id, citation=f"UNK-{n:06d}", question=question,
        impact_statement=impact_statement,
        created_by_class=actor.actor_class.value, created_by_id=actor.actor_id,
    )
    session.add(unknown)
    session.flush()
    audit.emit(session, case_id=case.id, actor=actor, action="unknown-created",
               target_type="Unknown", target_id=unk_id,
               detail={"citation": unknown.citation})
    session.commit()
    return unknown


def link_unknown(
    session: Session, *, unknown: Unknown, target_type: str, target_id: str,
    nature: str, actor: Actor,
) -> UnknownLink:
    if actor.actor_class is not ActorClass.HUMAN:
        _raise((adm.UNK_UNSUPPORTED_ACTOR,), "UnknownLink")
    model = _TARGETS.get(target_type)
    target = session.get(model, target_id) if model else None
    if target is None:
        _raise((adm.UNKNOWN_TARGET,), "UnknownLink")
    if target.case_id != unknown.case_id:
        _raise((adm.CROSS_CASE_LINK,), "UnknownLink")
    link_id = uuid.uuid4().hex
    if _is_postgres(session):
        session.execute(
            text("SELECT argus_private.link_unknown(:id, :unk, :tt, :tid, :nature, :ac, :aid, :ver)"),
            {"id": link_id, "unk": unknown.id, "tt": target_type, "tid": target_id,
             "nature": nature, "ac": actor.actor_class.value, "aid": actor.actor_id,
             "ver": actor.ai_model_version},
        )
        session.commit()
        return session.get(UnknownLink, link_id)
    link = UnknownLink(id=link_id, unknown_id=unknown.id, target_type=target_type,
                       target_id=target_id, nature=nature)
    session.add(link)
    session.flush()
    audit.emit(session, case_id=unknown.case_id, actor=actor, action="unknown-linked",
               target_type="UnknownLink", target_id=link_id,
               detail={"unknown_id": unknown.id, "target_type": target_type,
                       "target_id": target_id})
    session.commit()
    return link


def set_under_review(session: Session, unknown: Unknown, actor: Actor, *, under_review: bool) -> Unknown:
    if actor.actor_class is not ActorClass.HUMAN:
        raise ConstitutionalViolation("ONT-PRN-007", "Review marking is human-only.")
    if _is_postgres(session):
        session.execute(
            text("SELECT argus_private.set_unknown_review(:id, :ur, :ac, :aid, :ver)"),
            {"id": unknown.id, "ur": under_review, "ac": actor.actor_class.value,
             "aid": actor.actor_id, "ver": actor.ai_model_version},
        )
        session.commit()
        session.expire(unknown)
        return unknown
    if session.get(UnknownResolution, unknown.id) or session.execute(
        select(UnknownResolution).where(UnknownResolution.unknown_id == unknown.id)
    ).scalars().first():
        raise ConstitutionalViolation("ONT-PRN-012", "Disposition is terminal.")
    target = (UnknownOperationalState.UNDER_REVIEW if under_review
              else UnknownOperationalState.OPEN)
    if unknown.operational_state is target:
        raise ConstitutionalViolation("ONT-PRN-012", f"No such transition (already {target.value}).")
    unknown.operational_state = target
    audit.emit(session, case_id=unknown.case_id, actor=actor,
               action="unknown-review-started" if under_review else "unknown-review-paused",
               target_type="Unknown", target_id=unknown.id)
    session.commit()
    return unknown


def resolve_unknown(
    session: Session, *, unknown: Unknown, resolution_type: str, rationale: str,
    answering_claims: list[str] | None, actor: Actor,
) -> UnknownResolution:
    codes = adm.validate_unknown_resolution(
        resolution_type, rationale, tuple(answering_claims or ()), actor.actor_class
    )
    if codes:
        _raise(codes, "UnknownResolution")
    res_id = uuid.uuid4().hex
    if _is_postgres(session):
        arr = "{" + ",".join(answering_claims or []) + "}" if answering_claims else None
        session.execute(
            text("SELECT argus_private.resolve_unknown(:id, :unk, :t, :r, CAST(:claims AS text[]), :ac, :aid, :ver)"),
            {"id": res_id, "unk": unknown.id, "t": resolution_type, "r": rationale,
             "claims": arr, "ac": actor.actor_class.value, "aid": actor.actor_id,
             "ver": actor.ai_model_version},
        )
        session.commit()
        return session.get(UnknownResolution, res_id)
    if session.execute(select(UnknownResolution).where(
            UnknownResolution.unknown_id == unknown.id)).scalars().first():
        raise ConstitutionalViolation("ONT-PRN-012", "Disposition is terminal; already resolved.")
    for cid in answering_claims or []:
        if session.get(Observation, cid) is None and session.get(Interpretation, cid) is None:
            _raise((adm.ANSWER_REQUIRES_EVIDENCE,), "UnknownResolution")
    resolution = UnknownResolution(
        id=res_id, unknown_id=unknown.id,
        resolution_type=ResolutionType(resolution_type), rationale=rationale,
        answering_claims=answering_claims, resolved_by=actor.actor_id,
    )
    session.add(resolution)
    session.flush()
    action = {
        "ANSWERED": "unknown-resolved",
        "PARTIALLY_ANSWERED": "unknown-partially-resolved",
        "WITHDRAWN": "unknown-withdrawn",
        "UNRESOLVABLE": "unknown-marked-unresolvable",
    }[resolution_type]
    audit.emit(session, case_id=unknown.case_id, actor=actor, action=action,
               target_type="UnknownResolution", target_id=res_id,
               detail={"unknown_id": unknown.id, "type": resolution_type})
    session.commit()
    return resolution


def unknown_status(session: Session, unknown: Unknown) -> str:
    """Derived, never stored: resolution type if disposed, else the
    operational state."""
    res = session.execute(select(UnknownResolution).where(
        UnknownResolution.unknown_id == unknown.id)).scalars().first()
    if res is not None:
        return res.resolution_type.value
    return unknown.operational_state.value
