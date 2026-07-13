# ADR-0006: ARGUS Core v0.1 Technology Stack

- **Status:** Accepted
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), II (Human judgment is final), III (Conclusions explain themselves), V (Evidence is immutable), VII (Scientific integrity before convenience), VIII (Transparency), IX (Certainty never exceeds evidence)
- **Supersedes:** none

## Context

ADR-0001 through ADR-0005 established the governance layers and the domain doctrine: an analytical ladder that must never collapse (ADR-0002), append-only evidence with retraction (ADR-0003), provenance enforced at the persistence boundary (ADR-0004), and durable, human-resolved Unknowns and Contradictions (ADR-0005). None of those documents selected an implementation technology, deliberately: doctrine is enduring, tools are replaceable.

Implementation cannot begin without tools. This ADR selects the initial stack for ARGUS Core v0.1 — a prototype built by a small founding team — while keeping the conceptual model independent of it. The Domain Schema Specification (queued next, `docs/domain/DOMAIN_SCHEMA_SPECIFICATION.md`) will define *what* must be represented; this ADR decides *what represents it* for v0.1.

Two structural facts drive the selection more than any feature comparison:

1. **The constitutional rules are enforced at the persistence boundary** (ADR-0003, ADR-0004). Whatever owns transactions and schema constraints owns the Constitution's enforcement. That authority must be clearly and singly located.
2. **ARGUS's analytical machinery is Python-shaped.** AI integration, provenance-threaded pipelines, and future data-science work will be Python. Placing domain authority elsewhere would split the rules engine from the analysis it governs.

## Decision drivers

- **Transactional integrity** — retraction-and-replacement, audit writes, and provenance checks must be atomic.
- **Single authoritative domain model** — ARGUS shall have one authoritative domain model, implemented in Python, with critical persistence invariants independently reinforced by PostgreSQL. Client applications may mirror contracts for usability but may not become independent sources of domain truth.
- **Provenance enforcement** — the stack must make "no provenance, no claim" enforceable in schema and transaction code, not UI.
- **Auditability** — boring, widely understood, externally verifiable technology serves Article VIII better than novel technology.
- **Domain-model clarity** — the fourteen first-class entities must map onto the persistence layer without contortion.
- **Testability** — constitutional tests are release-blocking (Constitution, Enforcement §3); the stack must make them cheap to write.
- **Reversibility** — every choice here should be replaceable without rewriting doctrine.
- **Founding-team resource limits** — a small team; mainstream, well-documented tools; minimal operational surface.

## Decision

We will build ARGUS Core v0.1 on the following stack:

| Layer | Decision |
|---|---|
| Web application | Next.js with TypeScript |
| API and authoritative domain layer | Python with FastAPI |
| Python runtime policy | Primary runtime: Python 3.13. Compatibility target: Python 3.14, evaluated in CI. Minimum supported version: Python 3.13. Exact patch version locked in `.python-version`, container images, and CI. |
| Domain/API validation | Pydantic v2 |
| Operational database (system of record) | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Client-boundary validation | OpenAPI-generated TypeScript contracts, with Zod schemas generated or maintained only at genuine external-input boundaries. The exact generation tool is deferred to Task 001 after compatibility evaluation. |
| Object storage | S3-compatible abstraction; MinIO locally |
| Local infrastructure | Docker Compose |
| Backend testing | pytest |
| Frontend testing | Vitest |
| Python dependency management | uv |
| JavaScript package management | pnpm |
| Continuous integration | GitHub Actions |
| Repository layout | Monorepo (structure below) |
| Production deployment | **Explicitly deferred** |

**Authority boundaries (normative):**

