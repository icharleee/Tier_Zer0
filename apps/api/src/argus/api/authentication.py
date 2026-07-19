"""Transport authentication (Slice 1F-A; ONT-PRN-028).

Authentication answers exactly one question: who presented the request?
It is a DECLARED SINGLE IMPLEMENTATION surface (ACTOR_CONTEXT.md §6) — the
database cannot verify an HTTP credential, so, as with H9's probing, this
transport concern is not part of the triangulated pair (the binding rule
and the database guard are). Production identity providers are
protocol-bound followers of PrincipalVerifier.

The verifier returns authenticated identity facts ONLY. It never returns
permissions, case access, visibility grants, or sealed-content rights —
those are 1F-B. `credential valid` must never collapse into `principal
trusted for all purposes`.
"""

from __future__ import annotations

from typing import Protocol

from ..domain.actor_binding import AuthenticatedPrincipal, PrincipalClass


class PrincipalVerifier(Protocol):
    def verify(self, credential: str | None) -> AuthenticatedPrincipal | None:
        """Return the AuthenticatedPrincipal a valid credential proves, or
        None if the credential is absent or unverifiable. Never raises for
        an unauthenticated request — absence is a fact the caller handles."""
        ...


class DevTokenVerifier:
    """The Slice 1F-A dev/test verifier: a fixed registry of bearer tokens
    to authenticated identity facts. Stands in for a real IdP at exactly
    the PrincipalVerifier contract; it grants nothing beyond identity."""

    def __init__(self, registry: dict[str, AuthenticatedPrincipal]) -> None:
        self._registry = dict(registry)

    def verify(self, credential: str | None) -> AuthenticatedPrincipal | None:
        if not credential:
            return None
        token = credential.removeprefix("Bearer ").strip()
        return self._registry.get(token)


def default_dev_verifier() -> DevTokenVerifier:
    """A minimal registry for development and the H10 suite. Tokens map to
    identity only — no authority is implied by holding one."""
    return DevTokenVerifier(
        {
            "human-reyes": AuthenticatedPrincipal(
                principal_id="det.reyes",
                principal_class=PrincipalClass.HUMAN,
                authentication_method="dev-token",
            ),
            "human-morgan": AuthenticatedPrincipal(
                principal_id="det.morgan",
                principal_class=PrincipalClass.HUMAN,
                authentication_method="dev-token",
            ),
            "service-ingest": AuthenticatedPrincipal(
                principal_id="ingest-verifier-01",
                principal_class=PrincipalClass.SERVICE,
                authentication_method="dev-token",
                human_attribution="det.reyes",
            ),
        }
    )
