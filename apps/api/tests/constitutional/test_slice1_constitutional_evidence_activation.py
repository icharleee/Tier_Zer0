"""Slice 1 constitutional tests — Constitutional Evidence Activation.

Every test declares the ontological rule it protects (ADR-0010 / ONT-PRN-009):
tests derive from the ontology, not from the implementation. Registry:
docs/domain/ONTOLOGY.md §7 and §9.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from argus.domain.actors import human, system
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import ArtifactStatus, AuditEntry
from argus.domain.transitions import reactivate_artifact, retract_artifact
from argus.ingestion.hashing import compute_digest
from argus.ingestion.service import (
    create_artifact_record,
    stage_upload,
    verify_and_activate,
)

# A minimal valid PNG header + payload: the synthetic image of the first
# acceptance test (ADR-0007 §9).
SYNTHETIC_IMAGE = (
    b"\x89PNG\r\n\x1a\n" + b"\x00" * 64 + b"ARGUS-SYNTHETIC-EVIDENCE-0001"
)


def _ingest(session, store, case, actor, data=SYNTHETIC_IMAGE):
    staged = stage_upload(store, data)
    artifact = create_artifact_record(
        session,
        staged,
        case=case,
        actor=actor,
        media_type="image/png",
        acquisition_description="Synthetic image generated for the Slice 1 "
        "acceptance test; no real-world source.",
    )
    return staged, artifact


def _audit_actions(session, case_id):
    rows = session.execute(
        select(AuditEntry)
        .where(AuditEntry.case_id == case_id)
        .order_by(AuditEntry.seq)
    ).scalars()
    return [(e.seq, e.action, e.actor_class, e.outcome.value) for e in rows]


class TestConstitutionalEvidenceActivation:
    def test_first_acceptance_test_of_argus(self, session, store, case, investigator, verifier):
        """THE acceptance test (ADR-0007 §9; ONT-EVA-001, ONT-AUD-001,
        ONT-PRN-005, ONT-PRN-012 → Articles I, V, VIII).

        Given a synthetic image: ingest it, compute its identity, verify its
        integrity, activate it, emit every required audit event, and make it
        eligible for Observation creation — without violating a single
        constitutional invariant.
        """
        staged, artifact = _ingest(session, store, case, investigator)

        # Identity computed by the system, not declared by the client.
        assert artifact.hash_algorithm == "sha-256"
        assert artifact.hash_digest == compute_digest(SYNTHETIC_IMAGE)

        # Constitutional availability begins only at activation.
        assert artifact.status is ArtifactStatus.PENDING_VERIFICATION
        assert not artifact.is_observation_eligible

        verify_and_activate(session, store, artifact, verifier)

        assert artifact.status is ArtifactStatus.ACTIVE
        assert artifact.is_observation_eligible
        assert artifact.storage_ref == f"sha-256/{artifact.hash_digest}"

        # Every required audit event, gapless, attributed (ONT-AUD-001).
        trail = _audit_actions(session, case.id)
        assert trail == [
            (1, "case-created", "HUMAN", "SUCCEEDED"),
            (2, "artifact-ingested", "HUMAN", "SUCCEEDED"),
            (3, "artifact-activated", "SYSTEM", "SUCCEEDED"),
        ]

        # Idempotent re-run (ADR-0007 §4) changes nothing.
        verify_and_activate(session, store, artifact, verifier)
        assert len(_audit_actions(session, case.id)) == 3

    def test_evidence_exists_but_is_not_yet_claimable(self, session, store, case, investigator):
        """ONT-EVA-001 → Article I: bytes present, upload succeeded, record
        committed — and still not constitutionally usable before activation
        (the permanent maxim of AGC Session 004)."""
        _, artifact = _ingest(session, store, case, investigator)
        assert artifact.status is ArtifactStatus.PENDING_VERIFICATION
        assert not artifact.is_observation_eligible

    def test_corrupted_content_is_quarantined_never_deleted(self, session, store, case, investigator, verifier):
        """ONT-EVA-001, ONT-PRN-006 → Articles II, V: integrity failure leads
        to QUARANTINED with bytes retained for human disposition; nothing
        disappears, including failed ingestions."""
        staged, artifact = _ingest(session, store, case, investigator)
        # Corruption between staging and verification.
        store.put_staged(staged.session_id, b"tampered-bytes")

        verify_and_activate(session, store, artifact, verifier)

        assert artifact.status is ArtifactStatus.QUARANTINED
        assert not artifact.is_observation_eligible
        assert artifact.storage_ref.startswith("quarantine/")
        # The record persists; the audit trail shows the quarantine.
        actions = [a for _, a, _, _ in _audit_actions(session, case.id)]
        assert "artifact-quarantined" in actions

    def test_no_provenance_no_claim_at_ingest(self, session, store, case, investigator):
        """ONT-PRN-005 → Articles I, III: an empty acquisition description is
        rejected — provenance is a precondition of existence, not metadata."""
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        with pytest.raises(ConstitutionalViolation) as err:
            create_artifact_record(
                session,
                staged,
                case=case,
                actor=investigator,
                media_type="image/png",
                acquisition_description="   ",
            )
        assert err.value.ontology_rule == "ONT-PRN-005"

    def test_transitions_are_explicit_no_invisible_state_changes(self, session, store, case, investigator, verifier):
        """ONT-PRN-012 → Article VIII: a transition absent from the
        allowed-predecessor registry cannot be performed by anyone."""
        _, artifact = _ingest(session, store, case, investigator)
        # PENDING_VERIFICATION -> SEALED exists in no lifecycle table.
        from argus.domain.transitions import seal_artifact

        with pytest.raises(ConstitutionalViolation) as err:
            seal_artifact(session, artifact, investigator, legal_basis="court order")
        assert err.value.ontology_rule == "ONT-PRN-012"

    def test_activation_requires_actual_verification(self, session, store, case, investigator, verifier):
        """ONT-EVA-001 → Article V: activation without a matching recomputed
        digest is impossible — there is no promotion path that skips
        integrity verification (ADR-0007 §6)."""
        _, artifact = _ingest(session, store, case, investigator)
        from argus.domain.transitions import activate_artifact

        with pytest.raises(ConstitutionalViolation) as err:
            activate_artifact(
                session, artifact, verifier, verified_digest="not-the-digest"
            )
        assert err.value.ontology_rule == "ONT-EVA-001"

    def test_quarantine_disposition_is_human_only(self, session, store, case, investigator, verifier):
        """ONT-PRN-007 → Article II: the system detects; humans dispose. A
        SystemProcess cannot reactivate quarantined evidence."""
        staged, artifact = _ingest(session, store, case, investigator)
        store.put_staged(staged.session_id, b"tampered-bytes")
        verify_and_activate(session, store, artifact, verifier)
        assert artifact.status is ArtifactStatus.QUARANTINED

        with pytest.raises(ConstitutionalViolation) as err:
            reactivate_artifact(
                session,
                artifact,
                verifier,  # SYSTEM actor — forbidden
                reverified_digest=artifact.hash_digest,
                rationale="automated recovery",
            )
        assert err.value.ontology_rule == "ONT-PRN-007"

        # A human, after verified recovery, may dispose.
        reactivate_artifact(
            session,
            artifact,
            human("det.reyes"),
            reverified_digest=artifact.hash_digest,
            rationale="storage fault confirmed and repaired; content re-verified",
        )
        assert artifact.status is ArtifactStatus.ACTIVE

    def test_retraction_is_human_with_reason_and_preserves_record(self, session, store, case, investigator, verifier):
        """ONT-PRN-006, ONT-PRN-007 → Articles II, V: retraction demands a
        human actor and a reason, and the record remains readable."""
        _, artifact = _ingest(session, store, case, investigator)
        verify_and_activate(session, store, artifact, verifier)

        with pytest.raises(ConstitutionalViolation):
            retract_artifact(session, artifact, verifier, reason="cleanup")  # SYSTEM

        with pytest.raises(ConstitutionalViolation):
            retract_artifact(session, artifact, investigator, reason="   ")

        retract_artifact(
            session, artifact, investigator, reason="Superseded by re-scan at higher resolution."
        )
        assert artifact.status is ArtifactStatus.RETRACTED
        assert artifact.retraction_reason
        assert artifact.retracted_at is not None  # preserved, not erased

    def test_ai_may_not_ingest_evidence(self, session, store, case):
        """ONT-EVA-001, ONT-PRN-007 → Article II: AIWorkflows propose; they do
        not introduce evidence into the system."""
        from argus.domain.actors import Actor, ActorClass

        ai = Actor(ActorClass.AI, "summarizer-wf", ai_model_version="m1/v1/wf1")
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        with pytest.raises(ConstitutionalViolation):
            create_artifact_record(
                session,
                staged,
                case=case,
                actor=ai,
                media_type="image/png",
                acquisition_description="AI-collected",
            )

    def test_audit_ordering_is_gapless_and_monotonic_per_case(self, session, store, case, investigator, verifier):
        """ONT-AUD-001 → Article VIII: per-case sequence has no gaps, so an
        excised entry is detectable."""
        _, artifact = _ingest(session, store, case, investigator)
        verify_and_activate(session, store, artifact, verifier)
        retract_artifact(session, artifact, investigator, reason="test retraction")

        seqs = [s for s, _, _, _ in _audit_actions(session, case.id)]
        assert seqs == list(range(1, len(seqs) + 1))

    def test_case_requires_legal_authority(self, session, investigator):
        """ONT-CAS-001 → Article VI: no Case without a recorded legal
        authority basis."""
        from argus.ingestion.service import create_case

        with pytest.raises(ConstitutionalViolation):
            create_case(
                session, title="No authority", legal_authority_basis="  ",
                responsible=investigator,
            )


@pytest.mark.postgres
class TestDatabaseLayerEnforcement:
    """Invariant Matrix rows whose enforcing mechanism is PostgreSQL itself
    (grants, controlled functions). These run in CI against the Compose
    stack once the Alembic migrations land; SQLite proves nothing here
    (ADR-0006)."""

    def test_artifact_hash_immutable_at_db(self):
        pytest.skip("Requires PostgreSQL + migrations (next Slice 1 commit).")

    def test_audit_entry_immutable_for_all_roles(self):
        pytest.skip("Requires PostgreSQL + migrations (next Slice 1 commit).")

    def test_mutation_and_audit_atomic_rollback(self):
        pytest.skip("Requires PostgreSQL + migrations (next Slice 1 commit).")
