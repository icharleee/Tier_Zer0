# ARGUS Constitutional Baseline 1.0

- **Status:** Released (authorized by AGC Review Session 023; recorded in [ADR-0037](../adr/0037-phase-4-constitutional-hardening-and-replication.md))
- **Date:** 2026-07-21
- **Nature:** An immutable, versioned pin of the completed slice roadmap's normative corpus, experimental ledger, schema head, and reference results.

**Immutability rule:** this document is never edited after release. Future work supersedes it through *Constitutional Baseline 2.0* (or later), which must state what changed and why — the completed roadmap's record is never rewritten. The only permissible post-release change to this file is a superseded-by notice at the top.

## 1. Purpose

Baseline 1.0 is the clean handoff artifact for:

1. **Independent reimplementation** (Phase 4 workstream 4D / H16) — the second team receives this baseline and the documents it pins, never the reference implementation tree.
2. **External review, research publication, and security assessment** — a fixed corpus that reviewers can cite without chasing a moving head.
3. **Regression comparison** — every future change is measured against what this baseline established.

## 2. Pinned normative corpus

Lower layers comply with higher layers; the Constitution prevails in any conflict (ADR-0001).

| Document | Version |
|---|---|
| [Engineering Constitution](ENGINEERING_CONSTITUTION.md) (nine Articles) | 1.0.1 |
| [Lexicon](../glossary/LEXICON.md) | 2.1.0 |
| [The ARGUS Ontology](../domain/ONTOLOGY.md) | 1.19.0 |
| [Domain Schema Specification](../domain/DOMAIN_SCHEMA_SPECIFICATION.md) | 1.6.0 |
| [Entity Lifecycles](../domain/ENTITY_LIFECYCLES.md) | 2.3.0 |
| [Derivation Specification](../domain/DERIVATION_SPECIFICATION.md) | 1.11.0 |
| [Invariant Matrix](../domain/INVARIANT_MATRIX.md) | 0.13.0 |
| [Constitutional Predicates](../domain/CONSTITUTIONAL_PREDICATES.md) | 0.11.0 |
| [ERD](../architecture/ERD.md) | 0.6.0 |
| [Case Reconstruction Specification](../domain/CASE_RECONSTRUCTION.md) | 0.1.0 |
| [Storage Reconciliation Specification](../domain/STORAGE_RECONCILIATION.md) | 0.1.0 |
| [Actor Context Specification](../domain/ACTOR_CONTEXT.md) | 0.1.0 |
| [Authority Specification](../domain/AUTHORITY.md) | 0.1.0 |
| [Case Presentation Specification](../domain/CASE_PRESENTATION.md) | 0.1.0 |
| [ODE-0001 — Ontology-Driven Engineering](../knowledge/research/ODE-0001-ontology-driven-engineering.md) (research ledger) | 0.24.0 |

**Architectural decision record:** ADRs **0001–0037** inclusive ([index](../adr/README.md)). ADR-0037 records the Session 023 program-completion decision and this baseline's authorization.

## 3. Pinned ontology content (Ontology 1.19.0)

- **Principles:** ONT-PRN-001 through ONT-PRN-031 — the complete stable-identifier registry; identifiers never change meaning and are never reused (ADR-0011).
- **First-class objects (15):** ONT-CAS-001 Case, ONT-EVA-001 EvidenceArtifact, ONT-SRC-001 SourceLocator, ONT-OBS-001 Observation, ONT-INT-001 Interpretation, ONT-HYP-001 Hypothesis, ONT-UNK-001 Unknown, ONT-UNL-001 UnknownLink, ONT-UNR-001 UnknownResolution, ONT-CON-001 Contradiction, ONT-CNM-001 ContradictionMember, ONT-CDP-001 ContradictionDisposition, ONT-ENT-001 Entity, ONT-REL-001 Relationship, ONT-AUD-001 AuditEntry.
- **The analytical ladder:** Reality → Evidence → Observation → Interpretation → Hypothesis → Understanding → Human Judgment; the last two rungs are never machine-represented. Roadmap completion authorized **no further epistemic objects** (AGC Session 013, reaffirmed Session 023).

## 4. Pinned experimental ledger (ODE-0001 0.24.0)

### Hypotheses — all Supported (n = 1); none proven

| ID | Claim (abbreviated; normative wording in ODE-0001) | Slice |
|---|---|---|
| H1 | Independent implementations from a common ontology converge on identical constitutional behavior | 1B |
| H2 | Independently derived *behavior* (predicates) converges without shared executable logic | 1C |
| H3 | Independent implementations of epistemic admissibility converge | 1D |
| H4 | Plural admissible Interpretations preserved without epistemic priority | 2A |
| H5 | Explicit epistemic boundaries preserved; absence never becomes evidence | 2B |
| H6 | Formally scoped joint incompatibility preserved without adjudication | 2C |
| H7 | Plural provisional explanations admitted without revision, promotion, refutation, or adjudication | 2D |
| H8 | The complete authorized epistemic graph composes into equivalent read models without privileged narrative | 3A |
| H9 | Integrity divergence classified without silent repair or converting agreement into truth (probe declared single-implementation) | 1E |
| H10 | Actor attribution derived from authenticated principal; caller-supplied identity refused (authentication declared single-implementation) | 1F-A |
| H11 | Resource-scoped capability authority governs actions and visibility, never epistemic standing (provider declared single-implementation) | 1F-B |
| H12 | A human review surface organizes without creating epistemic hierarchy (static conformance; renderer declared single-implementation) | 1F-C |

