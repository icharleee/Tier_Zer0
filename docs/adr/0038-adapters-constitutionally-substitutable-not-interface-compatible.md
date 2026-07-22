# ADR-0038: Adapters are constitutionally substitutable, never merely interface-compatible

- **Status:** Accepted (AGC Review Session 024 — Founder Resolution 027; freeze exemption per ONT-PRN-011: Phase 4's first governance decision, discovered necessary by the 4A direction review)
- **Date:** 2026-07-21
- **Constitutional articles:** V (Evidence is immutable), VII (Scientific integrity), IX (Certainty never exceeds evidence)
- **Ontology:** ONT-PRN-032 (Ontology 1.20.0 — the first post-baseline principle; [Baseline 1.0](../foundation/CONSTITUTIONAL_BASELINE_1.0.md) pins 1.19.0 and is not edited)

## Context

Session 024 accepted Constitutional Baseline 1.0 as the immutable reference and authorized detailed planning for workstream 4A. Phase 4 changes the scientific question: not *can the reference implementation derive disciplined behavior from the Constitution* but *can different infrastructure implementations enter through the same contracts without changing constitutional behavior*. The naive success criterion — the new adapter satisfies the programming interface — is exactly the criterion Phase 4 exists to reject: a collection of passing interface tests can still hide storage-semantics drift, identity-attribution drift, or permission-scope drift.

## Decision

1. **Founder Resolution 027 (ratified as ONT-PRN-032):** *An adapter is constitutionally substitutable only when replacing the reference implementation changes neither the meaning of normalized inputs and outputs nor the constitutional behavior derived from them. Interface compatibility alone is insufficient.* Corollary: *backend-specific facts must be normalized before they enter constitutional derivations; backend-specific failure semantics may never silently redefine constitutional states.*

2. **One adapter per gate — a single combined 4A gate is REJECTED.** The three adapters replace different trust boundaries with different primary risks (MinIO — storage-semantics drift; production verifier — identity-attribution drift; persisted grants — permission-and-scope drift); combining them would leave any H13 result causally uninterpretable. Required order:
   - **4A-1 — MinIO ContentStore Replication** (protocol and conformance suite already exist; narrowest semantics; the designated **O11 repeat test**),
   - **4A-2 — Production PrincipalVerifier Replication** (provider-neutral until a provider is selected; normalizes external claims into the existing closed principal model; must not introduce authority into `AuthenticatedPrincipal`),
   - **4A-3 — Persisted Authority-Grant Replication** (the most constitutionally sensitive: durable security-significant state; must feed the existing `authorize()` derivation, never become a second decision engine; the designated **O15 repeat test**).

3. **H13 is the umbrella hypothesis with cumulative per-adapter evidence** (H13-S1 storage, H13-S2 identity, H13-S3 authority), refined so it cannot collapse into interface compatibility: *independently implemented infrastructure adapters can replace reference development implementations while preserving the applicable constitutional observations, derived states, refusal behavior, non-effects, visibility semantics, and epistemic neutrality defined by Baseline 1.0.* Results are reported per adapter as they complete — a failure in one must not obscure success in another.

4. **H13 failure taxonomy (binding on every adapter gate):**
   1. *Contract failure* — the adapter violates an explicit protocol obligation.
   2. *Conformance-suite insufficiency* — the adapter passes the existing contract suite but system behavior diverges from Baseline 1.0. The most scientifically valuable failure: the contract was incomplete. Response: adapter reveals missing invariant → governance reviews → contract and conformance suite strengthened → **both** implementations retested. Never special-case the new adapter, and never erase the failure from the research history — preserve the failing fixture, the pre-amendment result, the authorizing ADR, and the rerun.
   3. *Environmental divergence* — the adapter is correct but the environment cannot provide equivalent semantics. This may render the backend constitutionally unsuitable; ARGUS does not weaken a contract because a popular service cannot satisfy it.
   4. *Constitutional divergence* — every API call "works" but a constitutional distinction collapses (authentication implying authority; verification labeled authenticity; roles replacing exact capabilities; denied visibility surfacing as missing evidence). An H13 failure regardless of green tests.

5. **Three required test layers per adapter:** (A) adapter contract conformance; (B) reference/replica differential tests — the same fixtures through both adapters with normalized-output comparison, where only explicitly non-constitutional environmental values (request IDs, backend ETags unused constitutionally, timing, hostnames) may be excluded, and everything else is classified before exclusion; (C) full constitutional regression — the Baseline 1.0 suite remains green around the new adapter. Layer A alone never accepts an adapter.

6. **Scope caution:** adapter gates test adapter semantics; deployment packaging (compose files, networking, credentials, provisioning, monitoring) must not dominate the experiment.

## Governance review

1. **Constitutional Review** — PASS: the resolution extends Article V and IX discipline to infrastructure substitution — a backend's failure vocabulary cannot quietly redefine what ARGUS claims to know.
2. **Domain Review** — PASS: ONT-PRN-032 constrains implementation substitution; it adds no epistemic object and changes no existing meaning.
3. **Architectural Review** — PASS: the layered test structure reuses existing contracts and the pinned baseline as fixed comparators; the failure taxonomy makes a mixed result (reuse reduced divergence in X; adapter revealed missing constraint Y) reportable as a legitimate outcome.

## Consequences

- Each 4A sub-gate requires its own plan, threat model, conformance matrix, H13 evidence record, and implementation verdict before any code (ONT-PRN-024).
- Every adapter completion report carries the full evidence package: implementation, protocol conformance, differential result, full regression, newly discovered failure classes, contract amendments if any, remaining provider-specific limitations, and H13/observation evidence status.
- A green run and a discovered contract deficiency are equally legitimate scientific outcomes — provided neither moves Baseline 1.0.

## Alternatives considered

- **One combined 4A gate** — rejected by the Council: too many causal variables; Phase 4 must increase independence, not decrease interpretability.
- **Interface compatibility as the acceptance criterion** — rejected: necessary, never sufficient (the resolution's core).

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

**Affected Articles:** V, VII, IX. Others untouched.

**Compliant?** YES

**Explanation:** A new adapter has not replicated ARGUS merely because it fits the same interface. It has replicated ARGUS only when replacing the reference adapter leaves constitutional behavior unchanged.
