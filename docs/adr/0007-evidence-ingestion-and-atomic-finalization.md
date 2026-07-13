# ADR-0007: Evidence Ingestion and Atomic Finalization

- **Status:** Accepted — amended and ratified by AGC Review Session 004 (number reserved by ADR-0006; drafted after ADR-0015 as the gate to Slice 1)
- **Date:** 2026-07-13
- **Constitutional articles:** I (Evidence before opinion), V (Evidence is immutable), VII (Scientific integrity), VIII (Transparency)
- **Ontology rules:** ONT-EVA-001, ONT-AUD-001, ONT-PRN-005, ONT-PRN-006
- **Supersedes:** none (fulfills the deferral recorded in ADR-0006)

## Context

Evidence integrity spans two stores: the authoritative record in PostgreSQL and the content bytes in object storage. ADR-0006 named the dual-store inconsistency risk and deliberately deferred the protocol; ADR-0015 makes this the last decision gating Slice 1, whose constitutional loop *is* this protocol: upload → hash verification → EvidenceArtifact record → audit event → visible in UI. The protocol must guarantee that no artifact becomes analytically visible unless its record and its stored content have both passed integrity verification, and that every failure mode leaves surfaced evidence rather than silent inconsistency.

## Decision

### 1. Ordering principle: bytes, then record, then activation

Content is staged **before** the record exists; the record is created **before** activation; activation happens **only after** verification. Rationale: a record without bytes would be a claim without evidence (Article I), while staged bytes without a record are *pre-constitutional material* — invisible to analysis and swept by reconciliation. Errors on this ordering fail safe in the direction of "evidence exists but is not yet claimable," never "claim exists without evidence."

### 2. The explicit lifecycle (Session 004, Amendment 1)

```
STAGED                    (pre-constitutional: bytes exist; nothing else is guaranteed —
   ↓                       no ontology, no provenance, no claims; tracked by ingestion session)
PENDING_VERIFICATION      (constitutional: record exists, hash exists, verification running,
   ↓                       still analytically unavailable)
ACTIVE                    (constitutional and claimable)
   ↓
QUARANTINED               (integrity issue; unknown disposition; human required)
RETRACTED                 (superseded by human decision)
SEALED                    (legally restricted; existence visible, content access audited)
```

`STAGED` and `PENDING_VERIFICATION` are **different worlds**: staging is physical reality without constitutional standing; pending verification is a constitutional record awaiting availability. `QUARANTINED` is reachable from `PENDING_VERIFICATION` (verification failure) and from `ACTIVE` (integrity failure detected later, e.g. a read-time hash mismatch); disposition out of quarantine is human-only. Authoritative state tables: [Entity Lifecycles §2](../domain/ENTITY_LIFECYCLES.md).

### 3. The protocol

**Step 1 — Staging (`STAGED`).** An authorized actor (HumanActor, or SystemProcess pipeline attributing its human authority) opens an ingestion session and streams content to a **staging area** keyed by session ID. The system computes the cryptographic hash *while receiving the bytes* — the hash of record is always system-computed, never client-declared (a client-declared hash MAY be accepted for comparison and mismatch warning only).

**Step 2 — Record creation (transaction T1).** One atomic transaction creates the `EvidenceArtifact` in `PENDING_VERIFICATION` — with the system-computed hash, size, media type, acquisition description, ingesting actor and human authority, and a staging reference — together with its `artifact-ingested` AuditEntry (D-AUD). Pre-`ACTIVE` records are invisible to analysis; no SourceLocator can reference them (Lifecycles §2).

**Step 3 — Verification and promotion (SystemProcess, idempotent).** The verifier re-reads the staged bytes, recomputes the hash, and compares it to the recorded hash. On match, it copies the content to the **permanent content-addressed location** (keyed by hash) and read-back-verifies the permanent copy.

**Step 4 — Activation (transaction T2).** One atomic transaction transitions `PENDING_VERIFICATION → ACTIVE`, updates the storage reference to the permanent location, and writes the `artifact-activated` AuditEntry. Only now does the artifact exist analytically. The staging copy is then released — a mechanical cleanup permitted because staging is pre-constitutional; the preserved truth is the record plus the verified permanent copy.

**Step 5 — Failure path (`QUARANTINED`).** On any mismatch or corruption, one atomic transaction transitions the record to `QUARANTINED` with the `artifact-quarantined` AuditEntry; the staged bytes are **retained in quarantine, not deleted**, pending human disposition. The record persists — nothing disappears (ONT-PRN-006), including failed ingestions.

### 4. Recovery and reconciliation

- **Idempotence.** Verification and promotion are safely re-runnable after a crash at any point; content-addressed storage makes double-promotion a no-op.
- **Stalled ingestions.** A `PENDING` record older than a configured threshold is surfaced as an anomaly for human disposition — never auto-deleted, never auto-activated.
- **Reconciliation (scheduled SystemProcess).** A two-way sweep: permanent-store content without a record becomes a surfaced anomaly with its own AuditEntry (never silently deleted); a record whose content is missing or hash-divergent is flagged and surfaced. Reconciliation repairs nothing on its own — it detects and reports (Article II: disposition is human).

### 5. Hash policy

Initial algorithm: **SHA-256**, recorded per artifact as `algorithm + digest`. The original hash is content-immutable forever (ONT-EVA-001). Algorithm migration is **additive**: a stronger hash may be computed and recorded alongside the original, which is never replaced or recomputed. Content reads verify against the recorded hash; a mismatch is surfaced, never silently served.

