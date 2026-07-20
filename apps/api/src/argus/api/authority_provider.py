"""Authority grant facts (Slice 1F-B; ONT-PRN-029, Amendment 4).

An AuthorityProvider answers exactly one question: what grants does this
principal hold? It returns normalized grant FACTS — never a decision. The
dual-rendered authorize() is the decision-maker; if the provider decided,
the triangulated decision layer would be ceremonial.

The provider must not interpret epistemic state, inspect record truth,
decide a visibility or action outcome, or silently expand capability
scope. It is a declared single implementation for 1F-B (persisted grants
deferred), exactly as the dev principal verifier stood in for a production
IdP.
"""

from __future__ import annotations

from typing import Protocol

from ..domain.authority import AuthorityGrant, Capability


class AuthorityProvider(Protocol):
    def grants_for(self, principal_id: str) -> tuple[AuthorityGrant, ...]:
        """Return the normalized grant facts this principal holds. No
        ALLOW/DENY; no decision of any kind."""
        ...


class DevAuthorityProvider:
    """The Slice 1F-B dev/test provider: an explicit registry of grant
    facts. Case-scoped only — no global scope exists."""

    def __init__(self, grants: dict[str, tuple[AuthorityGrant, ...]]) -> None:
        self._grants = {k: tuple(v) for k, v in grants.items()}

    def grants_for(self, principal_id: str) -> tuple[AuthorityGrant, ...]:
        return self._grants.get(principal_id, ())


def grant(principal_id: str, capability: Capability, case_id: str) -> AuthorityGrant:
    """Build a Case-scoped grant fact (the only scope in 1F-B)."""
    return AuthorityGrant(
        principal_id=principal_id,
        capability=capability,
        scope_type="CASE",
        scope_id=case_id,
    )
