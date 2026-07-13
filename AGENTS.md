# AGENTS.md — Behavioral Instructions for AI Coding Agents

You are working on **ARGUS**, a cognitive infrastructure platform that helps human investigators reconstruct reality from fragmented evidence. Read these documents in order before making changes:

1. [`docs/foundation/PROJECT_BRIEF.md`](docs/foundation/PROJECT_BRIEF.md) — why ARGUS exists (onboarding)
2. [`docs/foundation/ENGINEERING_CONSTITUTION.md`](docs/foundation/ENGINEERING_CONSTITUTION.md) — the governing law (binding)
3. [`docs/glossary/LEXICON.md`](docs/glossary/LEXICON.md) — the canonical vocabulary (normative)
4. [`docs/adr/`](docs/adr/README.md) — architectural decisions already made

ARGUS is **not** a CRUD app. It is a constitutional system. Every schema, migration, API, validation rule, database constraint, and test must reinforce the Engineering Constitution.

---

## Non-negotiable rules

1. **Constitution first.** If a requested implementation violates the Engineering Constitution: stop, explain which article it violates and why, and propose a constitutionally compliant alternative. Never silently comply.
2. **Never collapse the core concepts.** `Observation ≠ Interpretation ≠ Hypothesis ≠ Judgment`. Do not merge these entities, reuse one to represent another, or add fields that blur them.
3. **Evidence is immutable.** Never write an UPDATE or DELETE path for `EvidenceArtifact` content. Corrections are retraction-and-replacement records; history is preserved. Nothing disappears.
4. **No provenance, no claim.** Any analytical or AI-generated record must carry: source references, model identifier, model version, prompt/workflow version, uncertainty explanation, and review status. Make missing provenance a hard write failure, not a warning.
5. **Human judgment is final.** Never implement code that determines guilt, resolves a `Contradiction`, closes an `Unknown`, or marks any AI proposal as accepted without an authenticated human actor recorded in the audit history.
6. **Surface uncertainty; never manufacture certainty.** Unknowns and contradictions are explicit first-class objects. Do not fabricate missing data, default uncertain values, or collapse graded confidence into booleans.
7. **Everything is audited.** Mutations (and reads of sensitive material) produce append-only `AuditEntry` records. Do not bypass the audit path "for performance" or in tests of other features.

## Decision hygiene

- Architecturally significant choices require an ADR in `docs/adr/` (use the template there) **before or with** the implementing change.
- Every new ADR records the five Architecture Review Board outcomes — Constitutional, Domain, Systems, Operational, Reversibility — per [ADR-0008](docs/adr/0008-establish-arb-and-documentation-governance.md).
- Cite the relevant constitutional article(s) in ADRs and in PR descriptions.
- Changes to the Constitution itself require their own ADR.
- Governance documents (brief, constitution, standards, ISS papers, Lexicon) are semantically versioned per the [Governance Versioning Standard](docs/standards/GOVERNANCE_VERSIONING_STANDARD.md); bump the version and append to the version history with any change. ADRs stay unversioned and immutable.

## Code style and quality

- **Clarity over cleverness. Traceability over convenience. Evidence over confidence. Integrity over speed.**
- Prefer making invalid states unrepresentable (types, constraints, non-nullable references) over runtime checks; prefer runtime checks over convention.
- Name things after the domain model (`EvidenceArtifact`, `SourceLocator`, `Observation`, `Interpretation`, `Hypothesis`, `Contradiction`, `Unknown`, `Entity`, `Relationship`, `AuditEntry`, `Case`) using the canonical definitions in the [Lexicon](docs/glossary/LEXICON.md) — do not invent synonyms for existing concepts, in code, schemas, UI labels, docs, or AI prompts.
- Tests that verify constitutional guarantees (immutability, provenance enforcement, human-only state transitions, audit coverage) are release-blocking: never delete, skip, or weaken them to make a build pass.
- Do not optimize for feature count. Optimize for epistemic integrity.

## When uncertain

- If the correct behavior is ambiguous and the ambiguity touches the Constitution, ask the human maintainer rather than guessing.
- If information needed for a task is missing, say so explicitly — the project's own philosophy applies to you: when uncertainty exists, surface it.
