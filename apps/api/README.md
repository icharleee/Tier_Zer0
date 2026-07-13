# ARGUS API — authoritative domain layer

Slice 1: **Constitutional Evidence Activation** (ADR-0007, ADR-0015).

This package derives from the [Ontology](../../docs/domain/ONTOLOGY.md) via the [Derivation Specification](../../docs/domain/DERIVATION_SPECIFICATION.md). It implements meaning; it does not define it (ONT-PRN-010).

## What exists

- `argus.domain` — Case, EvidenceArtifact, AuditEntry models (SQLAlchemy 2.x); explicit constitutional transitions (ONT-PRN-012) with the allowed-predecessor registry derived from [Entity Lifecycles](../../docs/domain/ENTITY_LIFECYCLES.md) §2; atomic audit emission (D-AUD).
- `argus.ingestion` — the ADR-0007 protocol: staging (pre-constitutional) → T1 record creation → idempotent verification → T2 activation, with quarantine-not-deletion on integrity failure. `ContentStore` abstraction with a local implementation (S3/MinIO arrives with the Compose stack).
- `tests/constitutional` — the Slice 1 suite, including **the first acceptance test of ARGUS** (ADR-0007 §9). Every test cites the ontology rule it protects (ADR-0010).
- `tools/constitutional_coverage.py` — the Constitutional Coverage metric skeleton (per-article test coverage, ADR-0007 §8).

## Running

```
cd apps/api
python -m pytest                          # constitutional suite (SQLite, app layer)
python tools/constitutional_coverage.py   # per-article coverage report
```

Runtime policy per ADR-0006: Python 3.13 primary (`.python-version`); the suite is version-portable for development convenience.

## Deliberately not here yet (remaining Slice 1 work)

- Alembic migrations carrying the **database-layer** enforcement of the [Invariant Matrix](../../docs/domain/INVARIANT_MATRIX.md) (INSERT-only grants, controlled transition functions, audit immutability for all roles) and the `@postgres` tests that prove them against the real Compose stack.
- FastAPI surface, the minimal UI ("visible in UI" leg of the loop), MinIO `ContentStore`, Docker Compose, CI wiring.
- Reconciliation sweep (ADR-0007 §4) and stalled-`PENDING_VERIFICATION` surfacing.
