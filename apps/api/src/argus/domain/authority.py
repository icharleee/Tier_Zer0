"""Authority and visibility (Slice 1F-B; ONT-PRN-029/030, ADR-0034/0035).

Authority changes what a principal may do or see. It never changes what a
constitutional record means (ONT-PRN-029). Access to protected information
is explicit, least-privileged, attributable, and auditable; absence of
access is never absence of evidence (ONT-PRN-030).

This module is the domain rendering of two pure things:

  - authorize(...)  -> the ALLOW/DENY decision over normalized, resource-
                       scoped capability grants. PostgreSQL carries an
                       independent rendering (argus_private.authorize); the
                       H11 conformance sweep compares them.
  - project_artifact_visibility(...) -> the two-stage visibility envelope,
                       derived separately from the action decision.

Grants are supplied as FACTS by an AuthorityProvider (argus.api); this
module never decides who holds what — only what a held set of grants
authorizes. Capabilities are Case-scoped, stand alone (no inheritance),
and there is no global scope in 1F-B.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Capability(enum.Enum):
    # Action authority — each authorizes exactly one constitutional command.
    OBSERVATION_CREATE = "OBSERVATION_CREATE"
    INTERPRETATION_CREATE = "INTERPRETATION_CREATE"
    HYPOTHESIS_CREATE = "HYPOTHESIS_CREATE"
    UNKNOWN_RESOLVE = "UNKNOWN_RESOLVE"
    CONTRADICTION_DISPOSE = "CONTRADICTION_DISPOSE"
    RETRACTION_PERFORM = "RETRACTION_PERFORM"
    # Visibility authority.
    CASE_READ = "CASE_READ"
    SEALED_METADATA_READ = "SEALED_METADATA_READ"
    SEALED_CONTENT_READ = "SEALED_CONTENT_READ"
    SEALED_VERIFY = "SEALED_VERIFY"


ACTION_CAPABILITIES = frozenset({
    Capability.OBSERVATION_CREATE, Capability.INTERPRETATION_CREATE,
    Capability.HYPOTHESIS_CREATE, Capability.UNKNOWN_RESOLVE,
    Capability.CONTRADICTION_DISPOSE, Capability.RETRACTION_PERFORM,
})
VISIBILITY_CAPABILITIES = frozenset({
    Capability.CASE_READ, Capability.SEALED_METADATA_READ,
    Capability.SEALED_CONTENT_READ, Capability.SEALED_VERIFY,
})


class Decision(enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


# Decision reasons (no scoring, no trust level, no partial authority).
CAPABILITY_NOT_GRANTED = "CAPABILITY_NOT_GRANTED"
RESOURCE_SCOPE_MISMATCH = "RESOURCE_SCOPE_MISMATCH"

# Canonical codes the enforcement layer maps decisions onto.
ACTION_NOT_AUTHORIZED = "ONT-PRN-029:action-not-authorized"
VISIBILITY_NOT_AUTHORIZED = "ONT-PRN-029:visibility-not-authorized"
OUT_OF_SCOPE_RESOURCE = "ONT-PRN-029:out-of-scope-resource"
UNAUTHENTICATED = "ONT-PRN-007:unauthenticated"


@dataclass(frozen=True)
class AuthorityGrant:
    """A normalized grant FACT supplied by an AuthorityProvider. Case scope
    only in 1F-B (no global '*')."""

    principal_id: str
    capability: Capability
    scope_type: str  # "CASE"
    scope_id: str  # case_id


@dataclass(frozen=True)
class AuthorityDecision:
    decision: Decision
    reason: str | None = None  # None on ALLOW

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW


def authorize(
    required_capability: Capability,
    resource_case_id: str,
    grants: tuple[AuthorityGrant, ...],
) -> AuthorityDecision:
    """The pure authority decision. ALLOW iff some grant carries exactly the
    required capability at the requested Case scope. No inheritance: only
    the named capability satisfies the check.

    - a grant with the capability but a different Case -> RESOURCE_SCOPE_MISMATCH
    - no grant with the capability at all             -> CAPABILITY_NOT_GRANTED
    """
    capability_held = False
    for g in grants:
        if g.capability is required_capability:
            capability_held = True
            if g.scope_type == "CASE" and g.scope_id == resource_case_id:
                return AuthorityDecision(Decision.ALLOW)
    reason = RESOURCE_SCOPE_MISMATCH if capability_held else CAPABILITY_NOT_GRANTED
    return AuthorityDecision(Decision.DENY, reason)


def code_for(required_capability: Capability, decision: AuthorityDecision) -> str:
    """Map a DENY decision to the canonical constitutional code, by whether
    the capability is an action or a visibility one."""
    if decision.reason == RESOURCE_SCOPE_MISMATCH:
        return OUT_OF_SCOPE_RESOURCE
    if required_capability in ACTION_CAPABILITIES:
        return ACTION_NOT_AUTHORIZED
    return VISIBILITY_NOT_AUTHORIZED


def _has(grants: tuple[AuthorityGrant, ...], cap: Capability, case_id: str) -> bool:
    return authorize(cap, case_id, grants).allowed


def project_artifact_visibility(
    *, sealed: bool, case_id: str, grants: tuple[AuthorityGrant, ...]
) -> dict:
    """The two-stage visibility envelope (Amendment 2), derived SEPARATELY
    from the action decision. This is invoked only after CASE_READ has
    gated the surface, so existence is disclosable here; a principal
    without CASE_READ never reaches this projection (the endpoint issues a
    generic resource denial instead — secrecy is not an existence leak).

    The underlying record is singular; only this projection changes (O14).
    """
    if not sealed:
        # A FULL artifact has no protected portion; CASE_READ sees all.
        return {
            "state": "FULL",
            "existence_visible": True,
            "metadata_visible": True,
            "content_visible": True,
            "withholding_basis": None,
        }
    metadata_visible = _has(grants, Capability.SEALED_METADATA_READ, case_id)
    content_visible = _has(grants, Capability.SEALED_CONTENT_READ, case_id)
    return {
        "state": "SEALED",
        "existence_visible": True,
        "metadata_visible": metadata_visible,
        "content_visible": content_visible,
        # Withholding is declared while any protected portion is withheld.
        "withholding_basis": (
            None if (metadata_visible and content_visible) else "AUTHORITY_REQUIRED"
        ),
    }
