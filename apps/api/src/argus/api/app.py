"""The ARGUS transport boundary (Slices 1F-A / 1F-B).

1F-A proved a constitutional action binds to an authenticated principal and
refuses caller-controlled identity. 1F-B adds authority and visibility: a
principal may do or see only what its resource-scoped capabilities permit —
and that authority never changes what a record means (ONT-PRN-029), while
protected access is explicit, least-privileged, and audited before
disclosure (ONT-PRN-030).

The request flow stays visibly layered:

    HTTP request
      -> authentication dependency  (who authenticated?)
      -> AuthenticatedPrincipal
      -> AuthorityProvider.grants_for (what grants exist? facts only)
      -> authorize(...) / visibility projection  (what do they permit?)
      -> reject_identity_input + bind_actor        (who is attributed?)
      -> set_config principal + assert_transaction_principal
      -> application service / projected read
"""

from __future__ import annotations

import base64
import os

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from ..domain import audit
from ..domain.actor_binding import (
    AuthenticatedPrincipal,
    UNAUTHENTICATED,
    bind_actor,
    reject_identity_input,
)
from ..domain.authority import (
    Capability,
    authorize,
    code_for,
    project_artifact_visibility,
)
from ..domain.exceptions import ConstitutionalViolation
from ..domain.models import Case, EvidenceArtifact
from ..ingestion.observations import create_observation
from ..ingestion.service import create_case
from ..reconstruction import reconstruct_case
from .authentication import default_dev_verifier
from .authority_provider import DevAuthorityProvider
from .dependencies import get_session, require_principal
from .principal_context import bind_and_assert


class CreateCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    legal_authority_basis: str


class CreateObservationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locator_id: str
    statement: str
    method_description: str


_UNAUTH_CODES = {UNAUTHENTICATED}


def _status_for(message: str) -> int:
    return 401 if any(code in message for code in _UNAUTH_CODES) else 403


class _ResourceDenied(Exception):
    """Generic resource denial — used when a principal is not entitled to
    know a resource exists (Amendment 2: secrecy is not an existence leak).
    The response is identical whether or not the resource exists."""


def _grants(request: Request, principal: AuthenticatedPrincipal):
    return request.app.state.authority_provider.grants_for(principal.principal_id)


def _enforce(required: Capability, case_id: str, grants) -> None:
    decision = authorize(required, case_id, grants)
    if not decision.allowed:
        raise ConstitutionalViolation(
            "ONT-PRN-029",
            f"not authorized: {code_for(required, decision)}",
        )


def _authorized_case_projection(session: Session, case_id: str, grants) -> dict | None:
    """The 1F-B authorized projection: identical epistemic sections for any
    CASE_READ principal, artifact visibility per capability. Returns None
    when existence may not be disclosed (no CASE_READ, or no such case) —
    the caller issues the generic denial. This is the single input the
    1F-C renderer receives: presentation is downstream of authority."""
    case = session.get(Case, case_id)
    if case is None or not authorize(Capability.CASE_READ, case_id, grants).allowed:
        return None
    doc = reconstruct_case(session, case_id)
    artifacts = []
    for a in sorted(
        session.execute(select(EvidenceArtifact).where(
            EvidenceArtifact.case_id == case_id)).scalars().all(),
        key=lambda x: x.id,
    ):
        sealed = a.status.value == "SEALED"
        vis = project_artifact_visibility(sealed=sealed, case_id=case_id, grants=grants)
        entry = {"id": a.id, "status": a.status.value, "visibility": vis}
        if vis["metadata_visible"]:
            entry["metadata"] = {
                "hash_algorithm": a.hash_algorithm, "hash_digest": a.hash_digest,
                "size_bytes": a.size_bytes, "media_type": a.media_type,
                "acquisition_description": a.acquisition_description,
            }
        artifacts.append(entry)
    return {
        "case": doc["case"],
        "evidence_artifacts": artifacts,
        "observations": doc["observations"],
        "interpretations": doc["interpretations"],
        "unknowns": doc["unknowns"],
        "contradictions": doc["contradictions"],
        "hypotheses": doc["hypotheses"],
        "hypothesis_alternatives": doc["hypothesis_alternatives"],
    }


