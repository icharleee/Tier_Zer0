"""Versioned content fingerprints (Session 012, Amendment 5).

The exact field set and encoding of every fingerprint is normative
(CONSTITUTIONAL_PREDICATES.md 0.6.0): implementations may not choose field
sets silently. PostgreSQL carries independent renderings; the conformance
sweep proves byte-identical digests.

- Statement fingerprint v1 (Slice 2A/2C, unchanged): SHA-256 of the single
  statement/meaning field.
- Interpretation fingerprint v2 (Slice 2D): SHA-256 over the UTF-8 encoding
  of meaning_statement, reasoning_description, uncertainty_status,
  uncertainty_explanation joined by U+001F (unit separator), in that order.
- Hypothesis fingerprint v1 (Slice 2D): the same construction over
  explanatory_statement, reasoning_description, uncertainty_status,
  uncertainty_explanation, testability_statement, challenge_condition.
"""

from __future__ import annotations

import hashlib

_SEP = "\x1f"


def _digest(fields: tuple[str, ...]) -> str:
    return hashlib.sha256(_SEP.join(fields).encode("utf-8")).hexdigest()


def interpretation_fingerprint_v2(
    meaning_statement: str,
    reasoning_description: str,
    uncertainty_status: str,
    uncertainty_explanation: str,
) -> str:
    return _digest(
        (meaning_statement, reasoning_description, uncertainty_status,
         uncertainty_explanation)
    )


def hypothesis_fingerprint_v1(
    explanatory_statement: str,
    reasoning_description: str,
    uncertainty_status: str,
    uncertainty_explanation: str,
    testability_statement: str,
    challenge_condition: str,
) -> str:
    return _digest(
        (explanatory_statement, reasoning_description, uncertainty_status,
         uncertainty_explanation, testability_statement, challenge_condition)
    )
