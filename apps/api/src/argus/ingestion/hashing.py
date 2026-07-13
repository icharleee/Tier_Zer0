"""System-computed content identity (ADR-0007 §3, §5).

The hash of record is always computed by the system that stores the bytes —
never trusted from the client. SHA-256 initially; the algorithm identifier is
recorded per artifact so migration is additive (the original digest is never
replaced).
"""

from __future__ import annotations

import hashlib

ALGORITHM = "sha-256"


def compute_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
