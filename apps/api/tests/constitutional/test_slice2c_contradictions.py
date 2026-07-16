"""Slice 2C — Contradictions as boundary objects (ODE Hypothesis H6).

H6 (refined): independent implementations can preserve a formally scoped
incompatibility among multiple constitutionally admissible claims without
changing their admissibility, assigning epistemic priority, or adjudicating
which claim survives.

Expectations transcribed from CONSTITUTIONAL_PREDICATES.md 0.5.0
(triangulation leg 3, ONT-PRN-015).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from argus.domain import admissibility as adm
from argus.domain.actors import ActorClass
from argus.domain.chain import verify_case_chain
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import (
    Contradiction,
    ContradictionDisposition,
    ContradictionMember,
    Interpretation,
)
from argus.ingestion.contradictions import (
    contradiction_health,
    contradiction_status,
    create_contradiction,
    dispose_contradiction,
    set_contradiction_review,
)
from argus.ingestion.interpretations import create_interpretation, retract_interpretation
from argus.ingestion.observations import create_observation, create_source_locator
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128 + b"ARGUS-SYNTHETIC-2C"

# The gold fixture: genuinely mutually exclusive propositions.
MEANING_A = "The visible vehicle is stationary throughout 19:42:00-19:42:10."
MEANING_B = "The visible vehicle changes position during 19:42:00-19:42:10."
SCOPE = "Same vehicle, same camera, same coordinate frame, same interval 19:42:00-19:42:10."
BASIS = ("A single vehicle cannot be both stationary throughout and changing "
         "position during the same interval in the same coordinate frame.")
DESCRIPTION = "Interpretations assert mutually exclusive motion states under identical scope."
REASONING = "Position comparison across the cited frames."
UNC = "No material uncertainty has been identified from the cited observations, but the interpretation remains provisional."

M = adm.MemberState
VALID_MEMBERS = (M(exists=True), M(exists=True))
CONTRADICTION_MATRIX = {
    "valid": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN, VALID_MEMBERS, 2), ()),
    "description-required": (("  ", "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN, VALID_MEMBERS, 2),
                             (adm.CON_DESCRIPTION_REQUIRED,)),
    "type-required": ((DESCRIPTION, "VIBES", SCOPE, BASIS, ActorClass.HUMAN, VALID_MEMBERS, 2),
                      (adm.CON_TYPE_REQUIRED,)),
    "scope-required": ((DESCRIPTION, "DESCRIPTIVE", "", BASIS, ActorClass.HUMAN, VALID_MEMBERS, 2),
                       (adm.CON_SCOPE_REQUIRED,)),
    "basis-required": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, " ", ActorClass.HUMAN, VALID_MEMBERS, 2),
                       (adm.CON_BASIS_REQUIRED,)),
    "insufficient-members": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN,
                              (M(exists=True),), 1), (adm.CON_INSUFFICIENT_MEMBERS,)),
    "duplicate-members": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN,
                           VALID_MEMBERS, 1),
                          (adm.CON_DUPLICATE_MEMBERS, adm.CON_INSUFFICIENT_MEMBERS)),
    "ai-actor": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.AI, VALID_MEMBERS, 2),
                 (adm.CON_UNSUPPORTED_ACTOR,)),
    "adjudicative": ((DESCRIPTION + " Interpretation A is wrong.", "DESCRIPTIVE", SCOPE, BASIS,
                      ActorClass.HUMAN, VALID_MEMBERS, 2), (adm.CON_ADJUDICATIVE_LANGUAGE,)),
    "member-retracted": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN,
                          (M(exists=True), M(exists=True, retracted=True)), 2),
                         (adm.CNM_MEMBER_RETRACTED,)),
    "cross-case": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN,
                    (M(exists=True), M(exists=True, same_case=False)), 2),
                   (adm.CNM_CROSS_CASE_MEMBER,)),
    "invalid-role": ((DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, ActorClass.HUMAN,
                      (M(exists=True), M(exists=True, role="REFUTING")), 2),
                     (adm.CNM_INVALID_ROLE,)),
}


class TestPythonRendering:
    def test_contradiction_admissibility_matrix(self):
        """ONT-CON-001/CNM-001 → Articles III, IV: incompatibility requires
        an explicit basis; mere disagreement never becomes contradiction."""
        for name, ((d, t, s, b, actor, members, distinct), expected) in CONTRADICTION_MATRIX.items():
            codes = adm.validate_contradiction(
                description=d, contradiction_type=t, scope_definition=s,
                incompatibility_basis=b, actor_class=actor, members=members,
                distinct_member_count=distinct,
            )
            assert sorted(codes) == sorted(expected), name

    def test_disposition_matrix_and_no_adjudicative_outcome(self):
        """ONT-CDP-001 → Articles II, IV: five outcomes, none implying a
        member was proven correct."""
        assert adm.validate_contradiction_disposition("EXPLAINED", "Scopes differed.", ActorClass.HUMAN) == ()
        assert adm.CDP_OUTCOME_REQUIRED in adm.validate_contradiction_disposition(
            "MEMBER_A_CORRECT", "x", ActorClass.HUMAN)
        assert adm.CDP_RATIONALE_REQUIRED in adm.validate_contradiction_disposition(
            "WITHDRAWN", " ", ActorClass.HUMAN)
        assert adm.ACTOR_NOT_PERMITTED in adm.validate_contradiction_disposition(
            "WITHDRAWN", "x", ActorClass.SYSTEM)
        for forbidden in ("CORRECT", "WINNER", "PREVAILS", "REFUTED"):
            assert forbidden not in adm.DISPOSITION_OUTCOMES

    def test_contradiction_health_derived(self):
        """Amendment 3 → Article II: CURRENT/DEGRADED derived; degradation
        surfaces, disposition remains human."""
        assert adm.contradiction_health(VALID_MEMBERS) == "CURRENT"
        assert adm.contradiction_health((M(exists=True), M(exists=True, retracted=True))) == "DEGRADED"
        assert adm.contradiction_health((M(exists=False), M(exists=True))) == "DEGRADED"


@pytest.mark.postgres
class TestExperimentH6:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 2C incompatibility",
            legal_authority_basis="Test warrant 2026-SYN-2C", responsible=investigator,
        )

    @pytest.fixture()
    def competing_interpretations(self, pg_session, store, pg_case, investigator, verifier):
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 2C video still.",
        )
        verify_and_activate(pg_session, store, artifact, verifier)
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 8, "end": 100}, actor=investigator,
        )
        obs = create_observation(
            pg_session, case=pg_case, locator_ids=[locator.id],
            statement="Blue sedan visible.", method_description="Direct visual review.",
            actor=investigator,
        )
        a = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement=MEANING_A, reasoning_description=REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator,
        )
        b = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement=MEANING_B, reasoning_description=REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator,
        )
        return a, b

    def _snap(self, i: Interpretation) -> tuple:
        return (i.citation, i.meaning_statement, i.reasoning_description,
                i.uncertainty_status, i.uncertainty_explanation, i.retracted_at)

    def _make(self, pg_session, pg_case, a, b, investigator):
        return create_contradiction(
            pg_session, case=pg_case,
            members=[("Interpretation", a.id), ("Interpretation", b.id)],
            description=DESCRIPTION, contradiction_type="DESCRIPTIVE",
            scope_definition=SCOPE, incompatibility_basis=BASIS,
            actor=investigator,
        )

    def test_h6_acceptance_incompatibility_without_adjudication(
        self, pg_session, pg_case, competing_interpretations, investigator
    ):
        """Given two admissible Interpretations with mutually exclusive
        propositions under an explicitly shared scope: record their formal
        incompatibility with provenance and audit while both remain
        admissible, unretracted, byte-identical, symmetrically exposed —
        and dispose it without identifying a winner or modifying either
        member. (ONT-CON/CNM/CDP-001 → Articles II, IV, VIII, IX.)"""
        a, b = competing_interpretations
        before_a, before_b = self._snap(a), self._snap(b)

        con = self._make(pg_session, pg_case, a, b, investigator)
        assert con.citation == "CON-000001"
        members = pg_session.execute(select(ContradictionMember).where(
            ContradictionMember.contradiction_id == con.id)).scalars().all()
        assert len(members) == 2
        assert all(m.member_role == "INCOMPATIBLE_CLAIM" for m in members)
        assert all(m.member_fingerprint for m in members)

        # Creation changed no member state.
        pg_session.expire_all()
        assert self._snap(a) == before_a and self._snap(b) == before_b

        # Both renderings agree on health and status.
        assert contradiction_health(pg_session, con) == "CURRENT"
        assert pg_session.execute(text(
            "SELECT argus_private.contradiction_health(:id)"), {"id": con.id}
        ).scalar() == "CURRENT"
        assert contradiction_status(pg_session, con) == "OPEN"

        # Human disposition: the incompatibility persists, formally.
        dispose_contradiction(
            pg_session, contradiction=con, outcome="UNRESOLVED",
            rationale="The incompatibility stands; no current basis disposes of its facts.",
            informing_refs=None, actor=investigator,
        )
        assert contradiction_status(pg_session, con) == "UNRESOLVED"

        # Disposition changed no member state; both stay symmetric.
        pg_session.expire_all()
        assert self._snap(a) == before_a and self._snap(b) == before_b
        assert verify_case_chain(pg_session, pg_case.id).valid

    def test_h6_no_survivor_surface_and_no_promotion(
        self, pg_session, pg_case, competing_interpretations, investigator
    ):
        """H6 assertions: no adjudicative field or constraint exists; member
        retraction degrades health without auto-disposition or promotion."""
        a, b = competing_interpretations
        con = self._make(pg_session, pg_case, a, b, investigator)

        forbidden = ("winner", "prevail", "surviv", "adjudicat", "correct", "refut", "preferred", "rank")
        for table in (Contradiction.__table__, ContradictionMember.__table__,
                      ContradictionDisposition.__table__):
            for col in table.columns:
                assert not any(f in col.name.lower() for f in forbidden), col.name
        constraints = [r for r in pg_session.execute(text(
            "SELECT conname FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
            "WHERE t.relname LIKE 'contradiction%'")).scalars()]
        assert not any(any(f in c for f in forbidden) for c in constraints)

        before_b = self._snap(b)
        retract_interpretation(pg_session, a, investigator, reason="Author withdrew after re-review.")
        pg_session.expire_all()
        # Health degrades in BOTH renderings; nothing else moves.
        assert contradiction_health(pg_session, con) == "DEGRADED"
        assert pg_session.execute(text(
            "SELECT argus_private.contradiction_health(:id)"), {"id": con.id}
        ).scalar() == "DEGRADED"
        assert contradiction_status(pg_session, con) == "OPEN"  # no auto-disposition
        assert self._snap(b) == before_b  # no promotion
        members = pg_session.execute(select(ContradictionMember).where(
            ContradictionMember.contradiction_id == con.id)).scalars().all()
        assert len(members) == 2  # historical membership immutable

    def test_h6_validator_conformance(self, pg_session, pg_case, competing_interpretations):
        """H6: SQL and Python renderings agree on expressible matrix rows."""
        a, b = competing_interpretations

        def sql_validate(d, t, s, basis, actor, member_ids):
            mt = "{" + ",".join("Interpretation" for _ in member_ids) + "}"
            mi = "{" + ",".join(member_ids) + "}"
            roles = "{" + ",".join("INCOMPATIBLE_CLAIM" for _ in member_ids) + "}"
            return sorted(pg_session.execute(text(
                "SELECT argus_private.validate_contradiction(:c, CAST(:mt AS text[]),"
                " CAST(:mi AS text[]), :d, :t, :s, :b, :a, CAST(:r AS text[]))"
            ), {"c": pg_case.id, "mt": mt, "mi": mi, "d": d, "t": t, "s": s,
                "b": basis, "a": actor, "r": roles}).scalar())

        checks = [
            ("valid", (DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, "HUMAN", [a.id, b.id]), ()),
            ("type", (DESCRIPTION, "VIBES", SCOPE, BASIS, "HUMAN", [a.id, b.id]),
             (adm.CON_TYPE_REQUIRED,)),
            ("scope", (DESCRIPTION, "DESCRIPTIVE", " ", BASIS, "HUMAN", [a.id, b.id]),
             (adm.CON_SCOPE_REQUIRED,)),
            ("insufficient", (DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, "HUMAN", [a.id]),
             (adm.CON_INSUFFICIENT_MEMBERS,)),
            ("duplicate", (DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, "HUMAN", [a.id, a.id]),
             (adm.CON_DUPLICATE_MEMBERS, adm.CON_INSUFFICIENT_MEMBERS)),
            ("ai", (DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, "AI", [a.id, b.id]),
             (adm.CON_UNSUPPORTED_ACTOR,)),
            ("adjudicative", (DESCRIPTION + " Interpretation A is wrong.", "DESCRIPTIVE",
                              SCOPE, BASIS, "HUMAN", [a.id, b.id]),
             (adm.CON_ADJUDICATIVE_LANGUAGE,)),
            ("unknown-member", (DESCRIPTION, "DESCRIPTIVE", SCOPE, BASIS, "HUMAN",
                                [a.id, "deadbeef"]), (adm.CNM_UNKNOWN_MEMBER,)),
        ]
        divergences = [
            f"{name}: pg={sql_validate(*inputs)} expected={sorted(exp)}"
            for name, inputs, exp in checks if sql_validate(*inputs) != sorted(exp)
        ]
        assert not divergences, "H6 falsified for:\n" + "\n".join(divergences)

    def test_disposition_terminal_human_only_at_db(
        self, pg_session, pg_case, competing_interpretations, investigator
    ):
        """ONT-CDP-001/PRN-012 → Article II: SYSTEM disposition refused in
        the function; second dispositions refused; review refused after
        disposition; direct INSERT refused."""
        from sqlalchemy.exc import DBAPIError

        a, b = competing_interpretations
        con = self._make(pg_session, pg_case, a, b, investigator)

        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.dispose_contradiction('d1', :c, 'WITHDRAWN', 'cleanup', NULL, 'SYSTEM', 'svc', NULL)"
            ), {"c": con.id})
            pg_session.commit()
        pg_session.rollback()
        assert "actor-not-permitted" in str(err.value)

        dispose_contradiction(pg_session, contradiction=con, outcome="EXPLAINED",
                              rationale="On review, the intervals differ by one frame; scopes were not identical.",
                              informing_refs=None, actor=investigator)
        with pytest.raises((ConstitutionalViolation, DBAPIError)):
            dispose_contradiction(pg_session, contradiction=con, outcome="WITHDRAWN",
                                  rationale="Second thoughts.", informing_refs=None,
                                  actor=investigator)
        pg_session.rollback()
        with pytest.raises((ConstitutionalViolation, DBAPIError)):
            set_contradiction_review(pg_session, con, investigator, under_review=True)
        pg_session.rollback()

        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "INSERT INTO public.contradictions (id, case_id, citation, description,"
                " contradiction_type, scope_definition, incompatibility_basis,"
                " operational_state, created_by_class, created_by_id, created_at)"
                " VALUES ('f00d2c', :c, 'CON-000099', 'forged', 'LOGICAL', 's', 'b',"
                " 'OPEN', 'HUMAN', 'x', now())"
            ), {"c": pg_case.id})
            pg_session.commit()
        pg_session.rollback()
        assert "permission denied" in str(err.value)