### 6. Finalization invariant (normative)

> No `EvidenceArtifact` becomes `ACTIVE` until its database record and its permanently stored content have both passed integrity verification, atomically recorded with an AuditEntry.

This is the invariant Slice 1's constitutional loop must prove, and the first row group of the Invariant Matrix (Case + EvidenceArtifact + AuditEntry) instantiates it.

### 7. Founder Resolution 007 (Session 004, Amendment 2)

> **Every constitutional transition is explicit.**
> No invisible state changes. No automatic promotion. No hidden lifecycle movement.

Every transition corresponds to: an audit event; a responsible actor; a timestamp; **an allowed predecessor state**. If something becomes `ACTIVE`, there is an event. If something becomes `RETRACTED`, there is an event. If verification succeeds, there is an event. Everything. The lifecycle tables in [Entity Lifecycles](../domain/ENTITY_LIFECYCLES.md) are the authoritative allowed-predecessor registry, and implementations MUST encode transitions as named operations — never as bare status-field writes. The principle receives stable identifier **ONT-PRN-012**.

### 8. Deferred concepts (Session 004, Amendment 3)

- **OperationalAnomaly** is reserved as a future domain object — operational truth, distinct from investigation objects: missing blob, missing record, hash mismatch, failed activation, broken audit chain, storage unavailable, clock skew, duplicate upload. **Not implemented in Slice 1**; until then, reconciliation findings are surfaced through audit events and flags as specified above.
- **Constitutional Coverage** is adopted as a permanent engineering metric: alongside code coverage, CI reports per-article test coverage (every constitutional article eventually has explicit tests, mapped via ONT identifiers per ADR-0010). Slice 1 introduces the reporting skeleton; a Verification Standard formalizes it later.
- **Provenance Engineering** is recorded as a third research discipline (see the research corpus): the engineering discipline concerned with preserving the traceability, integrity, reproducibility, and auditability of information across its complete lifecycle.

### 9. Slice 1 designation and acceptance test (Session 004, Amendment 4)

Slice 1 (named "Evidence Ingestion" in ADR-0015) is renamed **Constitutional Evidence Activation** — the upload is not the feature; activation is. The loop: Upload → `STAGED` → hash computed → record created → verification → `ACTIVE` → **Observation-eligible**. Observation itself cannot exist yet.

The first acceptance test of ARGUS:

> **Given a synthetic image, can ARGUS ingest it, compute its identity, verify its integrity, activate it, emit every required audit event, and make it eligible for Observation creation — without violating a single constitutional invariant?**

If that passes, the Constitution has survived contact with code.

## Governance review

1. **Constitutional Review** — **PASS** (Session 004): the system can never produce a claim without evidence — even with bytes present, upload succeeded, and PostgreSQL committed, the artifact is not constitutionally usable until activation completes.
2. **Domain Review** — **PASS** (Session 004), recording the permanent engineering maxim: *"Evidence exists but is not yet claimable"* — the separation of physical reality from constitutional availability.
3. **Architectural Review** — **PASS with two modifications** (Session 004), both applied: the explicit six-state lifecycle (§2) and the reserved OperationalAnomaly concept (§8).

Session 004 further verdicts: Research Review — PASS, recording Provenance Engineering as a third discipline (§8); Standards Review — PASS, additive hash policy confirmed unchanged.

## Consequences

- Slice 1 has a complete, testable specification: T1/T2 atomicity, idempotent verification, quarantine, timeout surfacing, and two-way reconciliation are each a required test citing ONT-EVA-001.
- Storage carries staging + permanent copies transiently, and quarantined failures indefinitely — the price of never deleting evidence-shaped bytes.
- Client-declared hashes are demoted to advisory, which means ingestion integrity does not depend on client honesty.
- The additive hash policy commits us to multi-hash schema support from the start.

## Alternatives considered

- **Record first, bytes second** — rejected: creates windows where a constitutional record references content that never arrives; fails unsafe toward claim-without-evidence (Article I).
- **Single transaction spanning database and object store** — rejected: distributed transactions across PostgreSQL and S3-compatible stores are unreliable fictions; the protocol achieves the same guarantee with two local atomic transactions plus an idempotent verifier and reconciliation.
- **Trusting client-computed hashes** — rejected: the hash anchors evidence integrity (Article V); it must be computed by the system that stores the bytes.
- **Auto-deleting orphaned staging/quarantine content** — rejected: bytes that might be evidence are never silently destroyed; disposition is human (Article II).

## Constitutional Checklist

- [x] Article I — Evidence before opinion
- [x] Article II — Human judgment is final
- [x] Article III — Every analytical conclusion must explain itself
- [x] Article IV — Alternative explanations must always remain possible
- [x] Article V — Evidence is immutable
- [x] Article VI — Privacy and legal authority must be respected
- [x] Article VII — Scientific integrity before convenience
- [x] Article VIII — Justice requires transparency
- [x] Article IX — Certainty must never exceed the evidence

**Affected Articles:** I, V, VIII (all reinforced by the ordering principle, immutable hash anchoring, and per-step auditing); II (respected: all failure dispositions are human); VI (respected: ingestion attributes human authority). III, IV, IX untouched — no analytical semantics here.

**Compliant?** YES

**Explanation:** The protocol makes the dual-store guarantee concrete without weakening any invariant: every path either ends in a verified, audited, active artifact or in surfaced, preserved, human-disposable evidence of failure. Nothing disappears on any path.
