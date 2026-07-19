"""The ARGUS transport boundary (Slice 1F-A; ONT-PRN-028).

The minimal API surface for the identity experiment (H10) — no authority
routing, no visibility model, no UI (1F-B / 1F-C). Its single architectural
job: prove that a constitutionally meaningful action binds to an
authenticated principal and refuses caller-controlled identity substitution.

The request flow, kept visibly layered:

    HTTP request
      -> authentication dependency  (who authenticated?)
      -> AuthenticatedPrincipal
      -> reject_identity_input       (no identity in the payload)
      -> bind_actor(...)             (who is attributed?)
      -> set_config principal + assert_transaction_principal (persistence guard)
      -> application service          (the constitutional mutation)

The endpoint NEVER constructs Actor(...) from request fields.
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..domain.actor_binding import (
    ACTOR_PRINCIPAL_MISMATCH,
    AuthenticatedPrincipal,
    IDENTITY_INPUT_PROHIBITED,
    UNAUTHENTICATED,
    bind_actor,
    reject_identity_input,
)
from ..domain.exceptions import ConstitutionalViolation
from ..ingestion.service import create_case
from .authentication import default_dev_verifier
from .dependencies import get_session, require_principal
from .principal_context import bind_and_assert


class CreateCaseRequest(BaseModel):
    """A constitutional command schema: no identity field (ONT-PRN-028,
    Amendment 3). extra='forbid' catches any unexpected field; reserved
    identity fields are refused earlier with the canonical code."""

    model_config = ConfigDict(extra="forbid")

    title: str
    legal_authority_basis: str


# Refusal codes that mean "not authenticated" (401) vs. an identity/binding
# refusal of an authenticated caller (403).
_UNAUTH_CODES = {UNAUTHENTICATED}


def _status_for(message: str) -> int:
    return 401 if any(code in message for code in _UNAUTH_CODES) else 403


def create_app(*, verifier=None, session_factory=None) -> FastAPI:
    app = FastAPI(title="ARGUS", version="1F-A")

    if session_factory is None:
        url = os.environ.get("DATABASE_URL")
        if url is None:
            raise RuntimeError("DATABASE_URL is required to build the ARGUS app")
        engine = create_engine(url, pool_pre_ping=True)
        session_factory = sessionmaker(bind=engine, class_=Session)
    app.state.session_factory = session_factory
    app.state.verifier = verifier if verifier is not None else default_dev_verifier()

    @app.exception_handler(ConstitutionalViolation)
    async def _constitutional_handler(request: Request, exc: ConstitutionalViolation):
        message = str(exc)
        return JSONResponse(
            status_code=_status_for(message),
            content={"ontology_rule": exc.ontology_rule, "detail": message},
        )

    @app.post("/cases", status_code=201)
    async def post_case(
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        # Reject any caller-controlled identity field BEFORE parsing — even
        # when it matches the principal (matching assertion is still
        # assertion). Reading the raw body lets us name the field.
        raw = await request.json()
        if isinstance(raw, dict):
            reject_identity_input(raw.keys())
        body = CreateCaseRequest.model_validate(raw)

        # Attribution is DERIVED, never claimed.
        actor = bind_actor(principal)  # HUMAN-required by default

        # Bind the principal to this transaction and assert consistency at
        # mutation entry (the persistence guard), then perform the command.
        bind_and_assert(session, principal, actor)
        case = create_case(
            session,
            title=body.title,
            legal_authority_basis=body.legal_authority_basis,
            responsible=actor,
        )
        return {
            "id": case.id,
            "title": case.title,
            "status": case.status.value,
            "responsible_actor": case.responsible_actor,
        }

    return app
