"""Atomic audit emission (ONT-AUD-001, D-AUD).

An AuditEntry is added to the same session — therefore the same transaction —
as the mutation it witnesses. If the transaction rolls back, both the mutation
and its audit entry vanish together; an unaudited material mutation and an
audit entry for a non-occurred mutation are equally impossible.

Under concurrent writers on PostgreSQL, the unique (case_id, seq) constraint
makes sequence collisions fail loudly for retry; gapless per-case ordering is
verified by the constitutional test suite.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .actors import Actor
from .models import AuditEntry, AuditOutcome


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
    next_seq = (
        session.execute(
            select(func.max(AuditEntry.seq)).where(AuditEntry.case_id == case_id)
        ).scalar()
        or 0
    ) + 1
    entry = AuditEntry(
        case_id=case_id,
        seq=next_seq,
        actor_class=actor.actor_class.value,
        actor_id=actor.actor_id,
        ai_model_version=actor.ai_model_version,
        action=action,
        target_type=target_type,
        target_id=target_id,
        outcome=outcome,
        detail=detail,
    )
    session.add(entry)
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

    Callers invoke this in a fresh transaction after the rejected operation's
    transaction has rolled back — the rejection is a fact in its own right.
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
