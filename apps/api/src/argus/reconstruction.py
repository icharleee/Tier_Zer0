"""Case Reconstruction — the Python rendering (Slice 3A, AGC Session 014).

A Case Reconstruction is a transient, read-only projection of the
constitutional state of one Case at the time of evaluation. It has no
epistemic standing independent of the records from which it is derived:
it is the system's reconstruction of its records — not of reality
(ONT-PRN-001). Not a first-class object: no identity, no citation, no
lifecycle, no audit history.

Pure read: nothing here mutates, emits, transitions, or repairs; no
evaluation-time value enters the canonical payload. Composition may
reveal relationships already present in the constitutional graph; it may
never create a meaning that no constitutional record already carries.

The document shape, ordering, visibility envelope, and manifest are
normative in docs/domain/CASE_RECONSTRUCTION.md 0.1.0; PostgreSQL carries
an independent rendering (argus_private.case_reconstruction). H8 compares
them through semantic structural equality, strengthened by canonical byte
identity under the chain_version=1 serialization rules.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .domain import canonical
from .domain.chain import verify_case_chain
from .domain.exceptions import ConstitutionalViolation
from .domain.models import (
    AuditEntry,
    Case,
    CaseAuthority,
    Contradiction,
    ContradictionDisposition,
    ContradictionLink,
    ContradictionMember,
    EvidenceArtifact,
    Hypothesis,
    HypothesisAlternative,
    HypothesisGrounding,
    Interpretation,
    InterpretationGrounding,
    Observation,
    ObservationGrounding,
    SourceLocator,
    Unknown,
    UnknownLink,
    UnknownResolution,
)
from .ingestion.contradictions import contradiction_health, contradiction_status
from .ingestion.hypotheses import (
    contradiction_boundary_state,
    current_alternative_state,
    hypothesis_health,
    unknown_boundary_state,
)
from .ingestion.interpretations import grounding_health
from .ingestion.observations import observation_is_grounded
from .ingestion.unknowns import unknown_status

RECONSTRUCTION_SCHEMA_VERSION = "0.1.0"
ONTOLOGY_VERSION = "1.15.0"
UNKNOWN_CASE = "ONT-CAS-001:unknown-case"


def _ts(dt: datetime | None) -> str | None:
    return None if dt is None else canonical.format_timestamp(dt)


def _retraction(record, *, superseded_by: bool = False) -> dict | None:
    if record.retracted_at is None:
        return None
    r = {"retracted_at": _ts(record.retracted_at), "reason": record.retraction_reason}
    if superseded_by:
        r["superseded_by"] = record.superseded_by
    return r


def _artifact(a: EvidenceArtifact) -> dict:
    sealed = a.status.value == "SEALED"
    doc = {
        "id": a.id,
        "ontology_class": "ONT-EVA-001",
        "status": a.status.value,
        "created_at": _ts(a.created_at),
        "retraction": _retraction(a, superseded_by=True),
        # Absence must never be ambiguous (Session 014, Amendment 5): a
        # SEALED artifact is existence-plus-status with its withholding
        # declared, never silently omitted. storage_ref is excluded by
        # design at every visibility (operational pointer).
        "visibility": {
            "state": "SEALED" if sealed else "FULL",
            "content_visible": not sealed,
            "provenance_detail_visible": not sealed,
            "withholding_basis": "AUTHORITY_REQUIRED" if sealed else None,
        },
    }
    if not sealed:
        doc.update(
            hash_algorithm=a.hash_algorithm,
            hash_digest=a.hash_digest,
            size_bytes=a.size_bytes,
            media_type=a.media_type,
            acquisition_description=a.acquisition_description,
            ingested_by_class=a.ingested_by_class,
            ingested_by_id=a.ingested_by_id,
            human_authority=a.human_authority,
        )
    return doc


def reconstruct_case(session: Session, case_id: str) -> dict:
    """The canonical payload (`document`) only — no evaluation-time values.
    Refuses unknown cases; an empty case reconstructs validly."""
    case = session.get(Case, case_id)
    if case is None:
        raise ConstitutionalViolation(
            "ONT-CAS-001", f"Reconstruction inadmissible: {UNKNOWN_CASE}"
        )

    def rows(model):
        return session.execute(
            select(model).where(model.case_id == case_id)
        ).scalars().all()

    authorities = sorted(rows(CaseAuthority), key=lambda a: (_ts(a.created_at), a.id))
    artifacts = sorted(rows(EvidenceArtifact), key=lambda a: a.id)
    locators = sorted(rows(SourceLocator), key=lambda l: l.id)
    observations = sorted(rows(Observation), key=lambda o: o.citation)
    interpretations = sorted(rows(Interpretation), key=lambda i: i.citation)
    unknowns = sorted(rows(Unknown), key=lambda u: u.citation)
    contradictions = sorted(rows(Contradiction), key=lambda c: c.citation)
    hypotheses = sorted(rows(Hypothesis), key=lambda h: h.citation)

    def obs_doc(o: Observation) -> dict:
        groundings = sorted(
            session.execute(select(ObservationGrounding).where(
                ObservationGrounding.observation_id == o.id)).scalars().all(),
            key=lambda g: g.locator_id,
        )
        return {
            "id": o.id, "citation": o.citation, "ontology_class": "ONT-OBS-001",
            "statement": o.statement, "method_description": o.method_description,
            "event_time_start": _ts(o.event_time_start),
            "event_time_end": _ts(o.event_time_end),
            "created_by_class": o.created_by_class, "created_by_id": o.created_by_id,
            "created_at": _ts(o.created_at), "retraction": _retraction(o),
            "groundings": [
                {"id": g.id, "locator_id": g.locator_id, "created_at": _ts(g.created_at)}
                for g in groundings
            ],
            "derived": {"is_grounded": observation_is_grounded(session, o)},
        }

    def int_doc(i: Interpretation) -> dict:
        groundings = sorted(
            session.execute(select(InterpretationGrounding).where(
                InterpretationGrounding.interpretation_id == i.id)).scalars().all(),
            key=lambda g: g.observation_id,
        )
        return {
            "id": i.id, "citation": i.citation, "ontology_class": "ONT-INT-001",
            "meaning_statement": i.meaning_statement,
            "reasoning_description": i.reasoning_description,
            "uncertainty_status": i.uncertainty_status.value,
            "uncertainty_explanation": i.uncertainty_explanation,
            "created_by_class": i.created_by_class, "created_by_id": i.created_by_id,
            "created_at": _ts(i.created_at), "retraction": _retraction(i),
            "groundings": [
                {"id": g.id, "observation_id": g.observation_id,
                 "statement_fingerprint": g.statement_fingerprint,
                 "grounding_role": g.grounding_role.value, "linked_at": _ts(g.linked_at)}
                for g in groundings
            ],
            "derived": {"grounding_health": grounding_health(session, i)},
        }

    def unk_doc(u: Unknown) -> dict:
        links = sorted(
            session.execute(select(UnknownLink).where(
                UnknownLink.unknown_id == u.id)).scalars().all(),
            key=lambda l: (l.target_type, l.target_id),
        )
        res = session.execute(select(UnknownResolution).where(
            UnknownResolution.unknown_id == u.id)).scalars().first()
        return {
            "id": u.id, "citation": u.citation, "ontology_class": "ONT-UNK-001",
            "question": u.question, "impact_statement": u.impact_statement,
            "operational_state": u.operational_state.value,
            "created_by_class": u.created_by_class, "created_by_id": u.created_by_id,
            "created_at": _ts(u.created_at),
            "links": [
                {"id": l.id, "target_type": l.target_type, "target_id": l.target_id,
                 "nature": l.nature, "linked_at": _ts(l.linked_at),
                 "retraction": _retraction(l)}
                for l in links
            ],
            "resolution": None if res is None else {
                "id": res.id, "resolution_type": res.resolution_type.value,
                "rationale": res.rationale, "answering_claims": res.answering_claims,
                "resolved_by": res.resolved_by, "created_at": _ts(res.created_at),
            },
            "derived": {"status": unknown_status(session, u)},
        }

    def con_doc(c: Contradiction) -> dict:
        members = sorted(
            session.execute(select(ContradictionMember).where(
                ContradictionMember.contradiction_id == c.id)).scalars().all(),
            key=lambda m: (m.member_type, m.member_id),
        )
        links = sorted(
            session.execute(select(ContradictionLink).where(
                ContradictionLink.contradiction_id == c.id)).scalars().all(),
            key=lambda l: l.hypothesis_id,
        )
        disp = session.execute(select(ContradictionDisposition).where(
            ContradictionDisposition.contradiction_id == c.id)).scalars().first()
        return {
            "id": c.id, "citation": c.citation, "ontology_class": "ONT-CON-001",
            "description": c.description,
            "contradiction_type": c.contradiction_type.value,
            "scope_definition": c.scope_definition,
            "incompatibility_basis": c.incompatibility_basis,
            "operational_state": c.operational_state.value,
            "created_by_class": c.created_by_class, "created_by_id": c.created_by_id,
            "created_at": _ts(c.created_at),
            "members": [
                {"id": m.id, "member_type": m.member_type, "member_id": m.member_id,
                 "member_fingerprint": m.member_fingerprint,
                 "member_role": m.member_role, "linked_at": _ts(m.linked_at)}
                for m in members
            ],
            "links": [
                {"id": l.id, "hypothesis_id": l.hypothesis_id,
                 "hypothesis_fingerprint": l.hypothesis_fingerprint,
                 "relationship_type": l.relationship_type, "explanation": l.explanation,
                 "linked_by_class": l.linked_by_class, "linked_by_id": l.linked_by_id,
                 "linked_at": _ts(l.linked_at), "retraction": _retraction(l)}
                for l in links
            ],
            "disposition": None if disp is None else {
                "id": disp.id, "outcome": disp.outcome.value,
                "rationale": disp.rationale, "informing_refs": disp.informing_refs,
                "disposed_by": disp.disposed_by, "created_at": _ts(disp.created_at),
            },
            "derived": {
                "health": contradiction_health(session, c),
                "status": contradiction_status(session, c),
            },
        }

    def hyp_doc(h: Hypothesis) -> dict:
        groundings = sorted(
            session.execute(select(HypothesisGrounding).where(
                HypothesisGrounding.hypothesis_id == h.id)).scalars().all(),
            key=lambda g: g.interpretation_id,
        )
        return {
            "id": h.id, "citation": h.citation, "ontology_class": "ONT-HYP-001",
            "explanatory_statement": h.explanatory_statement,
            "reasoning_description": h.reasoning_description,
            "uncertainty_status": h.uncertainty_status.value,
            "uncertainty_explanation": h.uncertainty_explanation,
            "testability_statement": h.testability_statement,
            "challenge_condition": h.challenge_condition,
            # Historical articulation beside current derived state — never
            # merged (ONT-PRN-025).
            "alternative_articulation_at_creation":
                h.alternative_articulation_at_creation.value,
            "alternative_absence_explanation": h.alternative_absence_explanation,
            "no_current_unknowns_explanation": h.no_current_unknowns_explanation,
            "no_current_contradictions_explanation":
                h.no_current_contradictions_explanation,
            "created_by_class": h.created_by_class, "created_by_id": h.created_by_id,
            "created_at": _ts(h.created_at), "retraction": _retraction(h),
            "groundings": [
                {"id": g.id, "interpretation_id": g.interpretation_id,
                 "interpretation_fingerprint": g.interpretation_fingerprint,
                 "grounding_role": g.grounding_role.value, "linked_at": _ts(g.linked_at)}
                for g in groundings
            ],
            "derived": {
                "hypothesis_health": hypothesis_health(session, h),
                "current_alternative_state": current_alternative_state(session, h),
                "unknown_boundary_state": unknown_boundary_state(session, h),
                "contradiction_boundary_state": contradiction_boundary_state(session, h),
            },
        }

    # The symmetric pair lives at top level: nesting it under either
    # Hypothesis would privilege one side structurally (Amendment 3/4).
    # Alternatives are same-case by construction; the a-side filter keeps
    # the query case-scoped (Article VI).
    alternatives = sorted(
        session.execute(select(HypothesisAlternative).where(
            HypothesisAlternative.hypothesis_a_id.in_(
                select(Hypothesis.id).where(Hypothesis.case_id == case_id)
            ))).scalars().all(),
        key=lambda a: (a.hypothesis_a_id, a.hypothesis_b_id),
    )

    entry_count = session.execute(
        select(func.count()).select_from(AuditEntry).where(
            AuditEntry.case_id == case_id)
    ).scalar() or 0
    chain = verify_case_chain(session, case_id)

    return {
        "case": {
            "id": case.id, "title": case.title, "status": case.status.value,
            "responsible_actor": case.responsible_actor,
            "created_at": _ts(case.created_at), "ontology_class": "ONT-CAS-001",
            "authorities": [
                {"id": a.id, "basis": a.basis, "recorded_by": a.recorded_by,
                 "created_at": _ts(a.created_at)}
                for a in authorities
            ],
        },
        "evidence_artifacts": [_artifact(a) for a in artifacts],
        "source_locators": [
            {"id": l.id, "ontology_class": "ONT-SRC-001", "artifact_id": l.artifact_id,
             "scheme": l.scheme, "payload": l.payload,
             "created_by_class": l.created_by_class, "created_by_id": l.created_by_id,
             "created_at": _ts(l.created_at), "retraction": _retraction(l)}
            for l in locators
        ],
        "observations": [obs_doc(o) for o in observations],
        "interpretations": [int_doc(i) for i in interpretations],
        "unknowns": [unk_doc(u) for u in unknowns],
        "contradictions": [con_doc(c) for c in contradictions],
        "hypotheses": [hyp_doc(h) for h in hypotheses],
        "hypothesis_alternatives": [
            {"id": a.id, "hypothesis_a_id": a.hypothesis_a_id,
             "hypothesis_b_id": a.hypothesis_b_id,
             "relation_explanation": a.relation_explanation,
             "linked_by_class": a.linked_by_class, "linked_by_id": a.linked_by_id,
             "linked_at": _ts(a.linked_at)}
            for a in alternatives
        ],
        # CHAIN_VALID means chain integrity only — never that evidence,
        # claims, or the case are verified. CHAIN_INVALID never prevents
        # reconstruction: surface the problem, present the records.
        "audit_chain": {
            "entry_count": int(entry_count),
            "integrity_status": "CHAIN_VALID" if chain.valid else "CHAIN_INVALID",
        },
    }


def canonical_bytes(document: dict) -> str:
    """Level-2 conformance surface: the chain_version=1 canonical JSON
    serialization of the payload (keys sorted by codepoint, minimal
    separators, no floats)."""
    return canonical.canonical_json(document)


def reconstruct_with_meta(session: Session, case_id: str) -> dict:
    """Transport envelope: evaluation circumstances stay outside the
    canonical payload (Amendment 6) — byte comparison covers `document`
    only."""
    document = reconstruct_case(session, case_id)
    return {
        "document": document,
        "meta": {
            "case_id": case_id,
            "generated_at": canonical.format_timestamp(datetime.now(timezone.utc)),
            "reconstruction_schema_version": RECONSTRUCTION_SCHEMA_VERSION,
            "ontology_version": ONTOLOGY_VERSION,
        },
    }
