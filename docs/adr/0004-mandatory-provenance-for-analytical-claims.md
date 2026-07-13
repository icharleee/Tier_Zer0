# ADR-0004: Mandatory provenance for all analytical claims

- **Status:** Accepted
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), III (Conclusions explain themselves), VIII (Transparency), IX (Certainty never exceeds evidence)

## Context

"No provenance, no claim" is the project's core data rule. If provenance is optional-but-encouraged, it will be omitted under time pressure, and unexplainable claims will accumulate. Provenance must therefore be enforced where it cannot be bypassed: at the persistence boundary.

## Decision

We will make provenance a structural precondition for writing any analytical record:

- Every `Observation`, `Interpretation`, and `Hypothesis` must carry non-empty source references down its ladder (per ADR-0002) at creation time. Writes without them are rejected, not defaulted.
- Every AI-generated record must additionally carry, as required fields:
  - source references,
  - model identifier,
  - model version,
  - prompt/workflow version,
  - an uncertainty explanation,
  - review status (initialized to *unreviewed*; only an authenticated human may advance it).
- Provenance fields are immutable after write (corrections follow ADR-0003 retraction).
- Exports include full provenance, so claims remain auditable outside the system.

## Consequences

- Claims are auditable end-to-end by external parties without access to internal tooling.
- Ingest and analysis pipelines must thread provenance through every step; ad-hoc scripts that "just insert results" are impossible by design.
- AI integrations must be versioned (model + prompt/workflow) before they may write anything, which slows integration of new models. Accepted cost.
- Reproducing an AI-generated claim's context (which model, which workflow, which sources) is always possible.

## Alternatives considered

- **Provenance as recommended metadata, enforced in review** — rejected: human review does not scale and fails exactly when pressure is highest.
- **Provenance captured in logs rather than on the record** — rejected: logs rotate, are internal-only, and do not travel with exports; Article VIII requires the claim itself to carry its explanation.
