# ADR-0016: Append-only audit hash chain (tamper-evident within the trust boundary)

- **Status:** Accepted (freeze exemption authorized by AGC Slice 1B plan review — implementation-discovered gap per ONT-PRN-011)
- **Date:** 2026-07-13
- **Constitutional articles:** V (Evidence is immutable), VIII (Justice requires transparency), IX (Certainty must never exceed the evidence)
- **Supersedes:** none (resolves the hash-chaining unresolved question of Domain Schema Specification §14 / ONT-AUD-001)

## Context

Slice 1B requires PostgreSQL to independently enforce audit integrity. The ratified spec listed hash-chaining as an unresolved question; implementing database enforcement forces the decision now. This is the Resolution 006 flow working as designed: Ontology → Implementation → Discovery → ADR.

## Decision

### Chain scope and head

Each Case has one audit chain. A **`case_audit_heads`** row (`case_id` PK, `last_sequence`, `last_event_hash`, `updated_at`) is the chain's aggregate root, created with the Case at sequence 0. It eliminates `MAX(seq)+1` and gives the chain inspectable state.

### Lock ordering (global, mandatory)

Every database operation that mutates an aggregate and appends to a case chain uses exactly this order:

1. `SELECT … FOR UPDATE` on `case_audit_heads` (per-case serialization);
2. `SELECT … FOR UPDATE` on the aggregate row (e.g., the EvidenceArtifact);
3. validate the transition (predecessor state, actor class, required inputs);
4. update the aggregate;
5. append the AuditEntry;
6. update the head.

No advisory locks; no other order anywhere.

### Canonical format — `chain_version = 1`

`event_hash = sha256(canonical_text)`, lowercase hexadecimal. `canonical_text` is UTF-8, LF (`\n`) line separator, one `field=value` line per field, in exactly this order, with **no trailing newline**:

```
chain_version, case_id, seq, target_type, target_id, action,
actor_class, actor_id, ai_model_version, occurred_at, outcome,
canonical_payload, previous_event_hash
```

