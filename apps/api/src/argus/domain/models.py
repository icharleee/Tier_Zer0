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


class UncertaintyStatus(enum.Enum):
    """The structured uncertainty envelope (Slice 2A, Amendment 2).
    Not a confidence scale; must never imply probability. Deliberately no
    'certain' status — ARGUS preserves the distinction between 'none
    identified' and 'none exists' (Article IX)."""

    ACKNOWLEDGED = "ACKNOWLEDGED"
    MATERIAL = "MATERIAL"
    LIMITING = "LIMITING"
    UNRESOLVED = "UNRESOLVED"


class GroundingRole(enum.Enum):
    """How an Interpretation relies on an Observation (Amendment 3). No
    CONTRADICTING while Contradiction remains out of scope — a limiting
    observation is not a formal contradiction."""

    SUPPORTING = "SUPPORTING"
    LIMITING = "LIMITING"
    CONTEXTUAL = "CONTEXTUAL"


class Interpretation(Base):
    """ONT-INT-001 — a derived meaning inferred from grounded Observations.

    A valid Interpretation means only: this human-authored meaning is
    constitutionally admissible and traceable. NOT correct, preferred,
    complete, likely, accepted, or endorsed. No epistemic-ranking surface
    exists on this table (Article IV; contamination registry); citation
    order is technical, non-evidentiary ordering only.
    """

    __tablename__ = "interpretations"
    __table_args__ = (UniqueConstraint("case_id", "citation", name="uq_int_citation"),)

    ONTOLOGY_CLASS = "ONT-INT-001"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    citation: Mapped[str] = mapped_column(String(16))  # INT-000001, per case
    meaning_statement: Mapped[str] = mapped_column(Text)
    reasoning_description: Mapped[str] = mapped_column(Text)
    uncertainty_status: Mapped[UncertaintyStatus] = mapped_column(
        SAEnum(UncertaintyStatus, native_enum=False)
    )
    uncertainty_explanation: Mapped[str] = mapped_column(Text)
    created_by_class: Mapped[str] = mapped_column(String(16))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class InterpretationGrounding(Base):
    """The grounding snapshot (Amendment 3): exactly what the Interpretation
    relied upon at creation — observation id plus statement fingerprint
    (observations are immutable, so id + sha256 is the revision), role, and
    link time. Content-immutable; survives every retraction so historical
    reasoning stays inspectable."""

    __tablename__ = "interpretation_groundings"
    __table_args__ = (
        UniqueConstraint("interpretation_id", "observation_id", name="uq_int_grounding"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    interpretation_id: Mapped[str] = mapped_column(
        ForeignKey("interpretations.id"), nullable=False
    )
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("observations.id"), nullable=False
    )
    statement_fingerprint: Mapped[str] = mapped_column(String(64))
    grounding_role: Mapped[GroundingRole] = mapped_column(
        SAEnum(GroundingRole, native_enum=False)
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UnknownOperationalState(enum.Enum):
    """Operational, not epistemic (AGC Session 008, Amendment 1):
    UNDER_REVIEW records only that a Steward is actively evaluating the
    Unknown — it carries no conclusion."""

    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"


class ResolutionType(enum.Enum):
    ANSWERED = "ANSWERED"
    PARTIALLY_ANSWERED = "PARTIALLY_ANSWERED"
    UNRESOLVABLE = "UNRESOLVABLE"
    WITHDRAWN = "WITHDRAWN"


class Unknown(Base):
    """ONT-UNK-001 / ONT-PRN-020 — the boundary of current knowledge, never a
    placeholder for future assumptions. Says exactly one thing: this question
    currently has no constitutionally admissible answer. Epistemic
    disposition is DERIVED from the UnknownResolution record; only the
    operational state lives here."""

    __tablename__ = "unknowns"
    __table_args__ = (UniqueConstraint("case_id", "citation", name="uq_unk_citation"),)

    ONTOLOGY_CLASS = "ONT-UNK-001"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    citation: Mapped[str] = mapped_column(String(16))  # UNK-000001, per case
    question: Mapped[str] = mapped_column(Text)
    impact_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    operational_state: Mapped[UnknownOperationalState] = mapped_column(
        SAEnum(UnknownOperationalState, native_enum=False),
        default=UnknownOperationalState.OPEN,
    )
    created_by_class: Mapped[str] = mapped_column(String(16))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UnknownLink(Base):
    """The validity-boundary family (ONT-PRN-021): what an Unknown bounds.
    Never grounds — a boundary can never become support."""

    __tablename__ = "unknown_links"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    unknown_id: Mapped[str] = mapped_column(ForeignKey("unknowns.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(32))
    nature: Mapped[str] = mapped_column(Text)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class UnknownResolution(Base):
    """ONT-UNR-001 — how knowing resumed. Human-only, content-immutable,
    terminal; (PARTIALLY_)ANSWERED requires claim references — an answer
    without evidence is not an answer (Article I). Resolving alters NO
    linked record: knowledge changes, the system does not."""

    __tablename__ = "unknown_resolutions"
    __table_args__ = (UniqueConstraint("unknown_id", name="uq_unk_resolution"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    unknown_id: Mapped[str] = mapped_column(ForeignKey("unknowns.id"), nullable=False)
    resolution_type: Mapped[ResolutionType] = mapped_column(
        SAEnum(ResolutionType, native_enum=False)
    )
    rationale: Mapped[str] = mapped_column(Text)
    answering_claims: Mapped[list | None] = mapped_column(JSON, nullable=True)
    resolved_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContradictionType(enum.Enum):
    TEMPORAL = "TEMPORAL"
    SPATIAL = "SPATIAL"
    IDENTITY = "IDENTITY"
    CAUSAL = "CAUSAL"
    DESCRIPTIVE = "DESCRIPTIVE"
    NUMERIC = "NUMERIC"
    PROCEDURAL = "PROCEDURAL"
    PROVENANCE = "PROVENANCE"
    CUSTODY = "CUSTODY"
    LOGICAL = "LOGICAL"


class DispositionOutcome(enum.Enum):
    """ADR-0027: no outcome exists, or may ever be added, that implies a
    member was proven correct."""

    EXPLAINED = "EXPLAINED"
    NO_LONGER_APPLICABLE = "NO_LONGER_APPLICABLE"
    WITHDRAWN = "WITHDRAWN"
    UNRESOLVED = "UNRESOLVED"
    SUPERSEDED = "SUPERSEDED"


class Contradiction(Base):
    """ONT-CON-001 — a formally scoped joint incompatibility: these
    admissible claims cannot all fit the same reality under the stated
    scope. It never decides which claim reality favors. Admissible — not
    necessarily true."""

    __tablename__ = "contradictions"
    __table_args__ = (UniqueConstraint("case_id", "citation", name="uq_con_citation"),)

    ONTOLOGY_CLASS = "ONT-CON-001"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    citation: Mapped[str] = mapped_column(String(16))  # CON-000001, per case
    description: Mapped[str] = mapped_column(Text)
    contradiction_type: Mapped[ContradictionType] = mapped_column(
        SAEnum(ContradictionType, native_enum=False)
    )
    scope_definition: Mapped[str] = mapped_column(Text)
    incompatibility_basis: Mapped[str] = mapped_column(Text)
    operational_state: Mapped[UnknownOperationalState] = mapped_column(
        SAEnum(UnknownOperationalState, native_enum=False),
        default=UnknownOperationalState.OPEN,
    )
    created_by_class: Mapped[str] = mapped_column(String(16))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContradictionMember(Base):
    """ONT-CNM-001 — an INCOMPATIBLE_CLAIM's part in a conflict, with the
    recognition-time fingerprint proving which version was judged
    incompatible. Content-immutable; survives every retraction and
    disposition. Directional roles are prohibited permanently."""

    __tablename__ = "contradiction_members"
    __table_args__ = (
        UniqueConstraint("contradiction_id", "member_id", name="uq_con_member"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    contradiction_id: Mapped[str] = mapped_column(
        ForeignKey("contradictions.id"), nullable=False
    )
    member_type: Mapped[str] = mapped_column(String(32))
    member_id: Mapped[str] = mapped_column(String(32))
    member_fingerprint: Mapped[str] = mapped_column(String(64))
    member_role: Mapped[str] = mapped_column(String(24), default="INCOMPATIBLE_CLAIM")
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContradictionDisposition(Base):
    """ONT-CDP-001 (ADR-0027) — the human record of how a conflict was
    disposed, never of which claim reality favors. Human-only,
    content-immutable, terminal; alters no member."""

    __tablename__ = "contradiction_dispositions"
    __table_args__ = (
        UniqueConstraint("contradiction_id", name="uq_con_disposition"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    contradiction_id: Mapped[str] = mapped_column(
        ForeignKey("contradictions.id"), nullable=False
    )
    outcome: Mapped[DispositionOutcome] = mapped_column(
        SAEnum(DispositionOutcome, native_enum=False)
    )
    rationale: Mapped[str] = mapped_column(Text)
    informing_refs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    disposed_by: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HypothesisGroundingRole(enum.Enum):
    """How a Hypothesis relies on an Interpretation (Session 012, Amendment 5).
    Only DERIVED_FROM satisfies the existence minimum — a Hypothesis
    containing only contextual links is inadmissible."""

    DERIVED_FROM = "DERIVED_FROM"
    CONTEXTUALIZED_BY = "CONTEXTUALIZED_BY"


class AlternativeArticulation(enum.Enum):
    """The immutable creation-time record of how Article IV was exercised
    (Session 012, Amendment 2). Historical truth of the creation moment —
    the current derived state lives nowhere in storage and never erases
    this articulation."""

    ALTERNATIVE_LINKED_AT_CREATION = "ALTERNATIVE_LINKED_AT_CREATION"
    NONE_CURRENTLY_ARTICULATED_AT_CREATION = "NONE_CURRENTLY_ARTICULATED_AT_CREATION"


class Hypothesis(Base):
    """ONT-HYP-001 / ONT-PRN-023 — a provisional, testable explanatory
    structure; its existence means only that it is admissible for
    examination — not that ARGUS considers it likely, preferred, correct,
    or accepted. The highest epistemic object authorized in the current
    ontology; Understanding and Judgment remain human, outside the schema.

    No probability, confidence, preference, promotion, acceptance, or
    refutation surface exists on this table (Resolution 018; contamination
    registry). hypothesis_health, current_alternative_state, and the
    boundary states are derived, never stored. ARGUS may preserve
    explanations for examination; it may never convert explanation into
    verdict.
    """

    __tablename__ = "hypotheses"
    __table_args__ = (UniqueConstraint("case_id", "citation", name="uq_hyp_citation"),)

    ONTOLOGY_CLASS = "ONT-HYP-001"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), nullable=False)
    citation: Mapped[str] = mapped_column(String(16))  # HYP-000001, per case
    explanatory_statement: Mapped[str] = mapped_column(Text)
    reasoning_description: Mapped[str] = mapped_column(Text)
    uncertainty_status: Mapped[UncertaintyStatus] = mapped_column(
        SAEnum(UncertaintyStatus, native_enum=False)
    )
    uncertainty_explanation: Mapped[str] = mapped_column(Text)
    testability_statement: Mapped[str] = mapped_column(Text)
    challenge_condition: Mapped[str] = mapped_column(Text)
    alternative_articulation_at_creation: Mapped[AlternativeArticulation] = mapped_column(
        SAEnum(AlternativeArticulation, native_enum=False)
    )
    alternative_absence_explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    no_current_unknowns_explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    no_current_contradictions_explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_by_class: Mapped[str] = mapped_column(String(16))
    created_by_id: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class HypothesisGrounding(Base):
    """The grounding snapshot: exactly which Interpretation revision the
    Hypothesis relied upon at creation — interpretation fingerprint v2
    (four fields, 0x1F-separated; see CONSTITUTIONAL_PREDICATES.md), role,
    link time. Content-immutable; survives every retraction. The FK to
    interpretations makes rung-skipping unrepresentable (D-PRN-004)."""

    __tablename__ = "hypothesis_groundings"
    __table_args__ = (
        UniqueConstraint("hypothesis_id", "interpretation_id", name="uq_hyp_grounding"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey("hypotheses.id"), nullable=False
    )
    interpretation_id: Mapped[str] = mapped_column(
        ForeignKey("interpretations.id"), nullable=False
    )
    interpretation_fingerprint: Mapped[str] = mapped_column(String(64))
    grounding_role: Mapped[HypothesisGroundingRole] = mapped_column(
        SAEnum(HypothesisGroundingRole, native_enum=False)
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HypothesisAlternative(Base):
    """The symmetric record that two Hypotheses are articulated alternatives
    (Article IV exercised structurally). Unordered pair normalized by
    identifier (a < b); no direction, weight, or rank exists or may be
    added. Content-immutable; preserved after either side's retraction —
    a retracted alternative never silently vanishes from history."""

    __tablename__ = "hypothesis_alternatives"
    __table_args__ = (
        UniqueConstraint("hypothesis_a_id", "hypothesis_b_id", name="uq_hyp_alternative"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    hypothesis_a_id: Mapped[str] = mapped_column(
        ForeignKey("hypotheses.id"), nullable=False
    )
    hypothesis_b_id: Mapped[str] = mapped_column(
        ForeignKey("hypotheses.id"), nullable=False
    )
    relation_explanation: Mapped[str] = mapped_column(Text)
    linked_by_class: Mapped[str] = mapped_column(String(16))
    linked_by_id: Mapped[str] = mapped_column(String(200))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContradictionLink(Base):
    """The validity-boundary record that a Contradiction challenges a
    Hypothesis (CHALLENGED_BY_CONTRADICTION — the only authorized
    relationship, ever; a Contradiction challenges without killing).
    Boundary-owned, mirroring UnknownLink: the boundary object describes
    the limit it imposes; the Hypothesis never owns its own constraints.
    A disposed Contradiction remains historically linked; link errors
    follow the retract pattern — never silent removal."""

    __tablename__ = "contradiction_links"
    __table_args__ = (
        UniqueConstraint("contradiction_id", "hypothesis_id", name="uq_con_link"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    contradiction_id: Mapped[str] = mapped_column(
        ForeignKey("contradictions.id"), nullable=False
    )
    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey("hypotheses.id"), nullable=False
    )
    hypothesis_fingerprint: Mapped[str] = mapped_column(String(64))
    relationship_type: Mapped[str] = mapped_column(
        String(32), default="CHALLENGED_BY_CONTRADICTION"
    )
    explanation: Mapped[str] = mapped_column(Text)
    linked_by_class: Mapped[str] = mapped_column(String(16))
    linked_by_id: Mapped[str] = mapped_column(String(200))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    retracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retraction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


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
