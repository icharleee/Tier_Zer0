"""Slice 2D service — Hypotheses as provisional explanatory structures
(ADR-0028, ONT-PRN-023).

A Hypothesis is admissible for examination — never likely, preferred,
correct, or accepted. Nothing here promotes, ranks, confirms, refutes, or
auto-closes any explanation; boundary events and sibling retraction alter
no stored Hypothesis field. ARGUS may preserve explanations for
examination; it may never convert explanation into verdict.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..domain import admissibility as adm
from ..domain import audit, fingerprints
from ..domain.actors import Actor, ActorClass
from ..domain.audit import _is_postgres
from ..domain.exceptions import ConstitutionalViolation
from ..domain.models import (
    AlternativeArticulation,
    Case,
    CaseAuditHead,
    Contradiction,
    ContradictionDisposition,
    ContradictionLink,
    Hypothesis,
    HypothesisAlternative,
    HypothesisGrounding,
    HypothesisGroundingRole,
    Interpretation,
    UncertaintyStatus,
    Unknown,
    UnknownLink,
    UnknownResolution,
)
from .interpretations import grounding_health as interpretation_grounding_health


def _raise(codes: tuple[str, ...], what: str) -> None:
    raise ConstitutionalViolation(
        codes[0].split(":")[0], f"{what} inadmissible: {', '.join(codes)}"
    )


def _interpretation_states(
    session: Session, case_id: str, groundings: list[tuple[str, str]]
) -> tuple[adm.InterpretationGroundingState, ...]:
    states = []
    for int_id, role in groundings:
        interp = session.get(Interpretation, int_id)
        if interp is None:
            states.append(adm.InterpretationGroundingState(exists=False, role=role))
            continue
        states.append(
            adm.InterpretationGroundingState(
                exists=True,
                retracted=interp.retracted_at is not None,
                grounded=interpretation_grounding_health(session, interp) == "GROUNDED",
                same_case=interp.case_id == case_id,
                role=role,
            )
        )
    return tuple(states)


def _validate_boundary_targets(
    session: Session,
    case_id: str,
    limiting_unknowns: list[tuple[str, str]],
    challenging_contradictions: list[tuple[str, str]],
) -> None:
    for unk_id, _nature in limiting_unknowns:
        unk = session.get(Unknown, unk_id)
        if unk is None:
            _raise((adm.UNKNOWN_TARGET,), "Hypothesis unknown articulation")
        if unk.case_id != case_id:
            _raise((adm.CROSS_CASE_LINK,), "Hypothesis unknown articulation")
    for con_id, explanation in challenging_contradictions:
        con = session.get(Contradiction, con_id)
        codes = adm.validate_contradiction_link(
            both_exist=con is not None,
            same_case=con is not None and con.case_id == case_id,
            duplicate=False,
            relationship_type=adm.CHALLENGED_BY_CONTRADICTION,
            explanation=explanation,
            actor_class=ActorClass.HUMAN,
        )
        if codes:
            _raise(codes, "Hypothesis contradiction articulation")


def create_hypothesis(
    session: Session,
    *,
    case: Case,
    groundings: list[tuple[str, str]],  # (interpretation_id, grounding_role)
    explanatory_statement: str,
    reasoning_description: str,
    uncertainty_status: str,
    uncertainty_explanation: str,
    testability_statement: str,
    challenge_condition: str,
    actor: Actor,
    alternatives: list[tuple[str, str]] | None = None,  # (hypothesis_id, relation_explanation)
    alternative_absence_explanation: str | None = None,
    limiting_unknowns: list[tuple[str, str]] | None = None,  # (unknown_id, nature)
    no_current_unknowns_explanation: str | None = None,
    challenging_contradictions: list[tuple[str, str]] | None = None,  # (contradiction_id, explanation)
    no_current_contradictions_explanation: str | None = None,
) -> Hypothesis:
    alternatives = alternatives or []
    limiting_unknowns = limiting_unknowns or []
    challenging_contradictions = challenging_contradictions or []

    codes = adm.validate_hypothesis(
        explanatory_statement=explanatory_statement,
        reasoning_description=reasoning_description,
        uncertainty_status=uncertainty_status,
        uncertainty_explanation=uncertainty_explanation,
        testability_statement=testability_statement,
        challenge_condition=challenge_condition,
        actor_class=actor.actor_class,
        groundings=_interpretation_states(session, case.id, groundings),
        distinct_grounding_count=len({i for i, _ in groundings}),
        alternative_link_count=len(alternatives),
        alternative_absence_explanation=alternative_absence_explanation,
        unknown_link_count=len(limiting_unknowns),
        no_current_unknowns_explanation=no_current_unknowns_explanation,
        contradiction_link_count=len(challenging_contradictions),
        no_current_contradictions_explanation=no_current_contradictions_explanation,
    )
    if codes:
        _raise(codes, "Hypothesis")

    hyp_id = uuid.uuid4().hex
    if _is_postgres(session):
        session.execute(
            text(
                "SELECT argus_private.create_hypothesis("
                ":id, :case_id, CAST(:ints AS text[]), CAST(:roles AS text[]), "
                ":stmt, :reasoning, :unc_status, :unc_expl, :testability, :challenge, "
                "CAST(:alt_ids AS text[]), CAST(:alt_expl AS text[]), :alt_absence, "
                "CAST(:unk_ids AS text[]), CAST(:unk_natures AS text[]), :no_unk, "
                "CAST(:con_ids AS text[]), CAST(:con_expl AS text[]), :no_con, "
                ":ac, :aid, :ver)"
            ),
            {
                "id": hyp_id, "case_id": case.id,
                "ints": "{" + ",".join(i for i, _ in groundings) + "}",
                "roles": "{" + ",".join(r for _, r in groundings) + "}",
                "stmt": explanatory_statement, "reasoning": reasoning_description,
                "unc_status": uncertainty_status, "unc_expl": uncertainty_explanation,
                "testability": testability_statement, "challenge": challenge_condition,
                "alt_ids": "{" + ",".join(a for a, _ in alternatives) + "}",
                "alt_expl": _pg_text_array([e for _, e in alternatives]),
                "alt_absence": alternative_absence_explanation,
                "unk_ids": "{" + ",".join(u for u, _ in limiting_unknowns) + "}",
                "unk_natures": _pg_text_array([n for _, n in limiting_unknowns]),
                "no_unk": no_current_unknowns_explanation,
                "con_ids": "{" + ",".join(c for c, _ in challenging_contradictions) + "}",
                "con_expl": _pg_text_array([e for _, e in challenging_contradictions]),
                "no_con": no_current_contradictions_explanation,
                "ac": actor.actor_class.value, "aid": actor.actor_id,
                "ver": actor.ai_model_version,
            },
        )
        session.commit()
        return session.get(Hypothesis, hyp_id)

    # SQLite path: identical semantics, citation under the head lock.
    _validate_boundary_targets(session, case.id, limiting_unknowns, challenging_contradictions)
    for alt_id, relation_explanation in alternatives:
        target = session.get(Hypothesis, alt_id)
        alt_codes = adm.validate_hypothesis_alternative(
            self_link=alt_id == hyp_id,
            both_exist=target is not None,
            same_case=target is not None and target.case_id == case.id,
            duplicate=False,
            relation_explanation=relation_explanation,
            actor_class=actor.actor_class,
        )
        if alt_codes:
            _raise(alt_codes, "HypothesisAlternative")

    session.get(CaseAuditHead, case.id, with_for_update=True)
    n = (session.execute(select(func.count()).select_from(Hypothesis).where(
        Hypothesis.case_id == case.id)).scalar() or 0) + 1
    articulation = (
        AlternativeArticulation.ALTERNATIVE_LINKED_AT_CREATION
        if alternatives
        else AlternativeArticulation.NONE_CURRENTLY_ARTICULATED_AT_CREATION
    )
    hypothesis = Hypothesis(
        id=hyp_id, case_id=case.id, citation=f"HYP-{n:06d}",
        explanatory_statement=explanatory_statement,
        reasoning_description=reasoning_description,
        uncertainty_status=UncertaintyStatus(uncertainty_status),
        uncertainty_explanation=uncertainty_explanation,
        testability_statement=testability_statement,
        challenge_condition=challenge_condition,
        alternative_articulation_at_creation=articulation,
        alternative_absence_explanation=alternative_absence_explanation,
        no_current_unknowns_explanation=no_current_unknowns_explanation,
        no_current_contradictions_explanation=no_current_contradictions_explanation,
        created_by_class=actor.actor_class.value, created_by_id=actor.actor_id,
    )
    session.add(hypothesis)
    session.flush()
    for int_id, role in groundings:
        interp = session.get(Interpretation, int_id)
        session.add(HypothesisGrounding(
            hypothesis_id=hyp_id, interpretation_id=int_id,
            interpretation_fingerprint=fingerprints.interpretation_fingerprint_v2(
                interp.meaning_statement, interp.reasoning_description,
                interp.uncertainty_status.value, interp.uncertainty_explanation,
            ),
            grounding_role=HypothesisGroundingRole(role),
        ))
    audit.emit(session, case_id=case.id, actor=actor, action="claim-created",
               target_type="Hypothesis", target_id=hyp_id,
               detail={"citation": hypothesis.citation,
                       "interpretations": [i for i, _ in groundings],
                       "uncertainty_status": uncertainty_status,
                       "alternative_articulation": articulation.value})
    for alt_id, relation_explanation in alternatives:
        _insert_alternative(session, hyp_id, alt_id, relation_explanation, actor,
                            case_id=case.id)
    for unk_id, nature in limiting_unknowns:
        link = UnknownLink(unknown_id=unk_id, target_type="Hypothesis",
                           target_id=hyp_id, nature=nature)
        session.add(link)
        session.flush()
        audit.emit(session, case_id=case.id, actor=actor, action="unknown-linked",
                   target_type="UnknownLink", target_id=link.id,
                   detail={"unknown_id": unk_id, "target_type": "Hypothesis",
                           "target_id": hyp_id})
    for con_id, explanation in challenging_contradictions:
        _insert_contradiction_link(session, con_id, hypothesis, explanation, actor)
    session.commit()
    return hypothesis


def _pg_text_array(values: list[str]) -> str | None:
    """Render a text[] literal with quoting safe for free prose."""
    if not values:
        return "{}"
    quoted = ",".join('"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"' for v in values)
    return "{" + quoted + "}"


def _insert_alternative(
    session: Session, a_id: str, b_id: str, relation_explanation: str,
    actor: Actor, *, case_id: str,
) -> HypothesisAlternative:
    lo, hi = sorted((a_id, b_id))
    link = HypothesisAlternative(
        hypothesis_a_id=lo, hypothesis_b_id=hi,
        relation_explanation=relation_explanation,
        linked_by_class=actor.actor_class.value, linked_by_id=actor.actor_id,
    )
    session.add(link)
    session.flush()
    audit.emit(session, case_id=case_id, actor=actor,
               action="hypothesis-alternative-linked",
               target_type="HypothesisAlternative", target_id=link.id,
               detail={"hypothesis_a_id": lo, "hypothesis_b_id": hi})
    return link


def _insert_contradiction_link(
    session: Session, con_id: str, hypothesis: Hypothesis, explanation: str,
    actor: Actor,
) -> ContradictionLink:
    link = ContradictionLink(
        contradiction_id=con_id, hypothesis_id=hypothesis.id,
        hypothesis_fingerprint=fingerprints.hypothesis_fingerprint_v1(
            hypothesis.explanatory_statement, hypothesis.reasoning_description,
            hypothesis.uncertainty_status.value, hypothesis.uncertainty_explanation,
            hypothesis.testability_statement, hypothesis.challenge_condition,
        ),
        explanation=explanation,
        linked_by_class=actor.actor_class.value, linked_by_id=actor.actor_id,
    )
    session.add(link)
    session.flush()
    audit.emit(session, case_id=hypothesis.case_id, actor=actor,
               action="contradiction-linked",
               target_type="ContradictionLink", target_id=link.id,
               detail={"contradiction_id": con_id, "hypothesis_id": hypothesis.id,
                       "relationship_type": adm.CHALLENGED_BY_CONTRADICTION})
    return link


def link_hypothesis_alternative(
    session: Session, *, hypothesis_a: Hypothesis, hypothesis_b_id: str,
    relation_explanation: str, actor: Actor,
) -> HypothesisAlternative:
    """The dedicated later-articulation operation (Session 012, Amendment 4):
    the first Hypothesis must not acquire an alternative only as a side
    effect of another creation path. Modifies neither Hypothesis."""
    target = session.get(Hypothesis, hypothesis_b_id)
    lo, hi = sorted((hypothesis_a.id, hypothesis_b_id))
    duplicate = session.execute(select(HypothesisAlternative).where(
        HypothesisAlternative.hypothesis_a_id == lo,
        HypothesisAlternative.hypothesis_b_id == hi,
    )).scalars().first() is not None
    codes = adm.validate_hypothesis_alternative(
        self_link=hypothesis_a.id == hypothesis_b_id,
        both_exist=target is not None,
        same_case=target is not None and target.case_id == hypothesis_a.case_id,
        duplicate=duplicate,
        relation_explanation=relation_explanation,
        actor_class=actor.actor_class,
    )
    if codes:
        _raise(codes, "HypothesisAlternative")
    if _is_postgres(session):
        link_id = uuid.uuid4().hex
        session.execute(
            text("SELECT argus_private.link_hypothesis_alternative(:id, :a, :b, :expl, :ac, :aid, :ver)"),
            {"id": link_id, "a": hypothesis_a.id, "b": hypothesis_b_id,
             "expl": relation_explanation, "ac": actor.actor_class.value,
             "aid": actor.actor_id, "ver": actor.ai_model_version},
        )
        session.commit()
        return session.get(HypothesisAlternative, link_id)
    session.get(CaseAuditHead, hypothesis_a.case_id, with_for_update=True)
    link = _insert_alternative(session, hypothesis_a.id, hypothesis_b_id,
                               relation_explanation, actor,
                               case_id=hypothesis_a.case_id)
    session.commit()
    return link


def retract_hypothesis(
    session: Session, hypothesis: Hypothesis, actor: Actor, *, reason: str
) -> Hypothesis:
    """Retraction retracts one explanation. It promotes no sibling, removes
    no alternative link, and alters no boundary record."""
    if actor.actor_class is not ActorClass.HUMAN:
        raise ConstitutionalViolation("ONT-PRN-007", "Hypothesis retraction is human-only.")
    if not reason or not reason.strip():
        raise ConstitutionalViolation("ONT-PRN-006", "Retraction requires a non-empty reason.")
    if _is_postgres(session):
        session.execute(
            text("SELECT argus_private.retract_hypothesis(:id, :ac, :aid, :ver, :reason)"),
            {"id": hypothesis.id, "ac": actor.actor_class.value,
             "aid": actor.actor_id, "ver": actor.ai_model_version, "reason": reason},
        )
        session.commit()
        session.expire(hypothesis)
        return hypothesis
    hypothesis.retracted_at = datetime.now(timezone.utc)
    hypothesis.retraction_reason = reason
    audit.emit(session, case_id=hypothesis.case_id, actor=actor,
               action="claim-retracted", target_type="Hypothesis",
               target_id=hypothesis.id, detail={"reason": reason})
    session.commit()
    return hypothesis


# ---- Derived states (never stored; Python renderings) ----

def hypothesis_health(session: Session, hypothesis: Hypothesis) -> str:
    rows = session.execute(select(HypothesisGrounding).where(
        HypothesisGrounding.hypothesis_id == hypothesis.id)).scalars().all()
    states = _interpretation_states(
        session, hypothesis.case_id,
        [(g.interpretation_id, g.grounding_role.value) for g in rows],
    )
    return adm.hypothesis_health(states)


def current_alternative_state(session: Session, hypothesis: Hypothesis) -> str:
    links = session.execute(select(HypothesisAlternative).where(
        (HypothesisAlternative.hypothesis_a_id == hypothesis.id)
        | (HypothesisAlternative.hypothesis_b_id == hypothesis.id)
    )).scalars().all()
    counterpart_active = []
    for link in links:
        other_id = (link.hypothesis_b_id if link.hypothesis_a_id == hypothesis.id
                    else link.hypothesis_a_id)
        other = session.get(Hypothesis, other_id)
        counterpart_active.append(other is not None and other.retracted_at is None)
    return adm.current_alternative_state(tuple(counterpart_active))


def unknown_boundary_state(session: Session, hypothesis: Hypothesis) -> str:
    links = session.execute(select(UnknownLink).where(
        UnknownLink.target_type == "Hypothesis",
        UnknownLink.target_id == hypothesis.id,
        UnknownLink.retracted_at.is_(None),
    )).scalars().all()
    unresolved = []
    for link in links:
        resolved = session.execute(select(UnknownResolution).where(
            UnknownResolution.unknown_id == link.unknown_id)).scalars().first()
        unresolved.append(resolved is None)
    return adm.unknown_boundary_state(tuple(unresolved))


def contradiction_boundary_state(session: Session, hypothesis: Hypothesis) -> str:
    links = session.execute(select(ContradictionLink).where(
        ContradictionLink.hypothesis_id == hypothesis.id,
        ContradictionLink.retracted_at.is_(None),
    )).scalars().all()
    undisposed = []
    for link in links:
        disposed = session.execute(select(ContradictionDisposition).where(
            ContradictionDisposition.contradiction_id == link.contradiction_id
        )).scalars().first()
        undisposed.append(disposed is None)
    return adm.contradiction_boundary_state(tuple(undisposed))
