"""Slice 1D — the first epistemic object (ADR-0020; ODE Hypothesis H3).

H3 (refined): independent implementations of epistemic admissibility
converge when derived from a shared ontology and provenance model. The
experimental surface is the validator pair; the expectations below are the
canonical refusal matrix transcribed as this file's own literal — the third,
independent leg of the triangulation (ONT-PRN-015).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from argus.domain import admissibility as adm
from argus.domain.actors import Actor, ActorClass, human, system
from argus.domain.chain import verify_case_chain
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import (
    ArtifactStatus,
    AuditEntry,
    CaseStatus,
    Observation,
)
from argus.ingestion.observations import (
    create_observation,
    create_source_locator,
    observation_is_grounded,
    retract_source_locator,
)
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128 + b"ARGUS-SYNTHETIC-1D"
GOLD_STATEMENT = "Blue sedan visible."  # the gold-standard fixture: nothing inferred
GOLD_METHOD = "Direct visual review of the synthetic image."

# ---- The canonical refusal matrix, transcribed (triangulation leg 3) ----
# scenario name -> (statement, method, actor_class, case_status, groundings, expected codes)
G = adm.GroundingState
VALID_G = (G(exists=True, artifact_status=ArtifactStatus.ACTIVE),)
REFUSAL_MATRIX = {
    "valid": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN, VALID_G, ()),
    "empty-statement": ("   ", GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN, VALID_G,
                        (adm.MISSING_STATEMENT,)),
    "empty-method": (GOLD_STATEMENT, "", ActorClass.HUMAN, CaseStatus.OPEN, VALID_G,
                     (adm.MISSING_METHOD,)),
    "ai-actor": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.AI, CaseStatus.OPEN, VALID_G,
                 (adm.ACTOR_NOT_PERMITTED,)),
    "no-grounding": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN, (),
                     (adm.NO_GROUNDING,)),
    "unknown-locator": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN,
                        (G(exists=False),), (adm.UNKNOWN_LOCATOR,)),
    "retracted-locator": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN,
                          (G(exists=True, retracted=True, artifact_status=ArtifactStatus.ACTIVE),),
                          (adm.LOCATOR_RETRACTED,)),
    "cross-case": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN,
                   (G(exists=True, same_case=False, artifact_status=ArtifactStatus.ACTIVE),),
                   (adm.CROSS_CASE_GROUNDING,)),
    "quarantined-artifact": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.OPEN,
                             (G(exists=True, artifact_status=ArtifactStatus.QUARANTINED),),
                             ("ONT-EVA-001:integrity-unresolved",)),
    "case-closed": (GOLD_STATEMENT, GOLD_METHOD, ActorClass.HUMAN, CaseStatus.CLOSED, VALID_G,
                    ("ONT-CAS-001:case-closed",)),
}


class TestPythonRendering:
    def test_observation_admissibility_matrix(self):
        """ONT-OBS-001, ONT-PRN-004/-005/-007 → Articles I, II, III: every
        row of the canonical refusal matrix, decisions and codes both."""
        for name, (stmt, method, actor, case_status, groundings, expected) in REFUSAL_MATRIX.items():
            codes = adm.validate_observation(
                statement=stmt, method_description=method, actor_class=actor,
                case_status=case_status, groundings=groundings,
            )
            assert sorted(codes) == sorted(expected), name

    def test_locator_validation(self):
        """ONT-SRC-001, ONT-PRN-016 → Articles I, V: scope of support must be
        objectively checkable where possible."""
        ok = adm.validate_source_locator(ArtifactStatus.ACTIVE, "byte-range", {"start": 0, "end": 10}, 100)
        assert ok == ()
        assert adm.OUT_OF_BOUNDS in adm.validate_source_locator(
            ArtifactStatus.ACTIVE, "byte-range", {"start": 0, "end": 101}, 100)
        assert adm.OUT_OF_BOUNDS in adm.validate_source_locator(
            ArtifactStatus.ACTIVE, "byte-range", {"start": 5, "end": 5}, 100)
        assert adm.UNKNOWN_SCHEME in adm.validate_source_locator(
            ArtifactStatus.ACTIVE, "vibes", {}, 100)
        assert adm.ARTIFACT_NOT_ACTIVE in adm.validate_source_locator(
            ArtifactStatus.PENDING_VERIFICATION, "byte-range", {"start": 0, "end": 1}, 100)

    def test_is_grounded_single_predicate(self):
        """ADR-0020 §6, ONT-PRN-014 → Article IX: exactly one groundedness
        question — a constitutionally valid locator exists. No grading."""
        assert adm.is_grounded(VALID_G)
        assert not adm.is_grounded(())
        assert not adm.is_grounded((G(exists=True, retracted=True, artifact_status=ArtifactStatus.ACTIVE),))
        assert not adm.is_grounded((G(exists=True, artifact_status=ArtifactStatus.RETRACTED),))
        # One valid locator among degraded ones suffices — >= 1, nothing more.
        assert adm.is_grounded((G(exists=True, retracted=True, artifact_status=ArtifactStatus.ACTIVE),) + VALID_G)

    def test_observation_has_no_meaning_fields(self):
        """ONT-PRN-004 → Article I (the exclusions are load-bearing): the
        Observation schema carries perception only — no meaning, inference,
        ranking, or confidence surface exists to leak into."""
        forbidden = ("meaning", "interpret", "hypoth", "confiden", "rank", "score", "infer")
        for column in Observation.__table__.columns:
            assert not any(f in column.name.lower() for f in forbidden), column.name

    def test_ontology_class_is_derived_not_stored(self):
        """ADR-0020 §5 / Resolution 005: the ontological identity is a
        derived constant, not a column."""
        assert Observation.ONTOLOGY_CLASS == "ONT-OBS-001"
        assert "ontology_class" not in Observation.__table__.columns


class TestApplicationPath:
    def test_first_observation_python_path(self, session, store, case, investigator, verifier):
        """The constitutional loop at the application layer: artifact →
        locator → Observation, citation OBS-000001, grounded, audited."""
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            session, staged, case=case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 1D image.",
        )
        verify_and_activate(session, store, artifact, verifier)
        locator = create_source_locator(
            session, artifact=artifact, scheme="byte-range",
            payload={"start": 8, "end": 72}, actor=investigator,
        )
        obs = create_observation(
            session, case=case, locator_ids=[locator.id],
            statement=GOLD_STATEMENT, method_description=GOLD_METHOD,
            actor=investigator,
        )
        assert obs.citation == "OBS-000001"
        assert observation_is_grounded(session, obs)
        actions = [
            a for a in session.execute(
                select(AuditEntry.action).where(AuditEntry.case_id == case.id).order_by(AuditEntry.seq)
            ).scalars()
        ]
        assert actions[-2:] == ["locator-created", "claim-created"]
        # Degradation surfaces, never auto-retracts (Article II).
        retract_source_locator(session, locator, investigator, reason="Wrong region; replaced.")
        assert not observation_is_grounded(session, obs)
        assert obs.retracted_at is None


@pytest.mark.postgres
class TestExperimentH3:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 1D epistemic case",
            legal_authority_basis="Test warrant 2026-SYN-1D", responsible=investigator,
        )

    def _active_artifact(self, pg_session, store, case, investigator, verifier, data=SYNTHETIC_IMAGE):
        staged = stage_upload(store, data)
        artifact = create_artifact_record(
            pg_session, staged, case=case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 1D image.",
        )
        verify_and_activate(pg_session, store, artifact, verifier)
        return artifact

    def test_first_acceptance_test_of_observation(
        self, pg_session, store, pg_case, investigator, verifier
    ):
        """Given one ACTIVE EvidenceArtifact and one valid SourceLocator, can
        ARGUS create exactly one constitutionally valid Observation whose
        provenance, audit history, and eligibility are independently
        verifiable — without introducing Interpretation or Hypothesis?
        (ONT-OBS-001, ONT-SRC-001, ONT-PRN-004/-005/-016 → Articles I, III,
        V, VIII.)"""
        artifact = self._active_artifact(pg_session, store, pg_case, investigator, verifier)
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 8, "end": 72}, actor=investigator,
        )
        obs = create_observation(
            pg_session, case=pg_case, locator_ids=[locator.id],
            statement=GOLD_STATEMENT, method_description=GOLD_METHOD,
            actor=investigator,
        )
        # Exactly one, with both identities.
        all_obs = pg_session.execute(select(Observation)).scalars().all()
        assert len(all_obs) == 1
        assert obs.citation == "OBS-000001" and Observation.ONTOLOGY_CLASS == "ONT-OBS-001"
        # Provenance: statement, method, actor, grounding — all present.
        assert obs.statement == GOLD_STATEMENT and obs.method_description == GOLD_METHOD
        assert obs.created_by_class == "HUMAN"
        # Groundedness, both renderings.
        assert observation_is_grounded(pg_session, obs)
        assert pg_session.execute(
            text("SELECT argus_private.is_observation_grounded(:id)"), {"id": obs.id}
        ).scalar() is True
        # Audit history verifiable end-to-end.
        result = verify_case_chain(pg_session, pg_case.id)
        assert result.valid, result.findings
        # The exclusions are load-bearing: no reasoning tables exist.
        tables = {
            r for r in pg_session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            ).scalars()
        }
        assert not any("interpret" in t or "hypoth" in t for t in tables)

    def test_h3_validator_conformance(
        self, pg_session, pg_admin_engine, store, pg_case, investigator, verifier
    ):
        """H3, Experiment One: the refusal matrix derived identically by the
        Python and PostgreSQL validators (which share no executable logic)."""
        artifact = self._active_artifact(pg_session, store, pg_case, investigator, verifier)
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 0, "end": 8}, actor=investigator,
        )
        # A second case with its own active artifact + locator (cross-case row).
        other_case = create_case(
            pg_session, title="Other case", legal_authority_basis="warrant-2",
            responsible=investigator,
        )
        other_artifact = self._active_artifact(
            pg_session, store, other_case, investigator, verifier, data=SYNTHETIC_IMAGE + b"2",
        )
        other_locator = create_source_locator(
            pg_session, artifact=other_artifact, scheme="byte-range",
            payload={"start": 0, "end": 8}, actor=investigator,
        )

        def sql_validate(stmt, method, actor_class, locator_ids):
            arr = "{" + ",".join(locator_ids) + "}" if locator_ids else "{}"
            return sorted(
                pg_session.execute(
                    text(
                        "SELECT argus_private.validate_observation(:c, CAST(:l AS text[]), :s, :m, :a)"
                    ),
                    {"c": pg_case.id, "l": arr, "s": stmt, "m": method, "a": actor_class},
                ).scalar()
            )

        def set_states(artifact_status=None, case_status=None, locator_retracted=None):
            with pg_admin_engine.begin() as conn:
                if artifact_status is not None:
                    conn.execute(text("UPDATE public.evidence_artifacts SET status=:s WHERE id=:id"),
                                 {"s": artifact_status, "id": artifact.id})
                if case_status is not None:
                    conn.execute(text("UPDATE public.cases SET status=:s WHERE id=:id"),
                                 {"s": case_status, "id": pg_case.id})
                if locator_retracted is not None:
                    conn.execute(text(
                        "UPDATE public.source_locators SET retracted_at = "
                        "CASE WHEN :r THEN now() ELSE NULL END WHERE id=:id"
                    ), {"r": locator_retracted, "id": locator.id})
            pg_session.expire_all()

        # (name, sql inputs, python expectation from the transcribed matrix)
        scenarios = [
            ("valid", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", [locator.id]), "valid", {}),
            ("empty-statement", ("  ", GOLD_METHOD, "HUMAN", [locator.id]), "empty-statement", {}),
            ("empty-method", (GOLD_STATEMENT, "", "HUMAN", [locator.id]), "empty-method", {}),
            ("ai-actor", (GOLD_STATEMENT, GOLD_METHOD, "AI", [locator.id]), "ai-actor", {}),
            ("no-grounding", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", []), "no-grounding", {}),
            ("unknown-locator", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", ["deadbeef"]), "unknown-locator", {}),
            ("retracted-locator", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", [locator.id]),
             "retracted-locator", {"locator_retracted": True}),
            ("cross-case", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", [other_locator.id]), "cross-case", {}),
            ("quarantined-artifact", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", [locator.id]),
             "quarantined-artifact", {"artifact_status": "QUARANTINED"}),
            ("case-closed", (GOLD_STATEMENT, GOLD_METHOD, "HUMAN", [locator.id]),
             "case-closed", {"case_status": "CLOSED"}),
        ]
        divergences = []
        for name, sql_inputs, matrix_key, state in scenarios:
            set_states(**{**{"artifact_status": "ACTIVE", "case_status": "OPEN",
                             "locator_retracted": False}, **state})
            expected = sorted(REFUSAL_MATRIX[matrix_key][5])
            got = sql_validate(*sql_inputs)
            if got != expected:
                divergences.append(f"{name}: pg={got} matrix={expected}")
        set_states(artifact_status="ACTIVE", case_status="OPEN", locator_retracted=False)
        assert not divergences, "H3 falsified for:\n" + "\n".join(divergences)

    def test_direct_insert_refused_and_ai_refused_at_db(
        self, pg_session, store, pg_case, investigator, verifier
    ):
        """ONT-OBS-001 → Articles I, II: bypassing Python still cannot create
        an observation directly, and the database itself refuses AI authors."""
        from sqlalchemy.exc import DBAPIError

        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "INSERT INTO public.observations (id, case_id, citation, statement,"
                " method_description, created_by_class, created_by_id, created_at)"
                " VALUES ('f00d1d', :c, 'OBS-000099', 'forged', 'none', 'HUMAN', 'x', now())"
            ), {"c": pg_case.id})
            pg_session.commit()
        pg_session.rollback()
        assert "permission denied" in str(err.value)

        artifact = self._active_artifact(pg_session, store, pg_case, investigator, verifier)
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 0, "end": 8}, actor=investigator,
        )
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.create_observation('ai01', :c, CAST(:l AS text[]),"
                " :s, :m, 'AI', 'wf-1', 'm/v/w', NULL, NULL)"
            ), {"c": pg_case.id, "l": "{" + locator.id + "}", "s": GOLD_STATEMENT, "m": GOLD_METHOD})
            pg_session.commit()
        pg_session.rollback()
        assert "actor-not-permitted" in str(err.value)

    def test_groundedness_degrades_on_retraction_both_renderings(
        self, pg_session, store, pg_case, investigator, verifier
    ):
        """ONT-PRN-006 → Articles II, V: retracting the sole locator degrades
        groundedness in both renderings; the observation is surfaced, never
        auto-retracted."""
        artifact = self._active_artifact(pg_session, store, pg_case, investigator, verifier)
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 0, "end": 8}, actor=investigator,
        )
        obs = create_observation(
            pg_session, case=pg_case, locator_ids=[locator.id],
            statement=GOLD_STATEMENT, method_description=GOLD_METHOD, actor=investigator,
        )
        retract_source_locator(pg_session, locator, investigator, reason="Region incorrect.")
        assert not observation_is_grounded(pg_session, obs)
        assert pg_session.execute(
            text("SELECT argus_private.is_observation_grounded(:id)"), {"id": obs.id}
        ).scalar() is False
        pg_session.expire(obs)
        assert obs.retracted_at is None  # human disposition, not automation
