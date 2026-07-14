"""The ADR-0007 protocol: staging → record → verification → activation.

The constitutional loop of Slice 1 (Constitutional Evidence Activation):

    Upload → STAGED → hash computed → record created (T1)
           → verification → ACTIVE (T2) → Observation-eligible

Ordering principle (ADR-0007 §1): bytes, then record, then activation —
errors fail safe toward "evidence exists but is not yet claimable"
(the permanent maxim of AGC Session 004), never toward claim-without-evidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..domain import audit
from ..domain.actors import Actor, ActorClass, human
from ..domain.exceptions import ConstitutionalViolation
from ..domain.models import (
    ArtifactStatus,
    Case,
    CaseAuditHead,
    CaseAuthority,
    EvidenceArtifact,
)
from ..domain.transitions import activate_artifact, quarantine_artifact
from .hashing import ALGORITHM, compute_digest
from .store import ContentStore


def create_case(
    session: Session, *, title: str, legal_authority_basis: str, responsible: Actor
) -> Case:
    """ONT-CAS-001: a Case requires its legal authority basis at creation
    (Article VI) and a responsible HumanActor."""
    if responsible.actor_class is not ActorClass.HUMAN:
        raise ConstitutionalViolation(
            "ONT-PRN-007", "A Case's responsible actor must be a HumanActor."
        )
    if not legal_authority_basis.strip():
        raise ConstitutionalViolation(
            "ONT-CAS-001", "A Case cannot be created without a legal authority basis."
        )
    case = Case(title=title, responsible_actor=responsible.actor_id)
    session.add(case)
    session.flush()
    session.add(
        CaseAuthority(
            case_id=case.id,
            basis=legal_authority_basis,
            recorded_by=responsible.actor_id,
        )
    )
    # The audit-chain root, at genesis (ADR-0016): created with the Case,
    # advanced only by the append routine.
    session.add(
        CaseAuditHead(case_id=case.id, last_sequence=0, last_event_hash="0" * 64)
    )
    session.flush()
    audit.emit(
        session,
        case_id=case.id,
        actor=responsible,
        action="case-created",
        target_type="Case",
        target_id=case.id,
        detail={"authority_basis": legal_authority_basis},
    )
    session.commit()
    return case


@dataclass(frozen=True)
class StagedUpload:
    """STAGED — pre-constitutional (ADR-0007 §2): bytes exist; nothing else is
    guaranteed. No ontology, no provenance, no claims."""

    session_id: str
    algorithm: str
    digest: str
    size_bytes: int


def stage_upload(
    store: ContentStore, data: bytes, *, client_declared_digest: str | None = None
) -> StagedUpload:
    """Step 1 — stream bytes to staging, computing the hash of record.

    A client-declared hash is advisory only (ADR-0007 §3): a mismatch is worth
    surfacing to the uploader, but the system-computed digest is the identity.
    """
    session_id = uuid.uuid4().hex
    digest = compute_digest(data)
    store.put_staged(session_id, data)
    staged = StagedUpload(session_id, ALGORITHM, digest, len(data))
    if client_declared_digest is not None and client_declared_digest != digest:
        # Advisory: recorded at T1 in the ingest audit detail; identity is
        # unaffected.
        object.__setattr__(staged, "_client_hash_mismatch", True)  # type: ignore[attr-defined]
    return staged


def create_artifact_record(
    session: Session,
    staged: StagedUpload,
    *,
    case: Case,
    actor: Actor,
    media_type: str,
    acquisition_description: str,
) -> EvidenceArtifact:
    """Step 2 (T1) — one atomic transaction: PENDING_VERIFICATION record plus
    its artifact-ingested AuditEntry (D-AUD)."""
    if actor.actor_class is ActorClass.AI:
        raise ConstitutionalViolation(
            "ONT-EVA-001", "AIWorkflows may not ingest evidence."
        )
    if actor.actor_class is ActorClass.SYSTEM and not actor.human_authority:
        raise ConstitutionalViolation(
            "ONT-CAS-001",
            "A SystemProcess ingesting evidence must attribute its human "
            "authority (Article VI).",
        )
    if not acquisition_description.strip():
        raise ConstitutionalViolation(
            "ONT-PRN-005",
            "No provenance, no claim: an EvidenceArtifact requires a non-empty "
            "acquisition description at ingest.",
        )
    artifact = EvidenceArtifact(
        case_id=case.id,
        status=ArtifactStatus.PENDING_VERIFICATION,
        hash_algorithm=staged.algorithm,
        hash_digest=staged.digest,
        size_bytes=staged.size_bytes,
        media_type=media_type,
        acquisition_description=acquisition_description,
        ingested_by_class=actor.actor_class.value,
        ingested_by_id=actor.actor_id,
        human_authority=actor.human_authority or actor.actor_id,
        storage_ref=f"staging/{staged.session_id}",
    )
    session.add(artifact)
    session.flush()
    audit.emit(
        session,
        case_id=case.id,
        actor=actor,
        action="artifact-ingested",
        target_type="EvidenceArtifact",
        target_id=artifact.id,
        detail={
            "algorithm": staged.algorithm,
            "digest": staged.digest,
            "size_bytes": staged.size_bytes,
            "client_hash_mismatch": getattr(staged, "_client_hash_mismatch", False),
        },
    )
    session.commit()  # T1: record + audit, atomically
    return artifact


def verify_and_activate(
    session: Session,
    store: ContentStore,
    artifact: EvidenceArtifact,
    verifier: Actor,
) -> EvidenceArtifact:
    """Steps 3–5 — idempotent verification, promotion, and activation (T2),
    or quarantine on integrity failure.

    No EvidenceArtifact becomes ACTIVE until its record and its permanently
    stored content have both passed integrity verification (ADR-0007 §6).
    """
    if artifact.status is ArtifactStatus.ACTIVE:
        return artifact  # idempotent re-run after crash (ADR-0007 §4)
    if artifact.status is not ArtifactStatus.PENDING_VERIFICATION:
        raise ConstitutionalViolation(
            "ONT-PRN-012",
            f"Verification applies to PENDING_VERIFICATION artifacts; this one "
            f"is {artifact.status.value}.",
        )

    staging_session = artifact.storage_ref.removeprefix("staging/")
    staged_bytes = store.read_staged(staging_session)
    recomputed = compute_digest(staged_bytes)

    if recomputed != artifact.hash_digest:
        quarantine_ref = store.quarantine_staged(staging_session)
        artifact.storage_ref = quarantine_ref
        quarantine_artifact(
            session,
            artifact,
            verifier,
            reason=f"hash mismatch: recorded {artifact.hash_digest}, "
            f"recomputed {recomputed}",
        )
        session.commit()  # quarantine transition + audit, atomically
        return artifact

    permanent_ref = store.promote_staged(staging_session, artifact.hash_digest)
    readback = compute_digest(store.read_permanent(artifact.hash_digest))
    if readback != artifact.hash_digest:
        quarantine_ref = store.quarantine_staged(staging_session)
        artifact.storage_ref = quarantine_ref
        quarantine_artifact(
            session, artifact, verifier, reason="permanent-copy read-back mismatch"
        )
        session.commit()
        return artifact

    artifact.storage_ref = permanent_ref
    activate_artifact(session, artifact, verifier, verified_digest=readback)
    session.commit()  # T2: activation + audit, atomically
    store.release_staged(staging_session)  # staging is pre-constitutional
    return artifact
