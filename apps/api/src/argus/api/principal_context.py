"""Transaction-scoped principal context (Slice 1F-A; ONT-PRN-028, Amendment 4).

Binds the authenticated principal to the current database transaction via
set_config(..., is_local => true) — the parameterizable, injection-safe
form of SET LOCAL. Transaction scope is mandatory: a persistent GUC on a
pooled connection would leak the principal across requests.

The primary guard (argus_private.assert_transaction_principal) is then
invoked at the beginning of the constitutional mutation path — before any
mutation — with audit-append consistency checking remaining only as
defense-in-depth (never the first line).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..domain.actors import Actor
from ..domain.audit import _is_postgres

_SET_LOCAL = text(
    "SELECT set_config('argus.actor_principal', :pid, true), "
    "set_config('argus.actor_principal_class', :pclass, true), "
    "set_config('argus.human_attribution', :hattr, true)"
)
_ASSERT = text(
    "SELECT argus_private.assert_transaction_principal(:actor_class, :actor_id, :hattr)"
)


def bind_and_assert(session: Session, principal, actor: Actor) -> None:
    """Bind the principal to the transaction and assert the derived actor
    is consistent with it, at mutation entry. No-op on the SQLite test
    backend (the guard is a PostgreSQL persistence-boundary control; the
    binding rule already enforced identity in Python)."""
    if not _is_postgres(session):
        return
    session.execute(
        _SET_LOCAL,
        {
            "pid": principal.principal_id,
            "pclass": principal.principal_class.value,
            "hattr": principal.human_attribution or "",
        },
    )
    session.execute(
        _ASSERT,
        {
            "actor_class": actor.actor_class.value,
            "actor_id": actor.actor_id,
            "hattr": actor.human_authority or "",
        },
    )
