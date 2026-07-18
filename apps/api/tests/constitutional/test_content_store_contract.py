"""ContentStore protocol conformance (Slice 1E, AGC Session 016).

Every adapter — LocalContentStore today, MinIO later — must satisfy one
behavioral contract, or a future backend could silently change what
MISSING, UNREADABLE, or metadata-only existence means. The suite is
parametrized so a new adapter joins by adding a fixture param, not new
tests (ONT-PRN-010: implementations replaceable; ONT-PRN-013: semantics
defined once).
"""

from __future__ import annotations

import hashlib

import pytest

from argus.ingestion.hashing import ALGORITHM
from argus.ingestion.store import LocalContentStore, expected_storage_ref

CONTENT = b"ARGUS-CONTRACT-BYTES" + b"\x00" * 32
DIGEST = hashlib.sha256(CONTENT).hexdigest()


@pytest.fixture(params=["local"])
def adapter(request, tmp_path):
    if request.param == "local":
        return LocalContentStore(tmp_path / "contract")
    raise NotImplementedError(request.param)


class TestContentStoreContract:
    def test_staged_round_trip(self, adapter):
        adapter.put_staged("s1", CONTENT)
        assert adapter.read_staged("s1") == CONTENT

    def test_promotion_is_write_once_and_content_addressed(self, adapter):
        """Write-once: double promotion of the same digest is a no-op
        returning the same reference; the reference follows the
        constitutional content-addressing rule."""
        adapter.put_staged("s1", CONTENT)
        ref1 = adapter.promote_staged("s1", DIGEST)
        assert ref1 == expected_storage_ref(ALGORITHM, DIGEST)
        # A second staging session with different bytes must not overwrite
        # the permanent location for an already-promoted digest.
        adapter.put_staged("s2", b"different bytes entirely")
        ref2 = adapter.promote_staged("s2", DIGEST)
        assert ref2 == ref1
        assert adapter.read_permanent(DIGEST) == CONTENT

    def test_metadata_level_existence(self, adapter):
        """permanent_exists succeeds without content access and is a
        different fact from content successfully read."""
        assert adapter.permanent_exists(DIGEST) is False
        adapter.put_staged("s1", CONTENT)
        adapter.promote_staged("s1", DIGEST)
        assert adapter.permanent_exists(DIGEST) is True
        assert adapter.permanent_exists("0" * 64) is False

    def test_exact_byte_reads(self, adapter):
        adapter.put_staged("s1", CONTENT)
        adapter.promote_staged("s1", DIGEST)
        assert adapter.read_permanent(DIGEST) == CONTENT

    def test_error_normalization(self, adapter):
        """Absence is a reportable observation: reads of unknown digests
        raise an OSError subclass the prober normalizes — never a bare
        crash of unspecified type."""
        with pytest.raises(OSError):
            adapter.read_permanent("f" * 64)

    def test_quarantine_retains_and_release_removes(self, adapter):
        adapter.put_staged("q1", CONTENT)
        ref = adapter.quarantine_staged("q1")
        assert ref  # quarantine yields a reference; disposition is human
        with pytest.raises(OSError):
            adapter.read_staged("q1")  # staging copy moved, not duplicated
        if isinstance(adapter, LocalContentStore):
            # Adapter-specific retention check: bytes survive in quarantine.
            assert (adapter._quarantine / "q1").read_bytes() == CONTENT
        adapter.put_staged("r1", CONTENT)
        adapter.release_staged("r1")
        with pytest.raises(OSError):
            adapter.read_staged("r1")
