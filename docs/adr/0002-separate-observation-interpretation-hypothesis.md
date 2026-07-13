# ADR-0002: Separate Observation, Interpretation, and Hypothesis as distinct entities

- **Status:** Accepted
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), III (Conclusions explain themselves), IV (Alternatives remain possible), IX (Certainty never exceeds evidence)

## Context

The central failure mode of investigative tooling is epistemic collapse: what the evidence *shows*, what it *may mean*, and what *might have happened* get flattened into a single "finding," after which certainty silently exceeds the evidence and alternatives disappear. The domain model must make this collapse impossible, not merely discouraged.

## Decision

We will model the analytical ladder as three distinct first-class entities, each referencing the layer beneath it:

- **`Observation`** — a statement of what an `EvidenceArtifact` shows, anchored to it via a `SourceLocator`. Observations contain no meaning-making.
- **`Interpretation`** — a statement of what one or more Observations may mean. Every Interpretation references the Observations it interprets.
- **`Hypothesis`** — a candidate explanation composed from Interpretations. Hypotheses over the same evidence coexist; none is structurally privileged.

Judgment is not modeled. It is a human act that occurs outside ARGUS.

These entities will remain separate in schema, API, and UI. No shared table with a `type` column, no field additions that let one layer carry another's content, no convenience endpoint that creates a Hypothesis directly from evidence.

## Consequences

- Every claim answers "what evidence supports this?" by construction: Hypothesis → Interpretation(s) → Observation(s) → SourceLocator → EvidenceArtifact.
- More records and more joins than a flattened model; this is an accepted cost (Article VII — integrity before convenience).
- APIs and UIs must present the ladder honestly, which constrains UX shortcuts.
- Validation must reject cross-layer references that skip a level.

## Alternatives considered

- **Single `Finding` entity with a `level` field** — rejected: nothing but convention prevents level drift, and conventions do not survive deadlines.
- **Free-form linking (any analytical node references any other)** — rejected: permits Hypotheses grounded in nothing, violating Article I.
