"""Chain canonical format, version 1 (ADR-0016).

This module is the Python rendering of the chain_version=1 specification.
PostgreSQL carries an equivalent rendering inside argus_private (migration
003); a PostgreSQL-gated parity test proves the two agree. The verifier never
re-canonicalizes payloads — it hashes the STORED canonical text — so this
module's payload renderer is used only when producing events on the
test-only SQLite path and when checking the parity of the two renderings.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

CHAIN_VERSION = 1
GENESIS_HASH = "0" * 64

# Fixed field order (ADR-0016 §canonical format).
FIELD_ORDER = (
    "chain_version",
    "case_id",
    "seq",
    "target_type",
    "target_id",
    "action",
    "actor_class",
    "actor_id",
    "ai_model_version",
    "occurred_at",
    "outcome",
    "canonical_payload",
    "previous_event_hash",
)

NULL_TOKEN = "\\N"


def escape_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n")


def format_timestamp(dt: datetime) -> str:
    """ISO-8601 UTC with microseconds: YYYY-MM-DDTHH:MM:SS.ffffffZ.
    Naive datetimes are treated as UTC (SQLite round-trip)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _check_payload_values(obj: object) -> None:
    """chain_version=1 restricts payload values to strings, booleans, null,
    integers, arrays, and objects thereof — no floats (ADR-0016)."""
    if isinstance(obj, bool) or obj is None or isinstance(obj, (str, int)):
        return
    if isinstance(obj, float):
        raise ValueError("chain_version=1 payloads may not contain floats")
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ValueError("payload object keys must be strings")
            _check_payload_values(v)
        return
    if isinstance(obj, (list, tuple)):
        for v in obj:
            _check_payload_values(v)
        return
    raise ValueError(f"unsupported payload value type: {type(obj).__name__}")


def canonical_json(payload: dict) -> str:
    """Minimal JSON: UTF-8, keys sorted by codepoint, separators ',' ':',
    non-ASCII unescaped."""
    _check_payload_values(payload)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_text(fields: dict[str, str | int | None]) -> str:
    """The exact hashed bytes: LF-separated field=value lines in FIELD_ORDER,
    no trailing newline. Null values render as the two-character token \\N."""
    lines = []
    for name in FIELD_ORDER:
        value = fields[name]
        if value is None:
            rendered = NULL_TOKEN
        else:
            rendered = escape_value(str(value))
        lines.append(f"{name}={rendered}")
    return "\n".join(lines)


def event_hash(fields: dict[str, str | int | None]) -> str:
    return hashlib.sha256(canonical_text(fields).encode("utf-8")).hexdigest()
