"""Constitutional errors.

A ConstitutionalViolation is not a validation error: it marks an attempt to do
something the Engineering Constitution forbids. It always names the ontology
rule (ONT-…) it protects, so a failure five years from now reads as:
violated rule, affected principle, constitutional article (ADR-0010).
"""

from __future__ import annotations


class ConstitutionalViolation(Exception):
    """Raised when an operation would violate a constitutional invariant."""

    def __init__(self, ontology_rule: str, message: str) -> None:
        self.ontology_rule = ontology_rule
        super().__init__(f"[{ontology_rule}] {message}")
