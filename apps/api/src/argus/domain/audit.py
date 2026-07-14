"""Atomic, hash-chained audit emission (ONT-AUD-001, D-AUD, ADR-0016).

An AuditEntry is created in the same transaction as the mutation it
witnesses. On PostgreSQL, emission goes through the SECURITY DEFINER
function argus_private.append_audit_event — the only insert path the
application role has — which owns sequence allocation (head row locked FOR
UPDATE), canonical serialization, and hash computation.

On the test-only SQLite path, this module performs the same chain_version=1
computation in Python (argus.domain.canonical); a PostgreSQL-gated parity
test proves the two renderings agree. This divergence exists solely so the
application-layer constitutional suite can run without a database server.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from . import canonical
from .actors import Actor
from .models import AuditEntry, AuditOutcome, CaseAuditHead


def _is_postgres(session: Session) -> bool:
    bind = session.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


_APPEND_SQL = text(
    "SELECT argus_private.append_audit_event("
    ":entry_id, :case_id, :actor_class, :actor_id, :ai_model_version, "
    ":action, :target_type, :target_id, :outcome, "
    "CAST(:detail AS jsonb))"
)


def emit(
    session: Session,
    *,
    case_id: str,
    actor: Actor,
    action: str,
    target_type: str,
    target_id: str,
    outcome: AuditOutcome = AuditOutcome.SUCCEEDED,
    detail: dict | None = None,
) -> AuditEntry:
    entry_id = uuid.uuid4().hex

    if _is_postgres(session):
        import json

        session.execute(
            _APPEND_SQL,
            {
                "entry_id": entry_id,
                "case_id": case_id,
                "actor_class": actor.actor_class.value,
                "actor_id": actor.actor_id,
                "ai_model_version": actor.ai_model_version,
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                "outcome": outcome.value,
                "detail": None if detail is None else json.dumps(detail),
            },
        )
        entry = session.get(AuditEntry, entry_id)
        assert entry is not None
        return entry

    # SQLite path: same specification, computed in Python.
    head = session.get(CaseAuditHead, case_id, with_for_update=True)
    if head is None:
        raise RuntimeError(f"no audit head for case {case_id} (create_case creates it)")

    seq = head.last_sequence + 1
    previous_hash = head.last_event_hash
    occurred_at = datetime.now(timezone.utc)
    canonical_payload = None if detail is None else canonical.canonical_json(detail)
    digest = canonical.event_hash(
        {
            "chain_version": canonical.CHAIN_VERSION,
            "case_id": case_id,
            "seq": seq,
            "target_type": target_type,
            "target_id": target_id,
            "action": action,
            "actor_class": actor.actor_class.value,
            "actor_id": actor.actor_id,
            "ai_model_version": actor.ai_model_version,
            "occurred_at": canonical.format_timestamp(occurred_at),
            "outcome": outcome.value,
            "canonical_payload": canonical_payload,
            "previous_event_hash": previous_hash,
        }
    )
    entry = AuditEntry(
        id=entry_id,
        case_id=case_id,
        seq=seq,
        actor_class=actor.actor_class.value,
        actor_id=actor.actor_id,
        ai_model_version=actor.ai_model_version,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=outcome,
        detail=detail,
        occurred_at=occurred_at,
        chain_version=canonical.CHAIN_VERSION,
        canonical_payload=canonical_payload,
        previous_event_hash=previous_hash,
        event_hash=digest,
    )
    session.add(entry)
    head.last_sequence = seq
    head.last_event_hash = digest
    head.updated_at = occurred_at
    return entry


def record_rejection(
    session: Session,
    *,
    case_id: str,
    actor: Actor,
    action: str,
    target_type: str,
    target_id: str,
    detail: dict | None = None,
) -> AuditEntry:
    """Constitutional rejections are themselves audited (ONT-AUD-001).

    Called in a fresh transaction after the rejected operation rolled back —
    the rejection is a fact in its own right. The rejected transaction itself
    leaves no event (both writes vanish together).
    """
    return emit(
        session,
        case_id=case_id,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=AuditOutcome.REJECTED,
        detail=detail,
    )
