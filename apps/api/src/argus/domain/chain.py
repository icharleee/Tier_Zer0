"""Audit-chain verification (ADR-0016; ONT-AUD-001 → Article VIII).

Walks a case's chain checking sequence continuity, genesis, per-row hash
recomputation from STORED fields and STORED canonical text (never
re-canonicalized from jsonb), previous-hash linkage, and head consistency.

The property verified is append-only and tamper-evident WITHIN THE
IMPLEMENTED TRUST BOUNDARY — not tamper-proof (Article IX).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import canonical
from .models import AuditEntry, CaseAuditHead


@dataclass
class ChainVerification:
    case_id: str
    valid: bool
    entries_checked: int
    findings: list[str] = field(default_factory=list)


def verify_case_chain(session: Session, case_id: str) -> ChainVerification:
    findings: list[str] = []
    head = session.get(CaseAuditHead, case_id)
    if head is None:
        return ChainVerification(case_id, False, 0, ["no audit head for case"])

    entries = list(
        session.execute(
            select(AuditEntry)
            .where(AuditEntry.case_id == case_id)
            .order_by(AuditEntry.seq)
        ).scalars()
    )

    previous_hash = canonical.GENESIS_HASH
    for i, entry in enumerate(entries, start=1):
        if entry.seq != i:
            findings.append(f"sequence gap: expected {i}, found {entry.seq}")
        if entry.previous_event_hash != previous_hash:
            findings.append(
                f"seq {entry.seq}: previous-hash linkage broken "
                f"(expected {previous_hash[:12]}…, stored {str(entry.previous_event_hash)[:12]}…)"
            )
        recomputed = canonical.event_hash(
            {
                "chain_version": entry.chain_version,
                "case_id": entry.case_id,
                "seq": entry.seq,
                "target_type": entry.target_type,
                "target_id": entry.target_id,
                "action": entry.action,
                "actor_class": entry.actor_class,
                "actor_id": entry.actor_id,
                "ai_model_version": entry.ai_model_version,
                "occurred_at": canonical.format_timestamp(entry.occurred_at),
                "outcome": entry.outcome.value,
                "canonical_payload": entry.canonical_payload,
                "previous_event_hash": entry.previous_event_hash,
            }
        )
        if recomputed != entry.event_hash:
            findings.append(f"seq {entry.seq}: stored event_hash does not match recomputation")
        previous_hash = entry.event_hash

    if entries:
        if head.last_sequence != entries[-1].seq:
            findings.append(
                f"head last_sequence {head.last_sequence} != final entry seq {entries[-1].seq}"
            )
        if head.last_event_hash != entries[-1].event_hash:
            findings.append("head last_event_hash does not match final entry")
    elif head.last_sequence != 0 or head.last_event_hash != canonical.GENESIS_HASH:
        findings.append("empty chain but head is not at genesis")

    return ChainVerification(case_id, not findings, len(entries), findings)
