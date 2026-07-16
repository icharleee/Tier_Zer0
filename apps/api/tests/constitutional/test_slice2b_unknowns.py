"""Slice 2B — Unknowns and evidentiary limits (ODE Hypothesis H5).

H5 (final): independent implementations preserve explicit epistemic
boundaries while ensuring that neither absence nor newly acquired knowledge
automatically changes previously admitted reasoning. Knowledge changes; the
system does not; humans decide what to do next.

Expectations transcribed from CONSTITUTIONAL_PREDICATES.md 0.4.0
(triangulation leg 3, ONT-PRN-015).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from argus.domain import admissibility as adm
from argus.domain.actors import ActorClass, human
from argus.domain.chain import verify_case_chain
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import Interpretation, Unknown, UnknownLink
from argus.ingestion.interpretations import create_interpretation
from argus.ingestion.observations import create_observation, create_source_locator
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)
from argus.ingestion.unknowns import (
    create_unknown,
    link_unknown,
    resolve_unknown,
    set_under_review,
    unknown_status,
)

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128 + b"ARGUS-SYNTHETIC-2B"
GOLD_QUESTION = "Who possessed the device between 19:42 and 20:15?"
REASONING = "The vehicle's position is identical at the start and end of the cited window."
UNC_EXPL = "The possession window remains unestablished; see the named Unknown."

# ---- Refusal matrix, transcribed (leg 3) ----
UNKNOWN_MATRIX = {
    "valid": (GOLD_QUESTION, ActorClass.HUMAN, ()),
    "question-required": ("   ", ActorClass.HUMAN, (adm.QUESTION_REQUIRED,)),
    "not-a-question": ("The device was possessed by someone.", ActorClass.HUMAN,
                       (adm.NOT_A_QUESTION,)),
    "task-shaped-interview": ("Interview the neighbor about the vehicle?", ActorClass.HUMAN,
                              (adm.TASK_SHAPED,)),
    "task-shaped-todo": ("What is the plate? todo: check registry?", ActorClass.HUMAN,
                         (adm.TASK_SHAPED,)),
    "task-shaped-need-to": ("Need to establish the timeline?", ActorClass.HUMAN,
                            (adm.TASK_SHAPED,)),
    "ai-actor": (GOLD_QUESTION, ActorClass.AI, (adm.UNK_UNSUPPORTED_ACTOR,)),
}
RESOLUTION_MATRIX = {
    "answered-with-evidence": ("ANSWERED", "Established by OBS-000001.", ("claim1",),
                               ActorClass.HUMAN, ()),
    "answered-no-evidence": ("ANSWERED", "It just seems resolved.", (),
                             ActorClass.HUMAN, (adm.ANSWER_REQUIRES_EVIDENCE,)),
    "partial-no-evidence": ("PARTIALLY_ANSWERED", "Partially clear.", (),
                            ActorClass.HUMAN, (adm.ANSWER_REQUIRES_EVIDENCE,)),
    "no-rationale": ("WITHDRAWN", "  ", (), ActorClass.HUMAN, (adm.RATIONALE_REQUIRED,)),
    "system-actor": ("WITHDRAWN", "Cleanup.", (), ActorClass.SYSTEM,
                     (adm.ACTOR_NOT_PERMITTED,)),
    "unresolvable-ok": ("UNRESOLVABLE", "Device destroyed; no source remains.", (),
                        ActorClass.HUMAN, ()),
}


class TestPythonRendering:
    def test_unknown_admissibility_matrix(self):
        """ONT-UNK-001 / ONT-PRN-020 → Article IX: a question, never a task."""
        for name, (q, actor, expected) in UNKNOWN_MATRIX.items():
            assert sorted(adm.validate_unknown(q, actor)) == sorted(expected), name

    def test_resolution_admissibility_matrix(self):
        """ONT-UNR-001 → Articles I, II: an answer without evidence is not an
        answer; disposition is human-only."""
        for name, (t, r, claims, actor, expected) in RESOLUTION_MATRIX.items():
            assert sorted(adm.validate_unknown_resolution(t, r, claims, actor)) == sorted(expected), name

    def test_unresolved_interpretation_requires_named_unknown(self):
        """ONT-PRN-019 accumulated obligation → Article IX: UNRESOLVED
        uncertainty names the limit that produces it."""
        base = dict(
            meaning_statement="M", reasoning_description="R",
            uncertainty_status="UNRESOLVED", uncertainty_explanation=UNC_EXPL,
            actor_class=ActorClass.HUMAN,
            groundings=(adm.ObservationGroundingState(exists=True, grounded=True),),
        )
        assert adm.UNRESOLVED_REQUIRES_UNKNOWN in adm.validate_interpretation(**base)
        assert adm.UNRESOLVED_REQUIRES_UNKNOWN in adm.validate_interpretation(
            **base, unresolved_unknown_named=False)
        assert adm.validate_interpretation(**base, unresolved_unknown_named=True) == ()


@pytest.mark.postgres
class TestExperimentH5:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 2B negative knowledge",
            legal_authority_basis="Test warrant 2026-SYN-2B", responsible=investigator,
        )

    @pytest.fixture()
    def grounded_observation(self, pg_session, store, pg_case, investigator, verifier):
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 2B image.",
        )
        verify_and_activate(pg_session, store, artifact, verifier)
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 8, "end": 100}, actor=investigator,
        )
        return create_observation(
            pg_session, case=pg_case, locator_ids=[locator.id],
            statement="Blue sedan visible.", method_description="Direct visual review.",
            actor=investigator,
        )

    def _snapshot(self, interp: Interpretation) -> tuple:
        return (interp.citation, interp.meaning_statement, interp.reasoning_description,
                interp.uncertainty_status, interp.uncertainty_explanation,
                interp.retracted_at)

    def test_h5_acceptance_knowledge_changes_the_system_does_not(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """Given a grounded Observation and an UNRESOLVED Interpretation
        naming its Unknown: the bounded record stays byte-identical while the
        question is open, through UNDER_REVIEW, and after human resolution
        with evidence — newly acquired knowledge never propagates as
        automated reasoning; linked Interpretations change only through
        explicit human reconsideration. (ONT-PRN-020, ONT-UNK/UNR-001 →
        Articles II, IX.)"""
        obs = grounded_observation
        unknown = create_unknown(pg_session, case=pg_case, question=GOLD_QUESTION,
                                 actor=investigator)
        assert unknown.citation == "UNK-000001"
        interp = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement="The sedan's possessor during the window is unestablished.",
            reasoning_description=REASONING,
            uncertainty_status="UNRESOLVED", uncertainty_explanation=UNC_EXPL,
            actor=investigator, unresolved_unknown_id=unknown.id,
        )
        # The validity link exists (boundary family, ONT-PRN-021).
        link = pg_session.execute(select(UnknownLink).where(
            UnknownLink.unknown_id == unknown.id)).scalars().one()
        assert (link.target_type, link.target_id) == ("Interpretation", interp.id)

        before = self._snapshot(interp)
        assert unknown_status(pg_session, unknown) == "OPEN"

        # Operational marking carries no conclusion and changes nothing bounded.
        set_under_review(pg_session, unknown, investigator, under_review=True)
        assert unknown_status(pg_session, unknown) == "UNDER_REVIEW"
        pg_session.expire(interp)
        assert self._snapshot(interp) == before

        # Human resolution WITH evidence.
        resolve_unknown(
            pg_session, unknown=unknown, resolution_type="ANSWERED",
            rationale="Possession established by the cited observation.",
            answering_claims=[obs.id], actor=investigator,
        )
        assert unknown_status(pg_session, unknown) == "ANSWERED"
        # Derived in SQL identically.
        assert pg_session.execute(
            text("SELECT argus_private.unknown_status(:id)"), {"id": unknown.id}
        ).scalar() == "ANSWERED"

        # THE H5 CORE: the bounded Interpretation is byte-identical. Knowing
        # more did not change meaning; that requires explicit human
        # reconsideration (a new interpretation or a human retraction).
        pg_session.expire_all()
        assert self._snapshot(interp) == before
        assert verify_case_chain(pg_session, pg_case.id).valid

    def test_h5_validator_conformance(self, pg_session, pg_case, investigator):
        """H5: the SQL and Python renderings of validate_unknown agree on the
        transcribed matrix."""
        divergences = []
        for name, (q, actor, expected) in UNKNOWN_MATRIX.items():
            got = sorted(pg_session.execute(
                text("SELECT argus_private.validate_unknown(:q, :a)"),
                {"q": q, "a": actor.value},
            ).scalar())
            if got != sorted(expected):
                divergences.append(f"{name}: pg={got} matrix={sorted(expected)}")
        assert not divergences, "H5 falsified for:\n" + "\n".join(divergences)

    def test_disposition_human_only_and_evidence_required_at_db(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """ONT-PRN-007, ONT-UNR-001 → Articles I, II: bypassing Python still
        cannot resolve as SYSTEM or answer without evidence."""
        from sqlalchemy.exc import DBAPIError

        unknown = create_unknown(pg_session, case=pg_case, question=GOLD_QUESTION,
                                 actor=investigator)
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.resolve_unknown('r1', :u, 'WITHDRAWN', 'cleanup', NULL, 'SYSTEM', 'svc', NULL)"
            ), {"u": unknown.id})
            pg_session.commit()
        pg_session.rollback()
        assert "actor-not-permitted" in str(err.value)

        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.resolve_unknown('r2', :u, 'ANSWERED', 'seems fine', NULL, 'HUMAN', 'det.x', NULL)"
            ), {"u": unknown.id})
            pg_session.commit()
        pg_session.rollback()
        assert "answer-requires-evidence" in str(err.value)

        # Direct INSERT refused (SELECT-only grants).
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "INSERT INTO public.unknowns (id, case_id, citation, question,"
                " operational_state, created_by_class, created_by_id, created_at)"
                " VALUES ('f00d2b', :c, 'UNK-000099', 'Forged?', 'OPEN', 'HUMAN', 'x', now())"
            ), {"c": pg_case.id})
            pg_session.commit()
        pg_session.rollback()
        assert "permission denied" in str(err.value)

    def test_disposition_is_terminal_and_derived(
        self, pg_session, pg_case, investigator
    ):
        """ONT-PRN-012 → Article VIII: no second resolution; no operational
        transition after disposition; no epistemic column exists to flip."""
        from sqlalchemy.exc import DBAPIError

        unknown = create_unknown(pg_session, case=pg_case, question=GOLD_QUESTION,
                                 actor=investigator)
        resolve_unknown(pg_session, unknown=unknown, resolution_type="UNRESOLVABLE",
                        rationale="Device destroyed; no source remains.",
                        answering_claims=None, actor=investigator)
        with pytest.raises((ConstitutionalViolation, DBAPIError)):
            resolve_unknown(pg_session, unknown=unknown, resolution_type="WITHDRAWN",
                            rationale="Second thoughts.", answering_claims=None,
                            actor=investigator)
        pg_session.rollback()
        with pytest.raises((ConstitutionalViolation, DBAPIError)):
            set_under_review(pg_session, unknown, investigator, under_review=True)
        pg_session.rollback()
        # No epistemic disposition column exists on the unknowns table.
        cols = {c.name for c in Unknown.__table__.columns}
        assert "status" not in cols and "resolution" not in cols
        assert "operational_state" in cols  # the only, explicitly operational, state

    def test_unresolved_interpretation_refused_without_named_unknown_at_db(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """ONT-PRN-019 → Article IX: the accumulated obligation holds in the
        database rendering too."""
        obs = grounded_observation
        with pytest.raises(ConstitutionalViolation) as err:
            create_interpretation(
                pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
                meaning_statement="Unclear possession.", reasoning_description=REASONING,
                uncertainty_status="UNRESOLVED", uncertainty_explanation=UNC_EXPL,
                actor=investigator,
            )
        assert "unresolved-requires-named-unknown" in str(err.value)

    def test_open_unknown_changes_nothing_it_bounds(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """ONT-PRN-020 → Article IX: linking an Unknown to an admitted record
        leaves it byte-identical — absence never becomes evidence."""
        obs = grounded_observation
        interp = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement="The sedan was stationary.", reasoning_description=REASONING,
            uncertainty_status="ACKNOWLEDGED",
            uncertainty_explanation="No material uncertainty has been identified from the cited observations, but the interpretation remains provisional.",
            actor=investigator,
        )
        before = self._snapshot(interp)
        unknown = create_unknown(pg_session, case=pg_case, question=GOLD_QUESTION,
                                 actor=investigator)
        link_unknown(pg_session, unknown=unknown, target_type="Interpretation",
                     target_id=interp.id, nature="The possession window bounds this meaning.",
                     actor=investigator)
        pg_session.expire_all()
        assert self._snapshot(interp) == before