1. **PostgreSQL is the v0.1 operational system of record.** All first-class entities, their lifecycles, and their audit history live in PostgreSQL under transactional guarantees.
2. **ARGUS has one authoritative domain model, implemented in Python (FastAPI + SQLAlchemy).** The Python domain layer is authoritative for meaning, business rules, and permitted transitions. PostgreSQL independently reinforces critical persisted invariants — least-privilege roles, constraints, triggers, and controlled functions — as the final integrity boundary, not as a second business-rules engine.
3. **TypeScript and Zod validate client contracts only.** They may reject malformed input early and improve UX; they must never encode a rule that the Python layer does not also enforce, and they must never be the *only* place a rule exists. The frontend is a client of the Constitution, not an enforcer of it.
4. **Neo4j is deferred.** It may later serve as a read-only graph *projection* for analytical traversal, introduced by its own ADR only after a demonstrated workload PostgreSQL cannot serve. It is never the v0.1 source of truth.
5. **Object-storage providers remain replaceable.** Evidence artifacts are identified by content hash and internal ID (per ADR-0003), never solely by a provider URI. The storage interface is S3-compatible; MinIO is an implementation detail of local development.

**Immutability classes (normative):**

"Evidence is immutable" (Article V) does not mean every database field is permanently frozen. It means substantive source truth cannot be silently rewritten. The schema distinguishes three classes, with enforcement specified per table in the Domain Invariant Matrix:

