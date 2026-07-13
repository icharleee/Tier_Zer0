# ADR-0008: Establish the Architecture Review Board and Phase 1 documentation governance

- **Status:** Superseded by [ADR-0009](0009-establish-argus-governance-council.md) (its documentation-corpus, versioning, and Lexicon decisions are reaffirmed there; the ARB is replaced by the ARGUS Governance Council)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity before convenience), VIII (Justice requires transparency); Prime Directive
- **Supersedes:** none (extends ADR-0001)

## Context

Founder Resolution 002 declares Phase 0 — the governance foundation — closed. ADR-0001 through ADR-0006 are ratified. Until now the project has been *inventing* its governing structures; from this point it must *govern* by them. Ordinary pull-request review is sufficient for implementation changes but not for decisions that alter the architecture, the ontology, or the governing documents themselves.

## Decision

### 1. The Architecture Review Board (ARB)

An Architecture Review Board is established from Day One, even while it consists solely of the founding team. Every architecturally significant decision must answer five questions before it is accepted:

1. **Constitutional Review** — Does this violate any article of the Engineering Constitution?
2. **Domain Review** — Does this preserve the analytical ladder (Reality → Evidence → Observation → Interpretation → Hypothesis → Understanding → Human Judgment)?
3. **Systems Review** — Will this still make sense five years from now?
4. **Operational Review** — Can a small team realistically maintain it?
5. **Reversibility Review** — If we're wrong, how expensive is it to undo?

Every new ADR records these five review outcomes in a **Review outcomes** section. The ADR template is updated accordingly. Existing ADRs (0001–0006) are immutable and are not retrofitted; they are deemed reviewed by their ratification.

### 2. Expanded documentation corpus

The `docs/` tree grows beyond the original four layers:

| Directory | Role |
|---|---|
| `docs/foundation/` | Project Brief and Engineering Constitution (unchanged) |
| `docs/adr/` | Immutable architectural decisions (unchanged) |
| `docs/domain/` | Domain Schema Specification and ontology documents |
| `docs/architecture/` | ERD, Domain Invariant Matrix, system diagrams |
| `docs/research/` | Investigation Systems Science (ISS) papers — research, not implementation |
| `docs/standards/` | Implementation standards (naming, provenance, audit events, envelopes) — keeps ADRs from bloating |
| `docs/glossary/` | The ARGUS Lexicon — canonical vocabulary |
| `docs/academy/` | Self-service onboarding curriculum |

**Deviation from the proposed tree, recorded deliberately:** the resolution's sketch shows a separate `docs/constitution/`. The Constitution remains at `docs/foundation/ENGINEERING_CONSTITUTION.md` because immutable, already-ratified ADRs link to that path; moving it would break the permanent record's references. Relocation, if ever desired, requires a superseding ADR and a redirect stub at the old path.

### 3. Semantic versioning for governance documents

Governance documents (Project Brief, Engineering Constitution, ISS papers, Standards, the Lexicon) carry semantic versions per the [Governance Versioning Standard](../standards/GOVERNANCE_VERSIONING_STANDARD.md):

- **Major** — the philosophy or meaning changed.
- **Minor** — an article, definition, or section was expanded or added.
- **Patch** — grammar, clarification, wording; no semantic change.

**ADRs remain immutable and unversioned** — they are superseded, never revised (per ADR-0001 conventions).

### 4. The ARGUS Lexicon is normative

[`docs/glossary/LEXICON.md`](../glossary/LEXICON.md) is the canonical vocabulary of the project. One canonical definition per term, always. Every ADR, API, database schema, UI label, documentation page, and AI prompt must use Lexicon terms consistently. Semantic changes to Lexicon definitions are major version changes and require ARB review.

## Review outcomes

1. **Constitutional Review** — No article violated; the ARB operationalizes Articles VII and VIII by making architectural change slower, reviewed, and recorded.
2. **Domain Review** — The analytical ladder is untouched; the Domain Review question makes its preservation an explicit gate for every future decision.
3. **Systems Review** — Review boards, versioned governance, and canonical vocabularies are how long-lived institutions stay coherent; this scales from two people to two hundred.
4. **Operational Review** — Cost today is process overhead on ADRs only; the five questions take minutes for a small team and pay for themselves at the first prevented mistake.
5. **Reversibility Review** — Cheap to undo: a superseding ADR can dissolve the ARB or restructure `docs/`; nothing here constrains runtime systems.

## Consequences

- Architectural change acquires deliberate friction; implementation change does not.
- Vocabulary drift becomes a defect with a canonical reference to cite against.
- Documentation gains maintenance obligations (version headers, histories, the Lexicon) — accepted as the cost of institutional memory.
- New contributors get a self-service path (`docs/academy/`) as it fills in; until then the reading order in AGENTS.md stands.

## Alternatives considered

- **Governance by convention (no ARB)** — rejected: conventions do not survive team growth or deadlines; ADR-0002 already rejected convention as an enforcement mechanism for the same reason.
- **External wiki for research/glossary/academy** — rejected by the same reasoning as ADR-0001: governance must version with the code it governs.
- **Retrofitting review outcomes into ADRs 0001–0006** — rejected: accepted ADRs are immutable; rewriting history to look more governed than it was would itself violate the spirit of Article VIII.
