"""Authenticated actor binding (Slice 1F-A; ONT-PRN-028, ADR-0033).

Identity is authenticated, never asserted. The domain Actor attributed to a
constitutional action is DERIVED from an AuthenticatedPrincipal established
at a trusted transport boundary — never taken from request payload.

This module is the domain rendering of the binding rule: a pure function
from (principal, required class) to an Actor or a canonical refusal. It
holds no transport concerns (authentication lives in argus.api) and no
authority concerns (what an actor may do or see is 1F-B). Authentication
establishes attribution only: no authority, access, credibility, or
epistemic standing.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .actors import Actor, ActorClass
from .exceptions import ConstitutionalViolation

# Canonical refusal codes (ACTOR_CONTEXT.md §7).
UNAUTHENTICATED = "ONT-PRN-007:unauthenticated"
IDENTITY_INPUT_PROHIBITED = "ONT-PRN-007:identity-input-prohibited"
IDENTITY_SUBSTITUTION = "ONT-PRN-007:identity-substitution"
PRINCIPAL_CLASS_MISMATCH = "ONT-PRN-007:principal-class-mismatch"
ACTOR_PRINCIPAL_MISMATCH = "ONT-PRN-007:actor-principal-mismatch"

# Request fields that would carry caller-controlled identity. Their mere
# presence on a constitutional command is refused (Amendment 3), even when
# the value matches the principal — matching caller assertion is still
# assertion; identity is transport-derived, not payload-confirmed.
RESERVED_IDENTITY_FIELDS = frozenset(
    {"actor_id", "actor_class", "created_by", "created_by_id", "created_by_class",
     "human_authority", "human_attribution", "principal_id", "responsible",
     "recorded_by", "resolved_by", "disposed_by", "linked_by"}
)


class PrincipalClass(enum.Enum):
    """What the transport boundary proved. HUMAN authenticates as a person;
    SERVICE authenticates as a provisioned system credential acting under a
    traceable human attribution."""

    HUMAN = "HUMAN"
    SERVICE = "SERVICE"


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Established ONLY by a PrincipalVerifier (argus.api.authentication),
    never constructed from request data. Carries authenticated identity
    facts only — no permission set, no case access, no visibility grants,
    no sealed-content rights (those are 1F-B)."""

    principal_id: str
    principal_class: PrincipalClass
    authentication_method: str
    # SERVICE only: the human identity associated with a mechanical action,
    # for traceability. ATTRIBUTION METADATA ONLY (ADR-0033) — never proof
    # the human authorized the current action.
    human_attribution: str | None = None


def refuse(code: str, message: str) -> ConstitutionalViolation:
    return ConstitutionalViolation("ONT-PRN-028", f"{message}: {code}")


def reject_identity_input(payload_keys) -> None:
    """Refuse a constitutional command that carries any caller-controlled
    identity field. Called by the transport layer before binding."""
    offending = sorted(set(payload_keys) & RESERVED_IDENTITY_FIELDS)
    if offending:
        raise refuse(
            IDENTITY_INPUT_PROHIBITED,
            f"constitutional commands carry no identity field; "
            f"got {', '.join(offending)} (identity is transport-derived, "
            f"not payload-confirmed)",
        )


def bind_actor(
    principal: AuthenticatedPrincipal | None,
    *,
    requires_class: ActorClass = ActorClass.HUMAN,
) -> Actor:
    """Derive the domain Actor from the authenticated principal. Pure: no
    transport, no persistence, no authority decision.

    - HUMAN principal            -> Actor(HUMAN, actor_id = principal_id)
    - SERVICE principal (SYSTEM) -> Actor(SYSTEM, actor_id = principal_id,
                                          human_authority = human_attribution)

    No path takes actor_id or human_authority from request data. The
    `requires_class` is the class the action demands; a principal that
    cannot satisfy it is refused (never elevated by claim).
    """
    if principal is None:
        raise refuse(UNAUTHENTICATED, "no authenticated principal for a constitutional command")

    if requires_class is ActorClass.AI:
        # AI authorship remains unauthorized wherever it already is; 1F-A
        # introduces no AI principal path.
        raise refuse(
            PRINCIPAL_CLASS_MISMATCH,
            "AI authorship is not authorized; no AI principal path exists",
        )

    if requires_class is ActorClass.HUMAN:
        if principal.principal_class is not PrincipalClass.HUMAN:
            raise refuse(
                PRINCIPAL_CLASS_MISMATCH,
                f"a HUMAN action requires a HUMAN principal; "
                f"principal is {principal.principal_class.value}",
            )
        return Actor(ActorClass.HUMAN, principal.principal_id)

    # requires_class is SYSTEM: a mechanical SystemProcess action.
    if principal.principal_class is not PrincipalClass.SERVICE:
        raise refuse(
            PRINCIPAL_CLASS_MISMATCH,
            f"a SYSTEM action requires a SERVICE principal; "
            f"principal is {principal.principal_class.value}",
        )
    # human_attribution traces to the provisioned principal, never payload.
    return Actor(
        ActorClass.SYSTEM,
        principal.principal_id,
        human_authority=principal.human_attribution,
    )