- **Content-immutable** — evidence bytes, the original cryptographic hash, the original ingestion record, audit events.
- **Versioned rather than overwritten** — observations, interpretations, hypotheses, contradiction descriptions, unknown questions (per ADR-0003's retraction-and-replacement pattern).
- **Mutable under controlled transitions** — assignment, review status, access classification, processing state, and operational metadata that does not alter source truth. Every such transition is authorized and audited.

## Component-by-component rationale

**Next.js + TypeScript (web).** The investigator-facing surface must present the analytical ladder, retraction history, unknowns, and contradictions honestly — a substantial, stateful UI. Next.js is mainstream, well-documented, and hires easily; TypeScript lets generated API contracts keep the client synchronized with the Pydantic models rather than hand-maintained.

**FastAPI + Pydantic (domain and API).** FastAPI keeps the domain layer in Python (decision driver: single authoritative domain model, adjacency to AI/data-science work) with a thin framework footprint: explicit request/response models, OpenAPI generation that feeds the TypeScript contract types, and dependency injection as the mechanism through which authorization services are invoked. Dependency injection is not itself the authorization control: actual authorization rests on authenticated identity, policy evaluation, and persistence-layer safeguards (Articles II, VI). Pydantic v2 gives the domain layer strict, typed validation where provenance preconditions (ADR-0004) are naturally expressed as required, non-defaultable fields.

**PostgreSQL (system of record).** ACID transactions make retraction-and-replacement plus audit-entry emission atomic. Referential integrity enforces the ladder's layer-by-layer references (ADR-0002). Least-privilege roles, triggers, and controlled database functions let ADR-0003's "at the database layer, not just service code" requirement be met literally, per table and per immutability class. Recursive CTEs and relationship tables serve the early evidence graph.

**SQLAlchemy 2.x + Alembic (persistence and migrations).** SQLAlchemy keeps transaction and persistence authority in the same Python process that owns the domain model — one authoritative model, one language. Its Core layer expresses PostgreSQL-specific enforcement (partial indexes, check constraints, restricted table privileges) that ORM-portability-focused tools abstract away. The project uses the SQLAlchemy 2.x execution and typing model consistently; legacy 1.x patterns are not mixed in. Alembic makes every schema change a reviewable, versioned migration — the schema's own audit history.

**OpenAPI-generated TS contracts + Zod at external boundaries (client).** API contract types are generated from the OpenAPI schema, so the client contract has one source of truth (Pydantic). Zod schemas exist only at genuine external-input boundaries (form entry, file metadata) — generated where tooling supports it reliably, hand-maintained where it does not. OpenAPI-generated TypeScript interfaces do not automatically provide runtime Zod schemas, and the generation pipeline must be proven before it is depended on; the exact tool is selected in Task 001 after compatibility evaluation. This layer is ergonomics, not authority — see normative boundary 3.

**S3 abstraction + MinIO (evidence blobs).** Evidence artifacts are large binaries (video, images, device dumps); they belong in object storage, with PostgreSQL holding the authoritative record: content hash, ingest metadata, provenance, retraction state. The interface is S3-compatible because it is the de facto standard with many independent implementations — maximal provider replaceability. MinIO gives local development and CI a faithful implementation without cloud dependency.

**Docker Compose (local infrastructure).** One command brings up PostgreSQL, MinIO, API, and web app identically for every contributor and CI. No orchestration platform is needed for v0.1.

**pytest / Vitest (testing).** Both are their ecosystems' defaults. Constitutional tests — immutability, provenance rejection, human-only transitions, audit coverage — will live in pytest against a real PostgreSQL instance (via Compose), because testing database-level enforcement against SQLite fakes would test nothing constitutional.

**uv / pnpm (dependency management).** Both produce strict lockfiles (reproducibility, Article VII) and are fast. uv additionally covers Python version management, environments, resolution, and workspace operations in one tool, reducing toolchain surface for a small team. Both choices are made for reproducibility and reduced maintenance burden, and both are cheaply reversible.

**GitHub Actions (CI).** The repository is on GitHub; Actions runs the Compose stack, both test suites, and constitutional test gates without extra vendor surface. Release-blocking constitutional tests become required status checks.

**Monorepo.** Initial structure:

```
apps/
  web/            # Next.js
  api/            # FastAPI + domain layer
packages/
  contracts/      # generated TS contract types, boundary Zod schemas
docs/
  foundation/     # brief, constitution
  adr/            # this record
  architecture/   # ERD, invariant matrix (queued)
  domain/         # Domain Schema Specification (queued)
tests/
  constitutional/ # cross-cutting constitutional test assets
  fixtures/       # shared test fixtures
```

A monorepo is adopted because the client contract (`packages/contracts`) must change in lockstep with the Pydantic models that generate it; separate repositories would let them drift, and drift between what the API enforces and what the client believes is an epistemic-integrity defect, not an inconvenience. One repo also means one governance chain — AGENTS.md and the Constitution govern every change without duplication. A `packages/ui` package is deliberately **not** pre-created; it is added only when a genuine second consumer or a critical mass of shared components justifies the package boundary. This structure may be refined by later ADRs without constitutional implications.

## Alternatives considered

**FastAPI vs. Django.** Django brings an admin, its own ORM, and batteries that assume conventional CRUD. ARGUS is explicitly not a CRUD application: Django's admin is an unaudited mutation surface that would have to be disabled or heavily fenced (Articles V, VIII), and the Django ORM abstracts away the PostgreSQL-specific enforcement ADR-0003 requires. FastAPI's smaller footprint means fewer default behaviors to constitutionally audit. *Rejected: Django.*

**SQLAlchemy vs. Prisma.** Prisma would place schema definition and persistence access in TypeScript while the authoritative domain model lives in Python — two languages sharing authority over one database. Every invariant would either be duplicated (drift) or enforced in only one place (gap). Persistence and transaction authority belong with the Python domain layer. Prisma's migration system also resists the hand-written, database-level privilege and trigger work that evidence immutability requires. *Rejected: Prisma.*

**PostgreSQL-only vs. PostgreSQL + Neo4j from the start.** Neo4j's traversal strengths are real, but adopting it now means dual-write consistency problems on day one — and an inconsistency between two sources of truth is precisely the kind of silent reality-distortion the Prime Directive forbids. PostgreSQL's recursive queries and relationship tables serve v0.1's graph needs. **Deferred note (normative): Neo4j is a potential analytical *projection*, not the initial source of truth.** Its introduction requires a demonstrated workload PostgreSQL cannot serve and its own ADR defining projection consistency semantics. *Rejected for v0.1: Neo4j.*

**MinIO/S3 abstraction vs. evidence blobs in PostgreSQL.** Storing blobs in PostgreSQL gives single-store transactional simplicity, and was seriously considered for that reason. It was rejected because evidence media at investigative scale (video, device images) would dominate the operational database, degrading backup/restore and the transactional path that enforces the Constitution. Instead, the authoritative *record* (hash, metadata, provenance) is transactional in PostgreSQL, and the blob is content-addressed in object storage; integrity is verified against the hash, not trusted to the store. *Rejected: blobs in PostgreSQL.*

**Monorepo vs. separate repositories.** See rationale above; separate repos were rejected because contract drift between client and domain layer is an integrity defect, and multi-repo governance would fragment the constitutional chain of authority. *Rejected: polyrepo.*

**pnpm vs. npm.** npm is the default but has a looser store model and slower installs; pnpm's content-addressed store gives stricter, reproducible dependency trees. Low-stakes, easily reversed. *Rejected: npm.*

**uv vs. Poetry.** Poetry is mature but slower, and its resolver and packaging behaviors have historically required workarounds. uv is a single tool covering version management, environments, resolution, and lockfiles — chosen for reproducibility and reduced toolchain surface. Low-stakes, easily reversed. *Rejected: Poetry.*

## Constitutional alignment

- **Article I / ADR-0004:** Pydantic required fields + PostgreSQL non-nullable references make ungrounded claims unrepresentable at both validation and persistence layers.
- **Article II / ADR-0005:** Authorization for human-only transitions rests on authenticated identity and policy evaluation invoked through FastAPI's dependency mechanism; PostgreSQL constraints on resolving-actor columns reinforce them.
- **Article V / ADR-0003:** Immutable records and append-only ledgers are protected with least-privilege database roles, restricted repository interfaces, and PostgreSQL triggers or controlled database functions where appropriate, specified per table in the Domain Invariant Matrix and versioned through Alembic.
- **Article VII:** Lockfiles (uv, pnpm), a pinned Python runtime policy, pinned Docker images, and Alembic migrations make environments and schema history reproducible.
- **Article VIII:** A boring, ubiquitous stack (PostgreSQL, Python, TypeScript) is auditable by external experts without specialized knowledge; the schema's evolution is itself a readable record.
- **Article IX:** No component in this stack stores or transports analytical content in a way that forces uncertainty to collapse; uncertainty representation is a Domain Schema Specification concern this stack does not constrain.
- **No stack choice weakens** evidence immutability, provenance, auditability, or human-only resolution — the authority boundaries above exist to keep it that way.

## Positive consequences

- One authoritative domain model in one language, with the database as an independent final integrity boundary — no split-brain rule authority.
- Constitutional invariants are testable against the real database in CI.
- Client contracts are generated, not hand-synchronized.
- Every component is mainstream: documentation, hiring, and external audit are all easy.
- Local development is fully self-contained (Compose + MinIO); no cloud account required to contribute.

## Negative consequences and costs

- **Two languages.** The team maintains Python and TypeScript toolchains, and the contract-generation pipeline between them is build infrastructure that must be kept working.
- **No graph-native traversal.** Deep relationship queries will be recursive SQL, which is verbose and will eventually hit expressive/performance limits — that pain is the intended trigger for the Neo4j-projection ADR.
- **Object storage split.** Evidence integrity spans two stores (record in PostgreSQL, blob in S3); ingestion consistency is a first-order design problem, addressed by its own ADR (see Risks and Deferred decisions).
- **FastAPI's minimalism** means auth, audit middleware, and conventions are built by us rather than inherited — more early work than Django would demand.
- **Per-table enforcement specification.** Distinguishing immutability classes per table requires the Domain Invariant Matrix to be produced and maintained; blanket rules would have been cheaper and wrong.

## Risks

- **Client-side rule creep.** The most likely long-term violation: Zod schemas gradually accumulating business rules. Mitigation: AGENTS.md rule, code review against normative boundary 3, and periodic contract audits.
- **ORM abstraction leakage.** Developers using SQLAlchemy ORM conveniences (e.g., object deletion, cascade updates) that bypass append-only doctrine. Mitigation: database-level privileges make these fail loudly; constitutional tests assert they fail.
- **Contract-generation drift.** If the OpenAPI→TS pipeline breaks and someone hand-patches types, the contract silently forks. Mitigation: CI regenerates and diffs; a dirty diff fails the build. (Tool selection deferred to Task 001; this mitigation is tool-independent.)
- **Dual-store ingestion inconsistency** (stored content without a database record, or a record without verified content). Mitigation: define a separate Evidence Ingestion Protocol ADR (ADR-0007 — Evidence Ingestion and Atomic Finalization) specifying staging, transaction boundaries, failure recovery, orphan detection, content verification, and artifact-finalization semantics. No artifact becomes ACTIVE until both its database record and stored content have passed integrity verification. This ADR establishes that dual-store consistency is a risk; it deliberately does not settle the protocol.
- **Legal-compliance overreach.** Retention, sealing, expungement, and discovery obligations vary by jurisdiction; nothing in this stack, and nothing in ADR-0003, constitutes universal legal compliance. Implementation must preserve the distinctions between evidence integrity, user-facing visibility, legal sealing, restricted access, cryptographic destruction, and legally required deletion — and must not claim compliance without jurisdiction-specific legal review. Carried as a standing flag into the Domain Schema Specification and all evidence-lifecycle work.

## Deferred decisions

Explicitly out of scope for v0.1; each requires its own ADR when taken up:

- **ADR-0007 — Evidence Ingestion and Atomic Finalization** (staging, transaction boundaries, failure recovery, orphan detection, content verification, finalization semantics)
- Production cloud / deployment provider
- Authentication and identity provider
- LLM provider(s) and AI-integration architecture (must satisfy ADR-0004's provenance fields)
- Vector database / semantic search
- Observability vendor
- Neo4j or any graph projection (see deferred note above)
- Jurisdiction-specific legal-compliance mechanisms (sealing, expungement, retention schedules)
- TypeScript contract/Zod generation tooling (evaluated and selected in Task 001)

## Migration and reversibility considerations

- **Frontend framework:** replaceable; the generated-contract boundary means the API neither knows nor cares what renders it. Cost: UI rewrite only.
- **FastAPI:** replaceable within Python (domain logic lives in plain Python modules, not route handlers, precisely to keep this cheap). Cost: routing/DI layer rewrite.
- **Python runtime:** 3.14 compatibility is evaluated continuously in CI, so the primary runtime can advance deliberately rather than under duress.
- **SQLAlchemy:** moderately expensive to replace but contained to the persistence package; domain rules must not import ORM types outside it.
- **PostgreSQL:** the most expensive reversal, accepted deliberately — the system of record *should* be the stickiest component. Alembic history plus standard SQL keeps exit possible.
- **MinIO/S3 provider:** cheap by design — content addressing means re-homing blobs is a copy plus hash verification.
- **uv/pnpm/Vitest/Actions:** trivially replaceable.

## Validation criteria

This ADR is validated when the following are demonstrated in CI on the scaffold (Task 001) and domain implementation (Task 002):

1. A Compose stack boots PostgreSQL, MinIO, API, and web app from a clean clone with one command.
2. A pytest suite, running against real PostgreSQL, proves: unauthorized mutation or physical deletion of constitutionally immutable records fails at the database layer, while approved lifecycle transitions occur through explicitly authorized, audited paths; an analytical write without provenance fields is rejected; a contradiction resolution without an authenticated human actor is rejected; and every material domain mutation produces an `AuditEntry` atomically within the same PostgreSQL transaction as the state change. ("Material domain mutation" is enumerated in the Domain Invariant Matrix; health checks, ephemeral sessions, caches, and technical telemetry are excluded.)
3. TypeScript contract types are generated from the OpenAPI schema in CI, and a hand-edited drift fails the build.
4. An ingestion interrupted between content storage and record commit produces a detectable, surfaced anomaly rather than silent inconsistency (protocol per ADR-0007).
5. No business rule exists in the frontend that is absent from the Python domain layer (audited by review checklist).

## Ratification

Decision: ADR-0006 is accepted as the initial technology architecture of ARGUS Core v0.1. Its choices are implementation decisions rather than domain doctrine and may be superseded through subsequent ADRs. No component selected here is authorized to weaken the Engineering Constitution, collapse the analytical ladder, obscure uncertainty, permit unsupported claims, or transfer consequential judgment from authenticated humans to machines.