- **Escaping (values only):** `\` → `\\`, LF → `\n` (two characters). Field names never need escaping.
- **Null:** the two-character value `\N` (distinct from empty string, which is an empty value).
- **Timestamps:** ISO-8601 UTC with microseconds: `YYYY-MM-DDTHH:MM:SS.ffffffZ`.
- **Identifiers:** lowercase hexadecimal (as generated; never re-cased).
- **Digest encoding:** lowercase hex.
- **Payload canonicalization:** `canonical_payload` is the payload object rendered as minimal JSON — UTF-8, keys sorted by Unicode codepoint, separators `,` and `:` with no whitespace, no ASCII-escaping of non-ASCII characters. **Version 1 restricts payload values to strings, booleans, null, integers, arrays, and objects thereof** (no floats — this removes cross-engine numeric-representation ambiguity).
- **Genesis:** `previous_event_hash` for `seq = 1` is 64 ASCII `0` characters.

The append routine derives `canonical_payload` from the supplied `jsonb` **exactly once at insertion**; callers may not submit it. Two representations are stored with defined roles: `detail` (jsonb — human/queryable) and `canonical_payload` (text — the immutable bytes hashed into the chain). **The verifier hashes stored canonical text; it never re-canonicalizes from jsonb.**

### Immutable hashed fields

`canonical_payload`, `event_hash`, `previous_event_hash`, `chain_version`, and every hashed field are immutable: the application role receives no UPDATE or DELETE on `audit_entries` at all, and only the append function inserts.

### Verification

A verification service walks a case's chain and checks: gapless monotonic sequence from 1; genesis rule; per-row recomputed hash against stored `event_hash` (from stored fields and stored canonical text); `previous_event_hash` linkage; head consistency (`last_sequence`/`last_event_hash` match the final row). The property claimed is **append-only and tamper-evident within the implemented trust boundary** — never tamper-proof.

### Trust boundary

The application role and ordinary operational roles cannot perform forbidden mutations. Privileged owners and administrators remain inside the declared trust boundary; unauthorized privileged modifications are *detected* through audit-chain verification, migration review, and operational controls — not prevented (Article IX: no impossible guarantees). Actor identity in Slice 1B is asserted by the trusted Python service; the database enforces actor-*class* rules, not actor authenticity (authentication is Slice 1D's problem).

### Failure and repair policy

A verification failure is surfaced for human disposition (Article II) and is never repaired by editing rows. Repair is forward-only: a compensating AuditEntry documenting the finding, plus operational restoration from backups where warranted, both leaving the failed rows in place as evidence of the incident.

### Future chain versions

Historical events are **never silently rehashed**. A future `chain_version = 2` begins at a documented checkpoint event that records the terminal hash of the version-1 chain; verification validates each segment under its own version and the continuity of checkpoints.

### Role provisioning boundary (Amendment 5)

Roles (`argus_owner`, `argus_app`, and test-only `argus_test_admin`) are created by infrastructure provisioning (`infra/db/`), never by Alembic. Migration 001 verifies the roles exist and fails clearly if not. Migrations create schemas, tables, functions, grants, and revocations against pre-existing roles.

### SECURITY DEFINER hardening (Amendment 3)

All controlled functions live in the non-user-writable schema `argus_private`; every referenced object is schema-qualified; each function sets `search_path = argus_private, pg_catalog, pg_temp`; EXECUTE is revoked from PUBLIC and granted only to `argus_app`; functions are created and permissioned in the same transaction. The application role has no CREATE on any schema in that path. (Function ownership by a dedicated non-login role is noted as production hardening for the deployment ADR; dev/CI use the migration owner.)

## Governance review

1. **Constitutional Review** — PASS: strengthens Articles V and VIII; Article IX honored by tamper-*evident* language and the declared trust boundary.
2. **Domain Review** — PASS: ONT-AUD-001 semantics implemented, not altered; the head row is chain bookkeeping, not a new domain concept.
3. **Architectural Review** — PASS: one global lock order (deadlock-free by construction among these paths); head row inspectable and O(1); canonical format fully reproducible; reversible only forward (checkpoint scheme), which is the appropriate stickiness for an integrity mechanism.

## Consequences

- `MAX+1` is gone; concurrency is serialized per case with an explicit, inspectable head.
- The audit chain becomes independently verifiable by an external auditor from stored bytes alone (Article VIII).
- Two payload representations must be kept honest — enforced by deriving one from the other in exactly one place and hashing the stored bytes.
- plpgsql carries a canonical-JSON renderer; Python carries the same spec for the test-only SQLite path, with a PostgreSQL-gated parity test proving the two renderings agree.

## Alternatives considered

- **Advisory lock on `hashtext(case_id)`** — rejected (Amendment 2): hash-space compression lets unrelated cases block each other; the head row also replaces the aging `MAX(seq)` query.
- **Hashing a re-serialization of jsonb at verify time** — rejected (Amendment 4): two serializations diverge; hash the stored canonical bytes.
- **Global chain** — rejected: needless cross-case contention; per-case matches the audit scope already ratified.
- **Tamper-proof claims via database controls alone** — rejected: overclaims against administrators (Article IX).

## Constitutional Checklist

- [x] Article I — Evidence before opinion
- [x] Article II — Human judgment is final
- [x] Article III — Every analytical conclusion must explain itself
- [x] Article IV — Alternative explanations must always remain possible
- [x] Article V — Evidence is immutable
- [x] Article VI — Privacy and legal authority must be respected
- [x] Article VII — Scientific integrity before convenience
- [x] Article VIII — Justice requires transparency
- [x] Article IX — Certainty must never exceed the evidence

**Affected Articles:** V, VIII (reinforced: durable append-only enforcement, externally verifiable trail); IX (honored: tamper-evident, bounded claims); II (repair policy keeps disposition human).

**Compliant?** YES

**Explanation:** This ADR adds integrity machinery beneath already-ratified audit semantics. It makes no analytical claims, moves no judgment, and carefully bounds what the database can and cannot defend against.
