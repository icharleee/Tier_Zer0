"""Slice 2A — Competing Interpretations (ODE Hypothesis H4).

H4 (refined): independent implementations can preserve multiple admissible
Interpretations over the same grounded Observations without assigning
epistemic priority, comparative strength, or preferred status to any
Interpretation. Technical ordering (citations, creation order) is permitted
and documented as non-evidentiary; epistemic preference is forbidden.

The refusal matrix below is transcribed from CONSTITUTIONAL_PREDICATES.md
0.3.0 — triangulation leg 3 (ONT-PRN-015).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from argus.domain import admissibility as adm
from argus.domain.actors import ActorClass, human, system
from argus.domain.chain import verify_case_chain
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import Interpretation, InterpretationGrounding
from argus.ingestion.interpretations import (
    create_interpretation,
    grounding_health,
    retract_interpretation,
)
from argus.ingestion.observations import (
    create_observation,
    create_source_locator,
    retract_source_locator,
)
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128 + b"ARGUS-SYNTHETIC-2A"

MEANING_A = "The visible blue sedan is stationary at the curb."
MEANING_B = (
    "This interpretation differs from INT-000001 because it treats the "
    "visible vehicle as stationary rather than arriving."
)
REASONING = "The vehicle's position is identical at the start and end of the cited window."
UNC_EXPL = (
    "No material uncertainty has been identified from the cited observations, "
    "but the interpretation remains provisional."
)

# ---- Refusal matrix, transcribed (leg 3) ----
S = adm.ObservationGroundingState
VALID_G = (S(exists=True, grounded=True),)
REFUSAL_MATRIX = {
    "valid": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN, VALID_G, ()),
    "meaning-required": ("  ", REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN, VALID_G,
                         (adm.MEANING_REQUIRED,)),
    "reasoning-required": (MEANING_A, "", "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN, VALID_G,
                           (adm.REASONING_REQUIRED,)),
    "uncertainty-status-required": (MEANING_A, REASONING, "CERTAIN", UNC_EXPL, ActorClass.HUMAN,
                                    VALID_G, (adm.UNCERTAINTY_STATUS_REQUIRED,)),
    "uncertainty-explanation-required": (MEANING_A, REASONING, "MATERIAL", " ", ActorClass.HUMAN,
                                         VALID_G, (adm.UNCERTAINTY_EXPLANATION_REQUIRED,)),
    "unsupported-actor": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.AI, VALID_G,
                          (adm.UNSUPPORTED_ACTOR,)),
    "no-grounded-observations": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN,
                                 (), (adm.NO_GROUNDED_OBSERVATIONS,)),
    "unknown-observation": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN,
                            (S(exists=False),), (adm.UNKNOWN_OBSERVATION,)),
    "observation-retracted": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN,
                              (S(exists=True, retracted=True),), (adm.OBSERVATION_RETRACTED,)),
    "observation-ungrounded": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN,
                               (S(exists=True, grounded=False),), (adm.OBSERVATION_UNGROUNDED,)),
    "cross-case-grounding": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN,
                             (S(exists=True, grounded=True, same_case=False),),
                             (adm.INT_CROSS_CASE,)),
    "comparative-ranking": (MEANING_A + " This is more likely than INT-000001.", REASONING,
                            "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN, VALID_G,
                            (adm.COMPARATIVE_RANKING,)),
    "invalid-grounding-role": (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, ActorClass.HUMAN,
                               (S(exists=True, grounded=True, role="DECISIVE"),),
                               (adm.INVALID_GROUNDING_ROLE,)),
}


class TestPythonRendering:
    def test_interpretation_admissibility_matrix(self):
        """ONT-INT-001 → Articles III, IV, IX: every row of the canonical
        refusal matrix, decisions and codes both."""
        for name, (m, r, us, ue, actor, g, expected) in REFUSAL_MATRIX.items():
            codes = adm.validate_interpretation(
                meaning_statement=m, reasoning_description=r,
                uncertainty_status=us, uncertainty_explanation=ue,
                actor_class=actor, groundings=g,
            )
            assert sorted(codes) == sorted(expected), name

    def test_no_certain_status_exists(self):
        """Article IX: 'none identified' stays distinct from 'none exists' —
        there is no status meaning certain."""
        assert "CERTAIN" not in adm.VALID_UNCERTAINTY_STATUSES
        assert adm.VALID_UNCERTAINTY_STATUSES == {
            "ACKNOWLEDGED", "MATERIAL", "LIMITING", "UNRESOLVED"
        }

    def test_grounding_health_derived(self):
        """ONT-INT-001 → Article II: GROUNDED iff one live grounding remains;
        degradation is a derived surface, never stored state."""
        assert adm.interpretation_grounding_health(VALID_G) == "GROUNDED"
        assert adm.interpretation_grounding_health(()) == "DEGRADED"
        assert adm.interpretation_grounding_health(
            (S(exists=True, retracted=True), S(exists=True, grounded=True))
        ) == "GROUNDED"
        assert adm.interpretation_grounding_health(
            (S(exists=True, grounded=False),)
        ) == "DEGRADED"


@pytest.mark.postgres
class TestExperimentH4:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 2A competing interpretations",
            legal_authority_basis="Test warrant 2026-SYN-2A", responsible=investigator,
        )

    @pytest.fixture()
    def grounded_observation(self, pg_session, store, pg_case, investigator, verifier):
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 2A image.",
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
        ), locator

    def _make(self, pg_session, pg_case, obs, investigator, meaning, status="ACKNOWLEDGED"):
        return create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement=meaning, reasoning_description=REASONING,
            uncertainty_status=status, uncertainty_explanation=UNC_EXPL,
            actor=investigator,
        )

    def test_h4_competing_interpretations_coexist_without_preference(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """H4 acceptance (Articles IV, IX): two admissible Interpretations
        over the SAME grounded Observation — no epistemic-ranking fields, no
        preferred constraint, symmetric exposure, order non-evidentiary."""
        obs, _ = grounded_observation
        a = self._make(pg_session, pg_case, obs, investigator, MEANING_A)
        b = self._make(pg_session, pg_case, obs, investigator, MEANING_B, status="MATERIAL")

        # Coexistence over identical grounding.
        assert a.citation == "INT-000001" and b.citation == "INT-000002"
        ga = pg_session.execute(select(InterpretationGrounding).where(
            InterpretationGrounding.interpretation_id == a.id)).scalars().all()
        gb = pg_session.execute(select(InterpretationGrounding).where(
            InterpretationGrounding.interpretation_id == b.id)).scalars().all()
        assert {g.observation_id for g in ga} == {g.observation_id for g in gb}

        # No epistemic-ranking field exists (schema scan, both tables).
        forbidden = ("rank", "preferred", "primary", "weight", "priority", "order")
        for table in (Interpretation.__table__, InterpretationGrounding.__table__):
            for col in table.columns:
                assert not any(f in col.name.lower() for f in forbidden), col.name

        # No preferred/primary constraint in the database.
        constraints = [r for r in pg_session.execute(text(
            "SELECT conname FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
            "WHERE t.relname IN ('interpretations','interpretation_groundings')"
        )).scalars()]
        assert not any("preferred" in c or "primary_int" in c or "rank" in c for c in constraints)

        # Symmetric exposure: identical field surface for both records.
        rows = pg_session.execute(
            select(Interpretation).where(Interpretation.case_id == pg_case.id)
            .order_by(Interpretation.citation)  # technical, non-evidentiary order
        ).scalars().all()
        assert len(rows) == 2
        assert all(r.reasoning_description and r.uncertainty_explanation for r in rows)

        # Chain verifies with both creations audited.
        assert verify_case_chain(pg_session, pg_case.id).valid

    def test_h4_retraction_does_not_promote_sibling(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """H4 assertion (Article IV): retracting one Interpretation has no
        effect on siblings — no promotion, no field changes; and the retracted
        record's groundings and uncertainty remain inspectable."""
        obs, _ = grounded_observation
        a = self._make(pg_session, pg_case, obs, investigator, MEANING_A)
        b = self._make(pg_session, pg_case, obs, investigator, MEANING_B, status="MATERIAL")
        before = (b.citation, b.uncertainty_status, b.meaning_statement)

        retract_interpretation(pg_session, a, investigator, reason="Author withdrew after re-review.")
        pg_session.expire_all()
        assert a.retracted_at is not None
        assert (b.citation, b.uncertainty_status, b.meaning_statement) == before
        # Historical reasoning stays inspectable (amendment requirement).
        assert a.uncertainty_explanation == UNC_EXPL
        ga = pg_session.execute(select(InterpretationGrounding).where(
            InterpretationGrounding.interpretation_id == a.id)).scalars().all()
        assert len(ga) == 1 and ga[0].statement_fingerprint

    def test_h4_validator_conformance(self, pg_session, pg_case, grounded_observation, investigator):
        """H4/H3 methodology: the SQL validator agrees with the transcribed
        matrix on inputs expressible against real records."""
        obs, _ = grounded_observation

        def sql_validate(m, r, us, ue, actor, obs_ids, roles):
            arr = "{" + ",".join(obs_ids) + "}" if obs_ids else "{}"
            rarr = "{" + ",".join(roles) + "}" if roles else "{}"
            return sorted(pg_session.execute(text(
                "SELECT argus_private.validate_interpretation(:c, CAST(:o AS text[]), :m, :r, :us, :ue, :a, CAST(:roles AS text[]))"
            ), {"c": pg_case.id, "o": arr, "m": m, "r": r, "us": us, "ue": ue,
                "a": actor, "roles": rarr}).scalar())

        checks = [
            ("valid", (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, "HUMAN", [obs.id], ["SUPPORTING"]), ()),
            ("meaning", ("  ", REASONING, "ACKNOWLEDGED", UNC_EXPL, "HUMAN", [obs.id], ["SUPPORTING"]),
             (adm.MEANING_REQUIRED,)),
            ("status", (MEANING_A, REASONING, "CERTAIN", UNC_EXPL, "HUMAN", [obs.id], ["SUPPORTING"]),
             (adm.UNCERTAINTY_STATUS_REQUIRED,)),
            ("actor", (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, "AI", [obs.id], ["SUPPORTING"]),
             (adm.UNSUPPORTED_ACTOR,)),
            ("none", (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, "HUMAN", [], []),
             (adm.NO_GROUNDED_OBSERVATIONS,)),
            ("unknown", (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, "HUMAN", ["deadbeef"], ["SUPPORTING"]),
             (adm.UNKNOWN_OBSERVATION,)),
            ("comparative", (MEANING_A + " more likely than INT-000001", REASONING, "ACKNOWLEDGED",
                             UNC_EXPL, "HUMAN", [obs.id], ["SUPPORTING"]), (adm.COMPARATIVE_RANKING,)),
            ("role", (MEANING_A, REASONING, "ACKNOWLEDGED", UNC_EXPL, "HUMAN", [obs.id], ["DECISIVE"]),
             (adm.INVALID_GROUNDING_ROLE,)),
        ]
        divergences = [
            f"{name}: pg={sql_validate(*inputs)} expected={sorted(exp)}"
            for name, inputs, exp in checks
            if sql_validate(*inputs) != sorted(exp)
        ]
        assert not divergences, "H4 falsified for:\n" + "\n".join(divergences)

    def test_comparative_fixture_refused_at_db(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """Amendment 1 → Article IX: 'more likely than INT-000001' is refused
        by the lexical guard even when Python is bypassed; the safe fixture
        (differs-because) is admissible."""
        from sqlalchemy.exc import DBAPIError

        obs, _ = grounded_observation
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.create_interpretation('cmp01', :c, CAST(:o AS text[]),"
                " CAST(:roles AS text[]), :m, :r, 'ACKNOWLEDGED', :ue, 'HUMAN', 'det.x', NULL)"
            ), {"c": pg_case.id, "o": "{" + obs.id + "}", "roles": "{SUPPORTING}",
                "m": "This is more likely than INT-000001.", "r": REASONING, "ue": UNC_EXPL})
            pg_session.commit()
        pg_session.rollback()
        assert "comparative-ranking-not-yet-modeled" in str(err.value)

        b = self._make(pg_session, pg_case, obs, investigator, MEANING_B)
        assert b.citation == "INT-000001"  # admissible: distinguishes without ranking

    def test_grounding_snapshot_and_health_both_renderings(
        self, pg_session, pg_case, grounded_observation, investigator
    ):
        """Amendment 3 → Articles II, V: the snapshot records exactly what was
        relied upon; degradation is derived identically in both renderings and
        never rewrites the Interpretation."""
        import hashlib

        obs, locator = grounded_observation
        a = self._make(pg_session, pg_case, obs, investigator, MEANING_A)
        g = pg_session.execute(select(InterpretationGrounding).where(
            InterpretationGrounding.interpretation_id == a.id)).scalars().one()
        assert g.statement_fingerprint == hashlib.sha256(
            obs.statement.encode("utf-8")).hexdigest()
        assert g.grounding_role.value == "SUPPORTING" and g.linked_at is not None

        assert grounding_health(pg_session, a) == "GROUNDED"
        assert pg_session.execute(text(
            "SELECT argus_private.interpretation_grounding_health(:id)"), {"id": a.id}
        ).scalar() == "GROUNDED"

        retract_source_locator(pg_session, locator, investigator, reason="Region incorrect.")
        assert grounding_health(pg_session, a) == "DEGRADED"
        assert pg_session.execute(text(
            "SELECT argus_private.interpretation_grounding_health(:id)"), {"id": a.id}
        ).scalar() == "DEGRADED"
        pg_session.expire(a)
        assert a.retracted_at is None  # surfaced, never auto-retracted
