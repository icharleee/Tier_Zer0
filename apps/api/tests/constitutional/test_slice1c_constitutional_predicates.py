"""Slice 1C — Constitutional predicates (ADR-0018; ODE Hypothesis H2).

The acceptance test, as redefined by the AGC: can every constitutional
predicate be derived identically by independent implementations?
Experiment One: can_support_observation — the canonical matrix
(docs/domain/CONSTITUTIONAL_PREDICATES.md) rendered independently in Python
and PostgreSQL, compared row by row for identical structural verdicts,
contextual verdicts, and canonical reason codes.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from argus.domain import predicates as P
from argus.domain.actors import ActorClass
from argus.domain.models import ArtifactStatus, CaseStatus
from argus.ingestion.service import create_artifact_record, create_case, stage_upload


@pytest.fixture()
def pg_case(pg_session, investigator):
    return create_case(
        pg_session,
        title="Slice 1C predicate case",
        legal_authority_basis="Test warrant 2026-SYN-1C",
        responsible=investigator,
    )

# The canonical eligibility matrix, transcribed from the normative artifact.
# (Artifact state, case state) -> (structural, contextual, reason codes).
# This literal is the TEST's rendering of the matrix — a third derivation,
# independent of both implementations.
A, C = ArtifactStatus, CaseStatus
CANONICAL_MATRIX: dict[tuple[ArtifactStatus, CaseStatus], tuple[bool, bool, tuple[str, ...]]] = {
    (A.ACTIVE, C.OPEN): (True, True, ()),
    (A.ACTIVE, C.SUSPENDED): (True, False, (P.CASE_SUSPENDED,)),
    (A.ACTIVE, C.CLOSED): (True, False, (P.CASE_CLOSED,)),
    (A.PENDING_VERIFICATION, C.OPEN): (False, False, (P.NOT_YET_VERIFIED,)),
    (A.PENDING_VERIFICATION, C.SUSPENDED): (False, False, (P.NOT_YET_VERIFIED, P.CASE_SUSPENDED)),
    (A.PENDING_VERIFICATION, C.CLOSED): (False, False, (P.NOT_YET_VERIFIED, P.CASE_CLOSED)),
    (A.QUARANTINED, C.OPEN): (False, False, (P.INTEGRITY_UNRESOLVED,)),
    (A.QUARANTINED, C.SUSPENDED): (False, False, (P.INTEGRITY_UNRESOLVED, P.CASE_SUSPENDED)),
    (A.QUARANTINED, C.CLOSED): (False, False, (P.INTEGRITY_UNRESOLVED, P.CASE_CLOSED)),
    (A.RETRACTED, C.OPEN): (False, False, (P.RETRACTED,)),
    (A.RETRACTED, C.SUSPENDED): (False, False, (P.RETRACTED, P.CASE_SUSPENDED)),
    (A.RETRACTED, C.CLOSED): (False, False, (P.RETRACTED, P.CASE_CLOSED)),
    (A.SEALED, C.OPEN): (True, False, (P.SEALED_ACCESS_RESTRICTED,)),
    (A.SEALED, C.SUSPENDED): (True, False, (P.SEALED_ACCESS_RESTRICTED, P.CASE_SUSPENDED)),
    (A.SEALED, C.CLOSED): (True, False, (P.SEALED_ACCESS_RESTRICTED, P.CASE_CLOSED)),
}


class TestPythonRendering:
    def test_predicate_matrix_python(self):
        """ONT-EVA-001, ONT-CAS-001, ONT-PRN-014 → Articles I, VI: the Python
        rendering reproduces every row of the canonical matrix, decisions and
        reason codes both."""
        for (a_status, c_status), (structural, contextual, reasons) in CANONICAL_MATRIX.items():
            d = P.can_support_observation(a_status, c_status)
            assert (d.structurally_eligible, d.contextually_eligible) == (structural, contextual), (
                f"{a_status.value}/{c_status.value}"
            )
            assert sorted(d.reasons) == sorted(reasons), f"{a_status.value}/{c_status.value}"

    def test_unknown_artifact_is_never_eligible(self):
        """ONT-EVA-001 → Article I: no constitutional record, no reasoning."""
        d = P.can_support_observation(None, C.OPEN)
        assert not d.structurally_eligible and not d.allowed
        assert d.reasons == (P.UNKNOWN_ARTIFACT,)

    def test_no_stored_eligibility_flag_exists(self):
        """ADR-0018 / Resolution 005: derived, never stored — no column on
        any model may persist an eligibility answer."""
        from argus.domain.models import Base

        for table in Base.metadata.tables.values():
            for column in table.columns:
                assert "eligib" not in column.name.lower(), (
                    f"{table.name}.{column.name} stores what must be derived"
                )

    def test_transition_predicates_derive_from_registry(self):
        """ONT-PRN-013 → Article VII: transition-authority predicates are the
        registry, asked politely — no second lifecycle rendering. Refusals
        carry canonical codes (ONT-PRN-007 / ONT-PRN-012)."""
        assert P.can_be_retracted(A.ACTIVE, ActorClass.HUMAN).allowed
        d = P.can_be_retracted(A.ACTIVE, ActorClass.SYSTEM)
        assert not d.allowed and d.reasons == (P.ACTOR_NOT_PERMITTED,)
        d = P.can_be_retracted(A.SEALED, ActorClass.HUMAN)
        assert not d.allowed and d.reasons == (P.NO_SUCH_TRANSITION,)
        assert P.can_be_sealed(A.ACTIVE, ActorClass.HUMAN).allowed
        assert not P.can_be_sealed(A.QUARANTINED, ActorClass.HUMAN).allowed
        assert P.can_be_unsealed(A.SEALED, ActorClass.HUMAN).allowed
        assert not P.can_be_unsealed(A.SEALED, ActorClass.AI).allowed


@pytest.mark.postgres
class TestExperimentH2:
    def test_predicate_conformance_python_vs_postgres(
        self, pg_session, pg_admin_engine, store, pg_case, investigator
    ):
        """ODE H2, Experiment One (ADR-0018 acceptance test): every matrix
        row derived identically by two implementations sharing no executable
        logic — same structural verdict, same contextual verdict, same
        canonical reason codes."""
        staged = stage_upload(store, b"predicate-conformance-artifact")
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="application/octet-stream",
            acquisition_description="H2 Experiment One artifact",
        )
        artifact_id, case_id = artifact.id, artifact.case_id
        divergences: list[str] = []

        for (a_status, c_status), _expected in CANONICAL_MATRIX.items():
            with pg_admin_engine.begin() as conn:
                conn.execute(
                    text("UPDATE public.evidence_artifacts SET status = :s WHERE id = :id"),
                    {"s": a_status.value, "id": artifact_id},
                )
                conn.execute(
                    text("UPDATE public.cases SET status = :s WHERE id = :id"),
                    {"s": c_status.value, "id": case_id},
                )
            row = pg_session.execute(
                text("SELECT * FROM argus_private.can_support_observation(:id)"),
                {"id": artifact_id},
            ).one()
            pg_session.rollback()
            py = P.can_support_observation(a_status, c_status)
            pg_decision = (row.structurally_eligible, row.contextually_eligible, sorted(row.reasons))
            py_decision = (py.structurally_eligible, py.contextually_eligible, sorted(py.reasons))
            if pg_decision != py_decision:
                divergences.append(
                    f"{a_status.value}/{c_status.value}: pg={pg_decision} py={py_decision}"
                )

        # The unknown-artifact row.
        row = pg_session.execute(
            text("SELECT * FROM argus_private.can_support_observation('no-such-id')")
        ).one()
        py = P.can_support_observation(None, C.OPEN)
        if (row.structurally_eligible, row.contextually_eligible, sorted(row.reasons)) != (
            py.structurally_eligible, py.contextually_eligible, sorted(py.reasons)
        ):
            divergences.append("unknown-artifact row diverged")

        assert not divergences, "H2 falsified for these rows:\n" + "\n".join(divergences)
