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

## Slice 1B — PostgreSQL enforcement (complete)

The persistence boundary is independently hostile to unconstitutional writes (ADR-0016):

- `infra/db/` provisions roles (`argus_owner`, `argus_app`, dev/CI-only `argus_test_admin`) **before** Alembic; migration 001 verifies they exist.
- Three migrations: 001 case/authority/audit-head foundation; 002 artifact integrity (immutable-column trigger, status CHECK excluding STAGED, least-privilege grants); 003 hash-chained `audit_entries` and the `argus_private` SECURITY DEFINER transition functions (hardened search_path, PUBLIC revoked, one global lock order: head row, then artifact row).
- The app role cannot: update constitutional columns or status, delete anything, insert audit entries directly, or call the transition core — only the six named wrappers.
- Audit chain: per-case, head-rooted, `chain_version=1` canonical format hashed in the append function; Python verifier (`argus.domain.chain`) recomputes from stored bytes. **Tamper-evident within the declared trust boundary, not tamper-proof.**

```
# dev/CI bootstrap (requires local PostgreSQL as superuser 'postgres')
sh ../../infra/db/provision.sh
python -m alembic upgrade head                    # as argus_owner
DATABASE_URL=postgresql+psycopg2://argus_app:...@127.0.0.1/argus \
ARGUS_TEST_ADMIN_URL=postgresql+psycopg2://argus_test_admin:...@127.0.0.1/argus \
python -m pytest                                  # 29 tests incl. adversarial suite
```

Known trust-boundary limits: actor identity is asserted by the trusted Python service (authentication is Slice 1D); privileged owners can alter schema/data — detected via chain verification, not prevented.

- **Slice 2A — Competing Interpretations (complete)**: rung two of the ladder. Structured uncertainty envelope (no "certain" status — Article IX), grounding snapshots (fingerprint + role + linked_at), comparative-vocabulary lexical guard, derived `grounding_health`, and the H4 property: competing interpretations over identical grounding with no epistemic-ranking surface, symmetric exposure, and no promotion on retraction. Citation order is technical and non-evidentiary.

## Deliberately not here yet (roadmap per AGC Session 005 — the ontology leads; storage serves the domain)

- **Slice 1C — Observation eligibility (complete)**: constitutional predicates (ADR-0018) — `argus.domain.predicates` and `argus_private.can_support_observation` independently render the [canonical matrix](../../docs/domain/CONSTITUTIONAL_PREDICATES.md); derived never stored; refusals answer with canonical reason codes; H2 conformance sweep proves identical decisions (16/16 rows). Transition-authority predicates derive from the registry (no second lifecycle rendering).
- **Slice 1D — Observation creation (complete)**: SourceLocator as scope of constitutional support (ONT-PRN-016) and Observation, the first epistemic object — validation distinct from persistence (`argus.domain.admissibility` + `argus_private.validate_*`), creation solely via controlled functions, two identities (citation + ONT-OBS-001), `is_grounded()` derived never stored, H3 conformance across the canonical refusal matrix. Perception only: no meaning fields exist, and a test proves it.
- **Slice 1E — Storage + reconciliation**: MinIO `ContentStore`, Docker Compose, reconciliation sweep (ADR-0007 §4), stalled-`PENDING_VERIFICATION` surfacing.
- **Slice 1F — API/UI**: FastAPI surface, authenticated actor context, the visible-UI leg, CI wiring.
- Long-term (ADR-0017 / ONT-PRN-013): generated lifecycle renderings from a single Lifecycle Specification; until then the conformance sweep (`test_lifecycle_renderings_conformance`) is release-blocking.
