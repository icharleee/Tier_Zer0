# ADR-0003: Append-only evidence with retraction instead of deletion

- **Status:** Accepted
- **Date:** 2026-07-13
- **Constitutional articles:** V (Evidence is immutable), VIII (Justice requires transparency)

## Context

Evidence handling must survive adversarial audit. If evidence records can be updated or deleted, no downstream claim is trustworthy: a defense attorney auditing the system must be able to establish that what analysts saw then is what the record shows now. The same holds for the analytical records built on top of evidence — corrections happen, but they must be visible as corrections.

## Decision

We will make `EvidenceArtifact` records append-only:

- No UPDATE or DELETE path exists for evidence content, at the API layer **and** at the database layer (permissions/constraints, not just service code).
- Artifact content is content-addressed (cryptographic hash stored at ingest) so tampering is detectable.
- Corrections are **retraction-and-replacement**: a new record is created, the old record is marked retracted with a reason and an explicit link to its replacement, and both remain readable.
- The same retraction pattern applies to analytical records (`Observation`, `Interpretation`, `Hypothesis`): they are never edited in place or hard-deleted.
- Every ingest, retraction, and replacement produces an `AuditEntry`.

Nothing disappears. History is preserved.

## Consequences

- Storage grows monotonically; cost is managed by tiering, never by deletion of case history.
- Legal destruction requirements (e.g., court-ordered expungement) are a distinct, explicitly authorized administrative process — outside normal application flows — that itself leaves an audit trail to the extent the order permits (Article VI).
- Bugs that write bad data cannot be silently cleaned up; fixes are visible retractions. This is the point.
- Queries must be retraction-aware; the default read path excludes retracted records but never hides their existence.

## Alternatives considered

- **Soft-delete flags with in-place edits** — rejected: an edited record destroys the historical fact of what was previously recorded, violating Article V.
- **Event sourcing for the entire system** — deferred, not rejected: full event sourcing may be adopted later by a superseding ADR; append-only-with-retraction is the minimal guarantee the Constitution demands and does not preclude it.
