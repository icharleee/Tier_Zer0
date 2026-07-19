"""FastAPI dependencies (Slice 1F-A).

Transport authentication is kept separate from domain attribution: this
module establishes the AuthenticatedPrincipal from the request and yields a
database Session. It never constructs a domain Actor — that is the binding
rule's job (argus.domain.actor_binding), invoked in the endpoint.
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..domain.actor_binding import AuthenticatedPrincipal, refuse, UNAUTHENTICATED


def get_session(request: Request) -> Session:
    factory = request.app.state.session_factory
    session = factory()
    try:
        yield session
    finally:
        session.close()


def require_principal(request: Request) -> AuthenticatedPrincipal:
    """Establish the authenticated principal, or refuse the request. The
    identity comes only from the verified credential — never from the body
    (ONT-PRN-028)."""
    verifier = request.app.state.verifier
    credential = request.headers.get("authorization")
    principal = verifier.verify(credential)
    if principal is None:
        raise refuse(UNAUTHENTICATED, "no authenticated principal for a constitutional command")
    return principal
