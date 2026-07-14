# Database infrastructure provisioning

Role and database creation live here, **outside** Alembic (ADR-0016, Amendment 5): migrations create schemas, tables, functions, and grants against roles that already exist, and fail clearly when they don't.

| Role | Purpose | Privileges |
|---|---|---|
| `argus_owner` | Runs migrations; owns all objects and SECURITY DEFINER functions | Object owner; never used at runtime |
| `argus_app` | Application runtime | SELECT + narrow INSERTs; `UPDATE(storage_ref)` on artifacts only; EXECUTE on `argus_private` functions; **no** UPDATE on constitutional columns, **no** DELETE anywhere, no CREATE on any schema |
| `argus_test_admin` | Corruption-detection test only (dev/CI, never production) | Direct table access granted by migration 003 in dev/CI to deliberately tamper across the trust boundary |

Order: `provision.sh` (roles + database + schema-CREATE lockdown) → `alembic upgrade head` as `argus_owner` → application connects as `argus_app`.

Trust boundary (ADR-0016): the application role and ordinary operational roles cannot perform forbidden mutations. Privileged owners remain inside the declared trust boundary; unauthorized privileged modifications are detected through audit-chain verification, migration review, and operational controls.
