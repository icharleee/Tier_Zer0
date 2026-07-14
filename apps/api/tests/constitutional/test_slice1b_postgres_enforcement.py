"""Slice 1B adversarial suite — PostgreSQL constitutional enforcement.

Every test attempts to corrupt constitutional state by BYPASSING the Python
domain services, proving the database is independently hostile to forbidden
writes. Trust boundary (ADR-0016): the application role and ordinary
operational roles cannot perform these mutations; privileged owners remain
inside the declared boundary, and their tampering is DETECTED by chain
verification (final tests), not prevented.

Runs against real PostgreSQL (DATABASE_URL = argus_app), never SQLite or
mocks (ADR-0006). Each test cites the ontology rule it protects (ADR-0010).
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.orm import Session

from argus.domain import canonical
from argus.domain.actors import human, system
from argus.domain.chain import verify_case_chain
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import ArtifactStatus, AuditEntry
from argus.domain.transitions import retract_artifact
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)
from argus.ingestion.store import LocalContentStore

pytestmark = pytest.mark.postgres

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64 + b"ARGUS-SYNTHETIC-EVIDENCE-1B"


@pytest.fixture()
def store(tmp_path):
    return LocalContentStore(tmp_path / "content")


@pytest.fixture()
def investigator():
    return human("det.reyes")


@pytest.fixture()
def verifier():
    return system("ingest-verifier-01", human_authority="det.reyes")


@pytest.fixture()
def case(pg_session, investigator):
    return create_case(
        pg_session,
        title="Slice 1B adversarial case",
        legal_authority_basis="Test warrant 2026-SYN-1B",
        responsible=investigator,
    )


@pytest.fixture()
def active_artifact(pg_session, store, case, investigator, verifier):
    staged = stage_upload(store, SYNTHETIC_IMAGE)
    artifact = create_artifact_record(
        pg_session,
        staged,
        case=case,
        actor=investigator,
        media_type="image/png",
        acquisition_description="Synthetic image for database-enforcement tests.",
    )
    verify_and_activate(pg_session, store, artifact, verifier)
    assert artifact.status is ArtifactStatus.ACTIVE
    return artifact


def _expect_db_rejection(session: Session, sql: str, params: dict | None = None) -> str:
    """Execute raw SQL expecting the database itself to refuse; return the
    error text. Rolls the session back to a clean state."""
    with pytest.raises((ProgrammingError, DBAPIError)) as err:
        session.execute(text(sql), params or {})
        session.commit()
    session.rollback()
    return str(err.value)


class TestDirectMutationHostility:
    def test_direct_update_original_digest_fails(self, pg_session, active_artifact):
        """ONT-EVA-001 → Article V: the original hash cannot be mutated
        after constitutional record creation — refused at the database."""
        msg = _expect_db_rejection(
            pg_session,
            "UPDATE public.evidence_artifacts SET hash_digest = 'forged' WHERE id = :id",
            {"id": active_artifact.id},
        )
        assert "permission denied" in msg

    def test_direct_status_update_fails_for_app_role(self, pg_session, active_artifact):
        """ONT-PRN-012 → Article VIII: lifecycle state is not writable as a
        bare column by the application role — only the named transition
        functions can move it."""
        msg = _expect_db_rejection(
            pg_session,
            "UPDATE public.evidence_artifacts SET status = 'RETRACTED' WHERE id = :id",
            {"id": active_artifact.id},
        )
        assert "permission denied" in msg

    def test_direct_delete_artifact_fails(self, pg_session, active_artifact):
        """ONT-PRN-006 → Article V: nothing disappears — physical deletion
        refused at the database."""
        msg = _expect_db_rejection(
            pg_session,
            "DELETE FROM public.evidence_artifacts WHERE id = :id",
            {"id": active_artifact.id},
        )
        assert "permission denied" in msg

    def test_direct_audit_update_fails(self, pg_session, case):
        """ONT-AUD-001 → Article VIII: audit entries are append-only."""
        msg = _expect_db_rejection(
            pg_session,
            "UPDATE public.audit_entries SET action = 'rewritten-history' WHERE case_id = :c",
            {"c": case.id},
        )
        assert "permission denied" in msg

    def test_direct_audit_delete_fails(self, pg_session, case):
        """ONT-AUD-001 → Article VIII."""
        msg = _expect_db_rejection(
            pg_session,
            "DELETE FROM public.audit_entries WHERE case_id = :c",
            {"c": case.id},
        )
        assert "permission denied" in msg

    def test_direct_audit_insert_fails(self, pg_session, case):
        """ONT-AUD-001: the ONLY insert path is the append function — a
        hand-rolled entry (which could forge hashes) is refused."""
        msg = _expect_db_rejection(
            pg_session,
            """
            INSERT INTO public.audit_entries
                (id, case_id, seq, actor_class, actor_id, action, target_type,
                 target_id, outcome, occurred_at, chain_version,
                 previous_event_hash, event_hash)
            VALUES ('f00d', :c, 999, 'HUMAN', 'forger', 'forged', 'Case',
                    :c, 'SUCCEEDED', now(), 1, repeat('0', 64), repeat('f', 64))
            """,
            {"c": case.id},
        )
        assert "permission denied" in msg

    def test_direct_head_update_fails(self, pg_session, case):
        """ONT-AUD-001 (ADR-0016): the chain head advances only inside the
        append function."""
        msg = _expect_db_rejection(
            pg_session,
            "UPDATE public.case_audit_heads SET last_sequence = 999 WHERE case_id = :c",
            {"c": case.id},
        )
        assert "permission denied" in msg

    def test_staged_is_not_a_persistable_status(self, pg_session, case, investigator):
        """ONT-EVA-001 / ADR-0007 §2: STAGED is pre-constitutional and is not
        an accepted database value — the CHECK constraint refuses it."""
        msg = _expect_db_rejection(
            pg_session,
            """
            INSERT INTO public.evidence_artifacts
                (id, case_id, status, hash_algorithm, hash_digest, size_bytes,
                 media_type, acquisition_description, ingested_by_class,
                 ingested_by_id, human_authority, storage_ref, created_at)
            VALUES ('feed01', :c, 'STAGED', 'sha-256', repeat('a', 64), 1,
                    'image/png', 'x', 'HUMAN', 'det.reyes', 'det.reyes',
                    'staging/x', now())
            """,
            {"c": case.id},
        )
        assert "ck_artifact_status" in msg


class TestTransitionFunctionEnforcement:
    def test_invalid_predecessor_transition_fails_and_appends_no_event(
        self, pg_session, active_artifact
    ):
        """ONT-PRN-012 → Article VIII: ACTIVE -> ACTIVE is not in the
        allowed-predecessor registry; the failed transaction leaves no event."""
        before = pg_session.execute(
            select(AuditEntry).where(AuditEntry.case_id == active_artifact.case_id)
        ).scalars().all()
        msg = _expect_db_rejection(
            pg_session,
            "SELECT argus_private.activate_evidence_artifact(:id, 'SYSTEM', 'v01', NULL, :d)",
            {"id": active_artifact.id, "d": active_artifact.hash_digest},
        )
        assert "ONT-PRN-012" in msg
        after = pg_session.execute(
            select(AuditEntry).where(AuditEntry.case_id == active_artifact.case_id)
        ).scalars().all()
        assert len(after) == len(before)  # no event from the rolled-back attempt

    def test_unauthorized_actor_transition_fails_at_db(self, pg_session, active_artifact):
        """ONT-PRN-007 → Article II: a SYSTEM actor cannot retract, even when
        Python is bypassed and the function is called directly."""
        msg = _expect_db_rejection(
            pg_session,
            "SELECT argus_private.retract_evidence_artifact(:id, 'SYSTEM', 'rogue', NULL, 'cleanup', NULL)",
            {"id": active_artifact.id},
        )
        assert "ONT-PRN-012/ONT-PRN-007" in msg

    def test_transition_core_not_callable_by_app_role(self, pg_session, active_artifact):
        """Defense in depth: the core transition function is not granted to
        the application role — only the named wrappers are."""
        msg = _expect_db_rejection(
            pg_session,
            "SELECT argus_private.transition_artifact(:id, 'SEALED', 'HUMAN', 'x', NULL, 'artifact-sealed', NULL)",
            {"id": active_artifact.id},
        )
        assert "permission denied" in msg

    def test_activation_without_matching_digest_fails_at_db(
        self, pg_session, store, case, investigator
    ):
        """ONT-EVA-001 / ADR-0007 §6: no activation without a verification
        basis matching the recorded original hash."""
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            pg_session, staged, case=case, actor=investigator,
            media_type="image/png", acquisition_description="digest-check test",
        )
        msg = _expect_db_rejection(
            pg_session,
            "SELECT argus_private.activate_evidence_artifact(:id, 'SYSTEM', 'v01', NULL, 'wrong-digest')",
            {"id": artifact.id},
        )
        assert "ONT-EVA-001" in msg

    def test_successful_transition_appends_event_atomically(
        self, pg_session, active_artifact, investigator
    ):
        """D-AUD → Articles V, VIII: transition and event commit together."""
        retract_artifact(
            pg_session, active_artifact, investigator,
            reason="Superseded by higher-resolution rescan.",
        )
        pg_session.commit()
        pg_session.expire_all()
        assert active_artifact.status is ArtifactStatus.RETRACTED
        assert active_artifact.retraction_reason  # set inside the definer fn
        last = pg_session.execute(
            select(AuditEntry)
            .where(AuditEntry.case_id == active_artifact.case_id)
            .order_by(AuditEntry.seq.desc())
        ).scalars().first()
        assert last.action == "artifact-retracted"
        assert last.actor_class == "HUMAN"

    def test_repeated_activation_is_idempotent_at_service_level(
        self, pg_session, store, active_artifact, verifier
    ):
        """ADR-0007 §4: re-running verification confirms state rather than
        manufacturing another activation event."""
        n_before = pg_session.execute(
            select(AuditEntry).where(AuditEntry.case_id == active_artifact.case_id)
        ).scalars().all()
        verify_and_activate(pg_session, store, active_artifact, verifier)
        n_after = pg_session.execute(
            select(AuditEntry).where(AuditEntry.case_id == active_artifact.case_id)
        ).scalars().all()
        assert len(n_after) == len(n_before)


class TestChainIntegrity:
    def test_concurrent_appends_gapless_per_case(self, pg_engine, pg_session, case):
        """ONT-AUD-001 (ADR-0016) → Article VIII: after all successful
        transactions commit, the per-case sequence is unique and gapless and
        the chain verifies. Assignment order between threads is NOT asserted
        (AGC test correction)."""
        from argus.domain import audit as audit_mod

        start_seq = 1  # case-created
        n_threads, per_thread = 4, 5
        errors: list[Exception] = []
        case_id = case.id  # resolve on this thread; ORM objects are not shared

        def worker(worker_id: int) -> None:
            try:
                with Session(pg_engine) as s:
                    for i in range(per_thread):
                        audit_mod.emit(
                            s,
                            case_id=case_id,
                            actor=human(f"det.thread{worker_id}"),
                            action="case-designation-changed",
                            target_type="Case",
                            target_id=case_id,
                            detail={"note": f"w{worker_id}-{i}"},
                        )
                        s.commit()
            except Exception as exc:  # surfaced below
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(w,)) for w in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, errors

        n = n_threads * per_thread
        seqs = [
            row
            for row in pg_session.execute(
                select(AuditEntry.seq)
                .where(AuditEntry.case_id == case_id)
                .order_by(AuditEntry.seq)
            ).scalars()
        ]
        assert len(seqs) == start_seq + n
        assert len(set(seqs)) == len(seqs)
        assert seqs[0] == 1 and seqs[-1] == start_seq + n
        assert seqs == list(range(1, start_seq + n + 1))
        result = verify_case_chain(pg_session, case_id)
        assert result.valid, result.findings

    def test_chain_verification_valid_after_full_loop(
        self, pg_session, active_artifact
    ):
        """ONT-AUD-001 → Article VIII: the Python verifier recomputes every
        PostgreSQL-produced hash from stored bytes — this is also the deep
        parity proof of the two chain_version=1 renderings."""
        result = verify_case_chain(pg_session, active_artifact.case_id)
        assert result.valid, result.findings
        assert result.entries_checked >= 3

    def test_canonicalization_parity_python_vs_postgres(self, pg_session):
        """ADR-0016: the two renderings of canonical JSON agree, including
        nested objects, arrays, escapes, and non-ASCII."""
        payload = {"b": 1, "aa": [True, None, "x\né=\\"], "ç": {"k2": "v", "k10": 7}}
        pg_text = pg_session.execute(
            text("SELECT argus_private.canonical_jsonb(CAST(:j AS jsonb))"),
            {"j": __import__("json").dumps(payload)},
        ).scalar()
        assert pg_text == canonical.canonical_json(payload)

    def test_privileged_corruption_is_detected(
        self, pg_session, pg_admin_engine, active_artifact
    ):
        """ONT-AUD-001 → Articles VIII, IX: tampering from INSIDE the trust
        boundary (privileged role) cannot be prevented — it is DETECTED.
        Tamper-evident, not tamper-proof."""
        result = verify_case_chain(pg_session, active_artifact.case_id)
        assert result.valid
        with pg_admin_engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE public.audit_entries SET action = 'history-rewritten' "
                    "WHERE case_id = :c AND seq = 2"
                ),
                {"c": active_artifact.case_id},
            )
        pg_session.expire_all()
        result = verify_case_chain(pg_session, active_artifact.case_id)
        assert not result.valid
        assert any("seq 2" in f for f in result.findings)