def create_app(*, verifier=None, session_factory=None, authority_provider=None,
               content_store=None) -> FastAPI:
    app = FastAPI(title="ARGUS", version="1F-B")

    if session_factory is None:
        url = os.environ.get("DATABASE_URL")
        if url is None:
            raise RuntimeError("DATABASE_URL is required to build the ARGUS app")
        engine = create_engine(url, pool_pre_ping=True)
        session_factory = sessionmaker(bind=engine, class_=Session)
    app.state.session_factory = session_factory
    app.state.verifier = verifier if verifier is not None else default_dev_verifier()
    app.state.authority_provider = (
        authority_provider if authority_provider is not None else DevAuthorityProvider({})
    )
    app.state.content_store = content_store

    @app.exception_handler(ConstitutionalViolation)
    async def _constitutional_handler(request: Request, exc: ConstitutionalViolation):
        message = str(exc)
        return JSONResponse(
            status_code=_status_for(message),
            content={"ontology_rule": exc.ontology_rule, "detail": message},
        )

    @app.exception_handler(_ResourceDenied)
    async def _resource_denied_handler(request: Request, exc: _ResourceDenied):
        # Identical whether or not the resource exists — no existence leak.
        return JSONResponse(status_code=404, content={"detail": "resource not available"})

    # ---- 1F-A: constitutional command bound to authenticated identity ----

    @app.post("/cases", status_code=201)
    async def post_case(
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        raw = await request.json()
        if isinstance(raw, dict):
            reject_identity_input(raw.keys())
        body = CreateCaseRequest.model_validate(raw)
        actor = bind_actor(principal)
        bind_and_assert(session, principal, actor)
        case = create_case(
            session, title=body.title,
            legal_authority_basis=body.legal_authority_basis, responsible=actor,
        )
        return {"id": case.id, "title": case.title, "status": case.status.value,
                "responsible_actor": case.responsible_actor}

    # ---- 1F-B: authority-aware case view (visibility authority) ----

    @app.get("/cases/{case_id}")
    async def get_case(
        case_id: str,
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        grants = _grants(request, principal)
        projection = _authorized_case_projection(session, case_id, grants)
        if projection is None:
            raise _ResourceDenied()
        return projection

    # ---- 1F-C: the read-only review surface (presentation) ----

    @app.get("/cases/{case_id}/review")
    async def get_case_review(
        case_id: str,
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        from fastapi.responses import HTMLResponse

        from ..presentation.render import render_case_review

        grants = _grants(request, principal)
        # The same generic-denial behavior as 1F-B, applied BEFORE rendering
        # begins: the page adds no existence channel the API lacks.
        projection = _authorized_case_projection(session, case_id, grants)
        if projection is None:
            raise _ResourceDenied()
        # The renderer receives only the authorized projection — no grants,
        # no authorize access (ONT-PRN-031: downstream of authority).
        return HTMLResponse(render_case_review(projection))

    # ---- 1F-B: action authority + resource scope ----

    @app.post("/cases/{case_id}/observations", status_code=201)
    async def post_observation(
        case_id: str,
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        raw = await request.json()
        if isinstance(raw, dict):
            reject_identity_input(raw.keys())
        body = CreateObservationRequest.model_validate(raw)
        grants = _grants(request, principal)
        case = session.get(Case, case_id)
        if case is None or not authorize(Capability.CASE_READ, case_id, grants).allowed:
            raise _ResourceDenied()
        # Action authority, resource-scoped: a Case-A grant never works here
        # unless it is scoped to this Case. Denied -> nothing is written.
        _enforce(Capability.OBSERVATION_CREATE, case_id, grants)
        actor = bind_actor(principal)
        bind_and_assert(session, principal, actor)
        obs = create_observation(
            session, case=case, locator_ids=[body.locator_id],
            statement=body.statement, method_description=body.method_description,
            actor=actor,
        )
        return {"id": obs.id, "citation": obs.citation}

    # ---- 1F-B: protected content access (audit before disclosure) ----

    @app.get("/artifacts/{artifact_id}/content")
    async def get_content(
        artifact_id: str,
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        grants = _grants(request, principal)
        artifact = session.get(EvidenceArtifact, artifact_id)
        # Stage 1 — existence: generic denial (no leak) without CASE_READ.
        if artifact is None or not authorize(
            Capability.CASE_READ, artifact.case_id, grants
        ).allowed:
            raise _ResourceDenied()
        # Stage 2 — content: SEALED content requires SEALED_CONTENT_READ.
        # Existence is known here, so withholding is explicit, not absence.
        sealed = artifact.status.value == "SEALED"
        if sealed:
            _enforce(Capability.SEALED_CONTENT_READ, artifact.case_id, grants)
        store = request.app.state.content_store
        actor = bind_actor(principal)
        try:
            data = store.read_permanent(artifact.hash_digest)
        except OSError:
            # Record the failed authorized attempt; disclose nothing.
            bind_and_assert(session, principal, actor)
            audit.emit(session, case_id=artifact.case_id, actor=actor,
                       action="sealed-content-access-failed",
                       target_type="EvidenceArtifact", target_id=artifact.id,
                       detail={"reason": "content-unreadable"})
            session.commit()
            raise _ResourceDenied()
        # Audit BEFORE disclosure: content is returned only once the access
        # attribution is durably recorded (Amendment 3). If the audit raises,
        # this returns before disclosure — content stays withheld.
        if sealed:
            bind_and_assert(session, principal, actor)
            audit.emit(session, case_id=artifact.case_id, actor=actor,
                       action="sealed-content-accessed",
                       target_type="EvidenceArtifact", target_id=artifact.id,
                       detail={"size_bytes": len(data)})
            session.commit()
        return {"artifact_id": artifact.id,
                "content_base64": base64.b64encode(data).decode("ascii"),
                "size_bytes": len(data)}

    # ---- 1F-B: sealed verify (integrity result only, never content) ----

    @app.post("/artifacts/{artifact_id}/verify")
    async def post_verify(
        artifact_id: str,
        request: Request,
        principal: AuthenticatedPrincipal = Depends(require_principal),
        session: Session = Depends(get_session),
    ):
        import hashlib

        from ..ingestion.hashing import ALGORITHM
        from ..ingestion.store import expected_storage_ref
        from ..reconciliation_scan import classify_storage_integrity

        grants = _grants(request, principal)
        artifact = session.get(EvidenceArtifact, artifact_id)
        if artifact is None or not authorize(
            Capability.CASE_READ, artifact.case_id, grants
        ).allowed:
            raise _ResourceDenied()
        # SEALED_VERIFY authorizes integrity verification that internally
        # reads bytes; the principal receives the RESULT only, never bytes.
        # This is the elevated path the 1E default scan deferred — it opens
        # sealed content because authority permits it here.
        _enforce(Capability.SEALED_VERIFY, artifact.case_id, grants)
        store = request.app.state.content_store
        digest = artifact.hash_digest
        supported = artifact.hash_algorithm == ALGORITHM
        present = store.permanent_exists(digest)
        readable = digest_match = size_match = location_match = False
        if present:
            try:
                data = store.read_permanent(digest)
            except OSError:
                readable = False
            else:
                readable = True
                digest_match = hashlib.sha256(data).hexdigest() == digest
                size_match = len(data) == artifact.size_bytes
                location_match = artifact.storage_ref == expected_storage_ref(
                    artifact.hash_algorithm, digest)
        condition = classify_storage_integrity(
            verification_performed=supported, present=present, readable=readable,
            digest_match=digest_match, size_match=size_match,
            location_match=location_match)
        # Integrity, never authenticity (ONT-PRN-026 survives elevation).
        return {"artifact_id": artifact.id, "integrity_status": condition}

    return app
