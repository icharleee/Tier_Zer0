"""Content storage abstraction (ADR-0006 boundary 5; ADR-0007).

Providers are replaceable: evidence identity is anchored by content hash and
record ID, never by a provider URI. This module defines the interface and a
local-filesystem implementation for development and the constitutional test
suite; the S3/MinIO implementation arrives with the Compose stack and MUST
honor the same semantics (write-once permanent locations; quarantine retains,
never deletes).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .hashing import ALGORITHM


class ContentStore(Protocol):
    def put_staged(self, session_id: str, data: bytes) -> None: ...

    def read_staged(self, session_id: str) -> bytes: ...

    def promote_staged(self, session_id: str, digest: str) -> str:
        """Copy staged bytes to the permanent content-addressed location and
        return its storage reference. Write-once: promoting the same digest
        twice is a no-op (idempotence, ADR-0007 §4)."""
        ...

    def read_permanent(self, digest: str) -> bytes: ...

    def quarantine_staged(self, session_id: str) -> str:
        """Move staged bytes to quarantine. Retains, never deletes (Article II:
        disposition is human)."""
        ...

    def release_staged(self, session_id: str) -> None:
        """Remove the staging copy after successful activation — permitted
        because staging is pre-constitutional (ADR-0007 §3, step 4)."""
        ...


class LocalContentStore:
    """Filesystem implementation for development and tests."""

    def __init__(self, root: Path) -> None:
        self._staging = root / "staging"
        self._permanent = root / "permanent" / ALGORITHM
        self._quarantine = root / "quarantine"
        for d in (self._staging, self._permanent, self._quarantine):
            d.mkdir(parents=True, exist_ok=True)

    def put_staged(self, session_id: str, data: bytes) -> None:
        (self._staging / session_id).write_bytes(data)

    def read_staged(self, session_id: str) -> bytes:
        return (self._staging / session_id).read_bytes()

    def promote_staged(self, session_id: str, digest: str) -> str:
        target = self._permanent / digest
        if not target.exists():  # write-once; double promotion is a no-op
            target.write_bytes(self.read_staged(session_id))
        return f"{ALGORITHM}/{digest}"

    def read_permanent(self, digest: str) -> bytes:
        return (self._permanent / digest).read_bytes()

    def quarantine_staged(self, session_id: str) -> str:
        source = self._staging / session_id
        target = self._quarantine / session_id
        source.replace(target)
        return f"quarantine/{session_id}"

    def release_staged(self, session_id: str) -> None:
        (self._staging / session_id).unlink(missing_ok=True)
