# ARGUS Entity-Relationship Diagram

- **Document version:** 0.1.0 (Slice 1 coverage — grows slice by slice per ADR-0015)
- **Derived from:** [Domain Schema Specification](../domain/DOMAIN_SCHEMA_SPECIFICATION.md) 1.1.0, [Entity Lifecycles](../domain/ENTITY_LIFECYCLES.md) 2.0.0, ADR-0007

## Slice 1 — Constitutional Evidence Activation

```mermaid
erDiagram
    CASE ||--o{ EVIDENCE_ARTIFACT : "scopes"
    CASE ||--o{ AUDIT_ENTRY : "scopes"
    CASE ||--o{ CASE_AUTHORITY : "grounded by (append-only)"
    EVIDENCE_ARTIFACT ||--o{ AUDIT_ENTRY : "target of"

    CASE {
        string id PK "opaque, never reused (C2)"
        string title
        string status "OPEN | SUSPENDED | CLOSED"
        string responsible_actor
        datetime created_at
    }
    CASE_AUTHORITY {
        string id PK
        string case_id FK
        string basis "warrant / statute / assignment"
        string recorded_by "HumanActor"
        datetime created_at "append-only; supersedes prior"
    }
    EVIDENCE_ARTIFACT {
        string id PK "opaque; identity also anchored by hash"
        string case_id FK "NOT NULL (C3)"
        string status "PENDING_VERIFICATION | ACTIVE | QUARANTINED | RETRACTED | SEALED"
        string hash_algorithm "sha-256 initial; additive only"
        string hash_digest "content-immutable forever"
        int    size_bytes "CI"
        string media_type "CI"
        string acquisition_description "CI (ONT-PRN-005)"
        string storage_ref "CT: non-authoritative pointer"
        string ingested_by "actor class + id"
        string human_authority "attributed HumanActor"
        datetime created_at
        datetime retracted_at "nullable; retraction pattern C6"
        string retraction_reason
        string superseded_by FK "nullable, self-reference"
    }
    AUDIT_ENTRY {
        string id PK
        string case_id FK "NOT NULL"
        int    seq "monotonic per case; unique(case_id, seq)"
        string actor_class "HUMAN | AI | SYSTEM"
        string actor_id
        string ai_model_version "nullable; required for AI actors"
        string action "from Lifecycles audit-event registry"
        string target_type
        string target_id
        string outcome "SUCCEEDED | REJECTED"
        string detail "structured payload (reason, transition)"
        datetime occurred_at
    }
```

Notes:

- `STAGED` does not appear: staging is pre-constitutional (ADR-0007 §2) and tracked by ingestion session outside the domain schema; only `PENDING_VERIFICATION` onward exists as a record.
- `AUDIT_ENTRY` has no update/delete path for any role; corrections are compensating entries (ONT-AUD-001).
- SourceLocator, the ladder claims, negative-space objects, Entity/Relationship arrive with Slices 2–4.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Slice 1 coverage: Case (+ append-only authority), EvidenceArtifact with the ADR-0007 explicit lifecycle, AuditEntry with per-case ordering. |
