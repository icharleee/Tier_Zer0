"""Slice 1 domain models: Case, EvidenceArtifact, AuditEntry.

Derived from the Ontology (ONT-CAS-001, ONT-EVA-001, ONT-AUD-001) via the
Derivation Specification; states per Entity Lifecycles 2.0.0 / ADR-0007.
These SQLAlchemy models are a replaceable rendering of the ontology
(ONT-PRN-010) — they implement meaning, they do not define it.

Database-layer enforcement (INSERT-only grants, controlled transition
functions, no UPDATE/DELETE for audit rows) is specified per field group in
docs/domain/INVARIANT_MATRIX.md and lands with the Alembic migrations; the
application layer enforces the same rules above it, never instead of it.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _new_id() -> str:
    """Opaque identity (spec C2): globally unique, never reused, never derived
    from mutable content."""
    return uuid.uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class CaseStatus(enum.Enum):
    OPEN = "OPEN"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class ArtifactStatus(enum.Enum):
    """Constitutional record states (ADR-0007 §2).

    STAGED is deliberately absent: staging is pre-constitutional — bytes exist,
    nothing else is guaranteed — and is tracked by ingestion session outside
    the domain schema.
    """

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    RETRACTED = "RETRACTED"
    SEALED = "SEALED"


class AuditOutcome(enum.Enum):
    SUCCEEDED = "SUCCEEDED"
    REJECTED = "REJECTED"


class Case(Base):
    """ONT-CAS-001 — the bounded investigative world and its legal authority."""

    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, native_enum=False), default=CaseStatus.OPEN
    )
    responsible_actor: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseAuthority(Base):
    """Append-only legal authority records for a Case (Article VI).

    Authority changes are new rows, never edits — the enforcing mechanism at
    the database layer is an INSERT-only grant (Invariant Matrix, Case rows).
    """

    __tablename__ = "case_authorities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    basis: Mapped[str] = mapped_column(Text)
    recorded_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvidenceArtifact(Base):
    """ONT-EVA-001 — a preserved fragment of reality.

    Content-immutable groups (hash, size, media type, ingestion record) have no
    legitimate mutation path at any layer. Status moves only through the named
    transitions in argus.domain.transitions (ONT-PRN-012) — never by writing
    this column directly.
    """

    __tablename__ = "evidence_artifacts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    status: Mapped[ArtifactStatus] = mapped_column(
        SAEnum(ArtifactStatus, native_enum=False),
        default=ArtifactStatus.PENDING_VERIFICATION,
    )

    # Content-immutable identity anchor (ADR-0007 §5: additive hash policy —
    # the original digest is never replaced or recomputed).
    hash_algorithm: Mapped[str] = mapped_column(String(32))
    hash_digest: Mapped[str] = mapped_column(String(128), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    media_type: Mapped[str] = mapped_column(String(255))

    # Provenance at ingest (ONT-PRN-005): required, non-defaultable.
    acquisition_description: Mapped[str] = mapped_column(Text)
    ingested_by_class: Mapped[str] = mapped_column(String(16))
    ingested_by_id: Mapped[str] = mapped_column(String(200))
    human_authority: Mapped[str] = mapped_column(String(200))

    # Controlled-transition operational pointer — never authoritative for
    # identity (ADR-0006 boundary 5).
    storage_ref: Mapped[str] = mapped_column(String(1000))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Retraction pattern (spec C6): nothing disappears (ONT-PRN-006).
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(
        ForeignKey("evidence_artifacts.id"), nullable=True
    )

    @property
    def is_observation_eligible(self) -> bool:
        """Constitutional availability (ADR-0007 §6): evidence may exist and
        still not be claimable. Only ACTIVE artifacts can ground a
        SourceLocator (Slice 2)."""
        return self.status is ArtifactStatus.ACTIVE


class SourceLocator(Base):
    """ONT-SRC-001 — the scope of constitutional support (ONT-PRN-016):
    the smallest evidentiary region required to justify an Observation,
    not merely an address. Immutable after creation (class V: corrections
    are retract-and-replace)."""

    __tablename__ = "source_locators"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_artifacts.id"), nullable=False
    )
    scheme: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
    created_by_class: Mapped[str] = mapped_column(String(16))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Observation(Base):
    """ONT-OBS-001 — the first epistemic object: a source-grounded statement
    of what evidence shows. Perception only; this table deliberately has no
    meaning, inference, ranking, or confidence fields — meaning enters the
    system at Interpretation and nowhere earlier (the one-rung rule,
    ONT-PRN-004)."""

    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("case_id", "citation", name="uq_obs_citation"),)

    # Ontological class — derived, never stored (Resolution 005 pattern);
    # citations pair it with the operational identity below (ADR-0020 §5).
    ONTOLOGY_CLASS = "ONT-OBS-001"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    citation: Mapped[str] = mapped_column(String(16))  # OBS-000001, per case
    statement: Mapped[str] = mapped_column(Text)
    method_description: Mapped[str] = mapped_column(Text)
    event_time_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    event_time_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_class: Mapped[str] = mapped_column(String(16))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ObservationGrounding(Base):
    """The junction binding an Observation to the SourceLocators that scope
    its constitutional support (≥ 1; heterogeneous evidence ready).
    Content-immutable rows."""

    __tablename__ = "observation_groundings"
    __table_args__ = (
        UniqueConstraint("observation_id", "locator_id", name="uq_grounding"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("observations.id"), nullable=False
    )
    locator_id: Mapped[str] = mapped_column(
        ForeignKey("source_locators.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseAuditHead(Base):
    """The per-case audit chain root (ADR-0016): explicit aggregate for
    sequence allocation and current head hash. Locked FOR UPDATE first in the
    global lock order; advanced only by the append routine."""

    __tablename__ = "case_audit_heads"

    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), primary_key=True)
    last_sequence: Mapped[int] = mapped_column(Integer, default=0)
    last_event_hash: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditEntry(Base):
    """ONT-AUD-001 — the witnessed history of a material act.

    Append-only and hash-chained (ADR-0016): the application role and ordinary
    operational roles cannot update or delete entries; privileged owners
    remain inside the declared trust boundary, and unauthorized privileged
    modifications are DETECTED through chain verification, not prevented.
    Corrections are compensating entries. Per-case ordering is gapless and
    monotonic, rooted in CaseAuditHead.
    """

    __tablename__ = "audit_entries"
    __table_args__ = (UniqueConstraint("case_id", "seq", name="uq_audit_case_seq"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)

    actor_class: Mapped[str] = mapped_column(String(16))
    actor_id: Mapped[str] = mapped_column(String(200))
    ai_model_version: Mapped[str | None] = mapped_column(String(200), nullable=True)

    action: Mapped[str] = mapped_column(String(100))
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(32))
    outcome: Mapped[AuditOutcome] = mapped_column(
        SAEnum(AuditOutcome, native_enum=False), default=AuditOutcome.SUCCEEDED
    )
    # Human/queryable representation (ADR-0016 Amendment 4).
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Hash-chain fields (ADR-0016): canonical_payload is the immutable exact
    # text hashed into the chain, derived from `detail` exactly once at
    # insertion by the append routine. The verifier hashes these stored
    # bytes; it never re-canonicalizes from jsonb.
    chain_version: Mapped[int] = mapped_column(Integer)
    canonical_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_event_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64))
