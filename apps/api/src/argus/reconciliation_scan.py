"""Storage reconciliation — the Python rendering (Slice 1E, AGC Session 016).

Reconciliation detects, surfaces, and accounts for divergence between
stored representations of constitutional records without deciding which
representation is epistemically authoritative (ONT-PRN-026). The scan is a
pure read: it mutates nothing, transitions nothing, repairs nothing, and
emits no audit events (ONT-PRN-027: detect ≠ decide ≠ mutate — repair sits
behind a later gate).

The split is deliberate and honestly bounded (H9): the PROBE is a single
declared implementation collecting raw observed facts from the
ContentStore; the CLASSIFIER is a pure function from those facts to an
integrity condition, dual-rendered here and in
argus_private.classify_storage_integrity, both derived from
docs/domain/STORAGE_RECONCILIATION.md 0.1.0.

Reconciliation may tell ARGUS that its representations disagree. It may
never tell ARGUS what reality therefore means: agreement is never
authenticity; divergence is never falsity.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain import canonical
from .domain.exceptions import ConstitutionalViolation
from .domain.models import Case, EvidenceArtifact
from .ingestion import hashing
from .ingestion.store import ContentStore, expected_storage_ref

RECONCILIATION_SCHEMA_VERSION = "0.1.0"
UNKNOWN_CASE = "ONT-CAS-001:unknown-case"

# Integrity conditions — closed for Slice 1E; never truth conditions.
MATCHED = "MATCHED"
MISSING = "MISSING"
DIVERGENT = "DIVERGENT"
UNREADABLE = "UNREADABLE"
UNVERIFIED = "UNVERIFIED"

DIGEST_MISMATCH = "DIGEST_MISMATCH"
SIZE_MISMATCH = "SIZE_MISMATCH"
STORAGE_LOCATION_MISMATCH = "STORAGE_LOCATION_MISMATCH"

_CLASSIFIED_STATUSES = frozenset({"ACTIVE", "SEALED", "RETRACTED", "QUARANTINED"})


def classify_storage_integrity(
    *,
    verification_performed: bool,
    present: bool,
    readable: bool,
    digest_match: bool,
    size_match: bool,
    location_match: bool,
) -> str:
    """The canonical classification precedence (normative in
    STORAGE_RECONCILIATION.md §5, never inferred from code):
    UNVERIFIED before MISSING before UNREADABLE before DIVERGENT."""
    if not verification_performed:
        return UNVERIFIED
    if not present:
        return MISSING
    if not readable:
        return UNREADABLE
    if not (digest_match and size_match and location_match):
        return DIVERGENT
    return MATCHED


def storage_divergence_reasons(
    *, digest_match: bool, size_match: bool, location_match: bool
) -> tuple[str, ...]:
    """Diagnostic subconditions, sorted — not new top-level states.
    A matching hash never hides metadata drift."""
    reasons = []
    if not digest_match:
        reasons.append(DIGEST_MISMATCH)
    if not size_match:
        reasons.append(SIZE_MISMATCH)
    if not location_match:
        reasons.append(STORAGE_LOCATION_MISMATCH)
    return tuple(sorted(reasons))


def _probe(store: ContentStore, artifact: EvidenceArtifact) -> dict:
    """The single-implementation prober: raw observed facts only, with
    error normalization — absence and unreadability are observations,
    never escaping exceptions. Sealed content is NEVER opened by the
    default scan: observed.present means storage-level existence
    detectable without content access — a different fact from content
    successfully read."""
    sealed = artifact.status.value == "SEALED"
    supported = artifact.hash_algorithm == hashing.ALGORITHM
    quarantined = artifact.status.value == "QUARANTINED"
    present = store.permanent_exists(artifact.hash_digest)
    verification_performed = supported and not sealed and not quarantined

    observed = {
        "present": present,
        "readable": None,
        "supported_algorithm": None if sealed else supported,
        "recomputed_digest": None,
        "observed_size": None,
    }
    facts = {
        "verification_performed": verification_performed,
        "present": present,
        "readable": False,
        "digest_match": False,
        "size_match": False,
        "location_match": False,
    }
    if verification_performed and present:
        try:
            data = store.read_permanent(artifact.hash_digest)
        except OSError:
            observed["readable"] = False
        else:
            observed["readable"] = True
            recomputed = hashlib.sha256(data).hexdigest()
            observed["recomputed_digest"] = recomputed
            observed["observed_size"] = len(data)
            facts["readable"] = True
            facts["digest_match"] = recomputed == artifact.hash_digest
            facts["size_match"] = len(data) == artifact.size_bytes
    if verification_performed:
        facts["location_match"] = artifact.storage_ref == expected_storage_ref(
            artifact.hash_algorithm, artifact.hash_digest
        )
    return {"observed": observed, "facts": facts}


def reconcile_case_storage(session: Session, store: ContentStore, case_id: str) -> dict:
    """The canonical report — no evaluation-time values (purity: two scans
    over unchanged database state and unchanged content-store state produce
    identical canonical reports)."""
    case = session.get(Case, case_id)
    if case is None:
        raise ConstitutionalViolation(
            "ONT-CAS-001", f"Reconciliation inadmissible: {UNKNOWN_CASE}"
        )

    artifacts = sorted(
        session.execute(select(EvidenceArtifact).where(
            EvidenceArtifact.case_id == case_id)).scalars().all(),
        key=lambda a: a.id,
    )

    results = []
    stalled = []
    counts = {MATCHED: 0, MISSING: 0, DIVERGENT: 0, UNREADABLE: 0, UNVERIFIED: 0}
    for a in artifacts:
        status = a.status.value
        if status not in _CLASSIFIED_STATUSES:
            # Verification process not yet completed ≠ unverified permanent
            # representation (Amendment 3): surfaced, never classified,
            # never auto-transitioned.
            stalled.append({
                "artifact_id": a.id,
                "status": status,
                "staged_since": canonical.format_timestamp(a.created_at),
            })
            continue
        probe = _probe(store, a)
        facts = probe["facts"]
        condition = classify_storage_integrity(**facts)
        reasons = (
            list(storage_divergence_reasons(
                digest_match=facts["digest_match"],
                size_match=facts["size_match"],
                location_match=facts["location_match"],
            ))
            if condition == DIVERGENT else []
        )
        counts[condition] += 1
        sealed = status == "SEALED"
        entry = {
            "artifact_id": a.id,
            "status": status,
            "condition": condition,
            "divergence_reasons": reasons,
            "observed": probe["observed"],
            "visibility": {
                "state": "SEALED" if sealed else "FULL",
                "content_visible": not sealed,
                "verification_performed": facts["verification_performed"],
                "withholding_basis": "AUTHORITY_REQUIRED" if sealed else None,
            },
        }
        if not sealed:
            # Withheld for SEALED entries: digest-bearing details would
            # reveal the content-addressed identity. The withholding is
            # declared by the envelope, never silent.
            entry["recorded"] = {
                "hash_algorithm": a.hash_algorithm,
                "hash_digest": a.hash_digest,
                "size_bytes": a.size_bytes,
                "recorded_storage_ref": a.storage_ref,
                "expected_storage_ref": expected_storage_ref(
                    a.hash_algorithm, a.hash_digest),
            }
        else:
            entry["observed"] = {"present": probe["observed"]["present"],
                                 "readable": None, "supported_algorithm": None,
                                 "recomputed_digest": None, "observed_size": None}
        results.append(entry)

    return {
        "results": results,
        "stalled_verification": stalled,
        # Operational counts summarize scan outcomes only and carry no
        # evidentiary, epistemic, or prioritization meaning.
        "operational_summary": {
            "matched_count": counts[MATCHED],
            "missing_count": counts[MISSING],
            "divergent_count": counts[DIVERGENT],
            "unreadable_count": counts[UNREADABLE],
            "unverified_count": counts[UNVERIFIED],
        },
    }


def canonical_report_bytes(report: dict) -> str:
    return canonical.canonical_json(report)


def reconcile_with_meta(session: Session, store: ContentStore, case_id: str) -> dict:
    """Runtime metadata stays outside the canonical comparison payload
    (Amendment 4): the report represents observed integrity state, not
    incidental properties of the scan invocation."""
    report = reconcile_case_storage(session, store, case_id)
    return {
        "report": report,
        "meta": {
            "case_id": case_id,
            "generated_at": canonical.format_timestamp(datetime.now(timezone.utc)),
            "backend_type": type(store).__name__,
            "reconciliation_schema_version": RECONCILIATION_SCHEMA_VERSION,
        },
    }
