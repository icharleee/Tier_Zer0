"""Slice 2C service — Contradictions as boundary objects (ADR-0027).

A Contradiction may state that claims cannot all fit the same reality.
It may never decide which claim reality favors. Nothing here orders,
adjudicates, promotes, or retracts any member — ever.
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
    Contradiction,
    ContradictionDisposition,
    ContradictionMember,
    ContradictionType,
    DispositionOutcome,
    Interpretation,
    Observation,
    UnknownOperationalState,
)

_MEMBER_MODELS = {"Observation": Observation, "Interpretation": Interpretation}


def _raise(codes: tuple[str, ...], what: str) -> None:
    raise ConstitutionalViolation(
        codes[0].split(":")[0], f"{what} inadmissible: {', '.join(codes)}"
    )


def _member_states(session, case_id, members):
    states = []
    for mtype, mid in members:
        model = _MEMBER_MODELS.get(mtype)
        rec = session.get(model, mid) if model else None
        if rec is None:
            states.append(adm.MemberState(exists=False))
            continue
        states.append(adm.MemberState(
            exists=True, retracted=rec.retracted_at is not None,
            same_case=rec.case_id == case_id,
        ))
    return tuple(states)


def _fingerprint(session, mtype, mid) -> str:
    rec = session.get(_MEMBER_MODELS[mtype], mid)
    payload = rec.statement if mtype == "Observation" else rec.meaning_statement
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_contradiction(
    session: Session, *, case: Case, members: list[tuple[str, str]],
    description: str, contradiction_type: str, scope_definition: str,
    incompatibility_basis: str, actor: Actor,
) -> Contradiction:
    codes = adm.validate_contradiction(
        description=description, contradiction_type=contradiction_type,
        scope_definition=scope_definition, incompatibility_basis=incompatibility_basis,
        actor_class=actor.actor_class,
        members=_member_states(session, case.id, members),
        distinct_member_count=len(set(members)),
    )
    if codes:
        _raise(codes, "Contradiction")

    con_id = uuid.uuid4().hex
    if _is_postgres(session):
        session.execute(
            text(
                "SELECT argus_private.create_contradiction("
                ":id, :case_id, CAST(:mtypes AS text[]), CAST(:mids AS text[]), "
                "CAST(:roles AS text[]), :descr, :ctype, :scope, :basis, "
                ":ac, :aid, :ver)"
            ),
            {
                "id": con_id, "case_id": case.id,
                "mtypes": "{" + ",".join(t for t, _ in members) + "}",
                "mids": "{" + ",".join(i for _, i in members) + "}",
                "roles": "{" + ",".join("INCOMPATIBLE_CLAIM" for _ in members) + "}",
                "descr": description, "ctype": contradiction_type,
                "scope": scope_definition, "basis": incompatibility_basis,
                "ac": actor.actor_class.value, "aid": actor.actor_id,
                "ver": actor.ai_model_version,
            },
        )
        session.commit()
        return session.get(Contradiction, con_id)

    session.get(CaseAuditHead, case.id, with_for_update=True)
    n = (session.execute(select(func.count()).select_from(Contradiction).where(
        Contradiction.case_id == case.id)).scalar() or 0) + 1
    contradiction = Contradiction(
        id=con_id, case_id=case.id, citation=f"CON-{n:06d}",
        description=description,
        contradiction_type=ContradictionType(contradiction_type),
        scope_definition=scope_definition,
        incompatibility_basis=incompatibility_basis,
        created_by_class=actor.actor_class.value, created_by_id=actor.actor_id,
    )
    session.add(contradiction)
    session.flush()
    for mtype, mid in members:
        session.add(ContradictionMember(
            contradiction_id=con_id, member_type=mtype, member_id=mid,
            member_fingerprint=_fingerprint(session, mtype, mid),
        ))
    audit.emit(session, case_id=case.id, actor=actor, action="contradiction-created",
               target_type="Contradiction", target_id=con_id,
               detail={"citation": contradiction.citation,
                       "type": contradiction_type,
                       "members": [m for _, m in members]})
    session.commit()
    return contradiction


def set_contradiction_review(session, contradiction, actor, *, under_review: bool):
    if actor.actor_class is not ActorClass.HUMAN:
        raise ConstitutionalViolation("ONT-PRN-007", "Review marking is human-only.")
    if _is_postgres(session):
        session.execute(
            text("SELECT argus_private.set_contradiction_review(:id, :ur, :ac, :aid, :ver)"),
            {"id": contradiction.id, "ur": under_review,
             "ac": actor.actor_class.value, "aid": actor.actor_id,
             "ver": actor.ai_model_version},
        )
        session.commit()
        session.expire(contradiction)
        return contradiction
    if session.execute(select(ContradictionDisposition).where(
            ContradictionDisposition.contradiction_id == contradiction.id)).scalars().first():
        raise ConstitutionalViolation("ONT-PRN-012", "Disposition is terminal.")
    target = (UnknownOperationalState.UNDER_REVIEW if under_review
              else UnknownOperationalState.OPEN)
    if contradiction.operational_state is target:
        raise ConstitutionalViolation("ONT-PRN-012", f"No such transition (already {target.value}).")
    contradiction.operational_state = target
    audit.emit(session, case_id=contradiction.case_id, actor=actor,
               action="contradiction-review-started" if under_review else "contradiction-review-paused",
               target_type="Contradiction", target_id=contradiction.id)
    session.commit()
    return contradiction


def dispose_contradiction(
    session, *, contradiction, outcome: str, rationale: str,
    informing_refs: list[str] | None, actor: Actor,
) -> ContradictionDisposition:
    codes = adm.validate_contradiction_disposition(outcome, rationale, actor.actor_class)
    if codes:
        _raise(codes, "ContradictionDisposition")
    disp_id = uuid.uuid4().hex
    if _is_postgres(session):
        arr = "{" + ",".join(informing_refs or []) + "}" if informing_refs else None
        session.execute(
            text("SELECT argus_private.dispose_contradiction(:id, :con, :o, :r, CAST(:inf AS text[]), :ac, :aid, :ver)"),
            {"id": disp_id, "con": contradiction.id, "o": outcome, "r": rationale,
             "inf": arr, "ac": actor.actor_class.value, "aid": actor.actor_id,
             "ver": actor.ai_model_version},
        )
        session.commit()
        return session.get(ContradictionDisposition, disp_id)
    if session.execute(select(ContradictionDisposition).where(
            ContradictionDisposition.contradiction_id == contradiction.id)).scalars().first():
        raise ConstitutionalViolation("ONT-PRN-012", "Disposition is terminal; already disposed.")
    disposition = ContradictionDisposition(
        id=disp_id, contradiction_id=contradiction.id,
        outcome=DispositionOutcome(outcome), rationale=rationale,
        informing_refs=informing_refs, disposed_by=actor.actor_id,
    )
    session.add(disposition)
    session.flush()
    audit.emit(session, case_id=contradiction.case_id, actor=actor,
               action="contradiction-disposed",
               target_type="ContradictionDisposition", target_id=disp_id,
               detail={"contradiction_id": contradiction.id, "outcome": outcome})
    session.commit()
    return disposition


def link_contradiction(
    session, *, contradiction, hypothesis_id: str, explanation: str, actor: Actor,
) -> "ContradictionLink":
    """Boundary-owned validity link (Session 012): the Contradiction
    CHALLENGES a Hypothesis — the only authorized relationship; it never
    refutes, disproves, defeats, weakens, or invalidates. Alters neither
    endpoint; a disposed Contradiction remains historically linked."""
    from ..domain import fingerprints
    from ..domain.models import ContradictionLink, Hypothesis

    hyp = session.get(Hypothesis, hypothesis_id)
    duplicate = session.execute(select(ContradictionLink).where(
        ContradictionLink.contradiction_id == contradiction.id,
        ContradictionLink.hypothesis_id == hypothesis_id,
    )).scalars().first() is not None
    codes = adm.validate_contradiction_link(
        both_exist=hyp is not None,
        same_case=hyp is not None and hyp.case_id == contradiction.case_id,
        duplicate=duplicate,
        relationship_type=adm.CHALLENGED_BY_CONTRADICTION,
        explanation=explanation,
        actor_class=actor.actor_class,
    )
    if codes:
        _raise(codes, "ContradictionLink")
    if _is_postgres(session):
        link_id = uuid.uuid4().hex
        session.execute(
            text("SELECT argus_private.link_contradiction(:id, :con, :hyp, :expl, :ac, :aid, :ver)"),
            {"id": link_id, "con": contradiction.id, "hyp": hypothesis_id,
             "expl": explanation, "ac": actor.actor_class.value,
             "aid": actor.actor_id, "ver": actor.ai_model_version},
        )
        session.commit()
        return session.get(ContradictionLink, link_id)
    session.get(CaseAuditHead, contradiction.case_id, with_for_update=True)
    link = ContradictionLink(
        contradiction_id=contradiction.id, hypothesis_id=hypothesis_id,
        hypothesis_fingerprint=fingerprints.hypothesis_fingerprint_v1(
            hyp.explanatory_statement, hyp.reasoning_description,
            hyp.uncertainty_status.value, hyp.uncertainty_explanation,
            hyp.testability_statement, hyp.challenge_condition,
        ),
        explanation=explanation,
        linked_by_class=actor.actor_class.value, linked_by_id=actor.actor_id,
    )
    session.add(link)
    session.flush()
    audit.emit(session, case_id=contradiction.case_id, actor=actor,
               action="contradiction-linked",
               target_type="ContradictionLink", target_id=link.id,
               detail={"contradiction_id": contradiction.id,
                       "hypothesis_id": hypothesis_id,
                       "relationship_type": adm.CHALLENGED_BY_CONTRADICTION})
    session.commit()
    return link


def contradiction_health(session, contradiction) -> str:
    """Derived, never stored. Python rendering; PostgreSQL carries
    argus_private.contradiction_health for conformance."""
    members = session.execute(select(ContradictionMember).where(
        ContradictionMember.contradiction_id == contradiction.id)).scalars().all()
    return adm.contradiction_health(_member_states(
        session, contradiction.case_id,
        [(m.member_type, m.member_id) for m in members]))


def contradiction_status(session, contradiction) -> str:
    """Derived: disposition outcome if disposed, else operational state."""
    disp = session.execute(select(ContradictionDisposition).where(
        ContradictionDisposition.contradiction_id == contradiction.id)).scalars().first()
    return disp.outcome.value if disp else contradiction.operational_state.value