**Registered untested (Phase 4; no implementation authorized without a plan gate):** H13 (independent adapter replication — 4A), H14 (browser and assistive-technology conformance — 4B), H15 (adversarial and concurrency hardening — 4C), H16 (independent reimplementation study — 4D).

### Observations and principles

- **Promoted observations:** O1–O14 and O16 (notably: O8 alternating positive/boundary rhythm; O9 local guarantees do not automatically compose — supported across four composition surfaces: read-model composition, storage reconciliation, transport/transaction interaction, presentation; O10 infrastructure reuse reduces divergence; O11 fact/classification/judgment layering; O12 integration constraints as discovery instruments; O13 three-layer identity agreement; O14 projections vary while epistemic reality stays singular; O16 presentation is epistemically consequential even when operationally read-only).
- **Principle:** P1 — constraint-before-expression compounds architecturally (earlier rigor → reusable invariant → later integration cost falls).
- **Unpromoted candidate:** O15 (capabilities vs roles) — retained as candidate; promotion requires further evidence.

## 5. Pinned reference implementation state

- **Reference commit:** `fc2432d` (branch `claude/argus-project-foundation-bst1ck`) — the commit at which the final roadmap slice (1F-C) passed review.
- **Migration head:** `013_authority_decision` (Alembic migrations 001–013).
- **Reference test result:** **150 passed, 0 failed** against PostgreSQL 16 (constitutional suite including the `postgres` marker; dual-rendered conformance sweeps at zero divergences).
- **Trust anchor:** audit hash chain `chain_version = 1`, canonical serialization parity-proven between Python and PostgreSQL renderings.

## 6. Published limitations (publication mandatory)

### 6.1 Constitutional research questions — each requires research question → constitutional constraints → ontology decision → experimental hypothesis → gate before any implementation

1. No evidentiary sufficiency model.
2. No formal comparative assessment of explanations.
3. No calibrated confidence representation.
4. No AI provenance at the Hypothesis rung.
5. No end-user review workflow (binding caution: *reviewed ≠ believed, acknowledged ≠ accepted as true, approved for action ≠ epistemically correct, institutionally adopted ≠ reality established*).
6. No formal distinction yet between creation admissibility and later human endorsement or institutional adoption.

### 6.2 Operational gaps — buildable in Phase 4 without new epistemic meaning

1. Production identity-provider integration (DevTokenVerifier is the declared development-only verifier).
2. Persisted authority-grant administration (grants are currently provider-supplied facts, not persisted records).
3. MinIO ContentStore adapter (behind the ContentStore contract and conformance suite).
4. Browser and assistive-technology conformance (H12's evidence is static analysis of the rendered document, not a browser runtime).

### 6.3 Honest experimental bounds

Every "Supported" verdict is **n = 1** — evidence, not proof. Four surfaces are declared single-implementation (storage probing, authentication, authority-grant provider, HTML renderer): for these, triangulation covers the pure decision/classification logic, not the surface itself. Reconciliation classifies integrity, never truth (ONT-PRN-026). Detection never becomes decision or mutation (ONT-PRN-027).

### 6.4 Trust-boundary statements

- The audit hash chain is tamper-*evident within its trust boundary*: it detects modification through authorized database paths; it does not defend against an adversary with filesystem or superuser access to the database host (ADR-0016).
- Authority decisions bind facts supplied by the provider at decision time; the system does not verify the provider's own governance (H11 honest bound).
- Identity attribution is only as strong as the transport verifier; the constitutional guarantee is that identity is *authenticated, never asserted* (ONT-PRN-028), not that any particular verifier is unbreakable.
- Presentation conformance is verified against the reference surface's generated documents; a hostile or modified client can still render unconstitutionally — the guarantee covers what ARGUS emits, not what third parties display (H12 limitation).
- SEALED content is disclosed only after the access is durably audited; secrecy never leaks existence, and absence of access is never absence of evidence (ONT-PRN-030).

## 7. Deliberate absences (accomplishments, not gaps)

No guilt. No verdict. No accepted truth. No winning explanation. No confidence score. No machine-selected Case theory. No privileged narrative. No epistemic ranking anywhere in schema, API, or presentation. Understanding and Judgment remain human, outside the schema.

## 8. Supersession

Any future baseline must: (a) carry a new version number; (b) enumerate every pinned item that changed and the governance decision (ADR / Council session) authorizing each change; (c) leave this document intact apart from a superseded-by notice.
