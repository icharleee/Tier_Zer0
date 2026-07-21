# ADR-0037: Phase 4 — Constitutional hardening and replication

- **Status:** Accepted (AGC Review Session 023 — the program-completion decision; freeze exemption per ONT-PRN-011: a phase transition, like ADR-0015, is an architecturally significant program decision)
- **Date:** 2026-07-13
- **Constitutional articles:** VII (Scientific integrity), IX (Certainty never exceeds evidence) — applied to the program itself
- **Supersedes:** none (succeeds the ADR-0015 slice program upon its completion; ADR-0015 remains the record of how the roadmap was executed)

## Context

The original slice roadmap is complete: 1A–1F (with the Session 017 A/B/C decomposition), 2A–2D, and 3A. The full authorized constitutional path exists and is verified — evidence persistence → Observation → Interpretation → Unknown and Contradiction boundaries → Hypothesis → Case composition → storage reconciliation → authenticated identity → authority and visibility → human presentation — with H1–H12 each Supported at n = 1 after review, 150 tests against PostgreSQL 16, and the deliberate absences intact: no guilt, no verdict, no accepted truth, no winning explanation, no confidence score, no machine-selected Case theory, no privileged narrative. That absence remains one of the program's primary accomplishments.

Roadmap completion is not authorization to build what was deliberately deferred. Several published gaps exist precisely because ARGUS has not yet established that they can be added safely.

## Decision

1. **The program phase changes** from *ontology and constitutional construction* to **constitutional hardening and replication**. The phase's purpose: *demonstrate that ARGUS's constitutional behavior survives changes in infrastructure, implementation team, runtime environment, concurrency, and presentation technology.* The phase contains **no new epistemic objects by default**; roadmap completion authorizes none.

2. **Four workstreams** (hypotheses H13–H16, registered in ODE-0001 0.24.0):
   - **4A — Independent Adapter Replication** (H13): MinIO ContentStore, production identity provider, persisted authority-grant provider — each entering through an existing protocol and conformance suite, with no ontology change required.
   - **4B — Browser and Assistive-Technology Conformance** (H14): the H12 checklist repeated through a real browser runtime, testing the reference surface rather than redesigning it.
   - **4C — Adversarial and Concurrency Hardening** (H15): systematic attack on the integration boundaries where the program already found failures; the goal is *constitutional* resilience — under failure, surface uncertainty and degradation rather than silently normalize, repair, omit, or infer.
   - **4D — Independent Reimplementation Study** (H16): a second team, given only the normative corpus (never the reference implementation), tested for material behavioral convergence — the experiment most capable of validating ODE beyond a disciplined internal method.

3. **The published gaps are formally split:**
   - **Operational gaps appropriate for Phase 4** (buildable without adding epistemic meaning): production identity-provider integration; persisted authority grants; the MinIO adapter; browser and assistive-technology conformance.
   - **Constitutional research questions requiring separate future gates** (each could alter how humans interpret ARGUS output): evidentiary sufficiency; comparative assessment; calibrated confidence; AI provenance at Hypothesis; review workflow; admissibility versus institutional adoption. Each requires *research question → constitutional constraints → ontology decision → experimental hypothesis → gate* before implementation — never placement on an ordinary product backlog.

4. **Review-workflow caution (binding on the future gate):** administrative states (reviewed, acknowledged, assigned, action requested, escalated) can be legitimate, but the design must preserve *reviewed ≠ believed*, *acknowledged ≠ accepted as true*, *approved for action ≠ epistemically correct*, *institutionally adopted ≠ reality established*. It is its own experiment, not an extension of the presentation page.

5. **ARGUS Constitutional Baseline 1.0 is authorized and prepared** ([docs/foundation/CONSTITUTIONAL_BASELINE_1.0.md](../foundation/CONSTITUTIONAL_BASELINE_1.0.md)): a versioned, immutable pin of the completed roadmap's normative corpus, experimental ledger, schema head, and reference results — the clean artifact for independent reimplementation, external review, research publication, security assessment, and future regression comparison. The baseline is immutable after release; future work supersedes it through a new version, never by rewriting what the completed roadmap established.

## Governance review

1. **Constitutional Review** — PASS: Article IX applied to the program — twelve n = 1 results justify replication, not expansion; Article VII — the phase tests the method's claim rather than accumulating features.
2. **Domain Review** — PASS: the ontology is untouched; the phase exercises existing meaning under new conditions.
3. **Architectural Review** — PASS: every workstream enters through contracts that already exist (protocols, conformance suites, checklists, refusal matrices); the baseline gives regression comparison a fixed reference.

## Consequences

- Phase 4 workstreams each require their own plan gate before implementation (ONT-PRN-024 applies to hardening exactly as it applied to construction).
- The baseline is the handoff artifact for workstream 4D: the independent team receives it, not the repository's implementation tree.

## Alternatives considered

- **Proceed directly to filling the published gaps** — rejected: several gaps are epistemic powers whose constraints do not yet exist; constraint precedes expression (ONT-PRN-024).
- **Declare the program finished** — rejected: one reference implementation obeying the Constitution is evidence about the implementation; whether the *Constitution* is strong enough to discipline different implementations, environments, adapters, and teams is the unanswered — and now testable — question.

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

**Affected Articles:** VII, IX (the program's own scientific discipline). Others untouched.

**Compliant?** YES

**Explanation:** ARGUS has demonstrated constitutional discipline from the first stored byte to the final human-visible screen. The next challenge is not proving that one reference implementation can obey the Constitution — it is determining whether the Constitution is strong enough that different implementations, environments, adapters, and teams continue to produce the same disciplined behavior.
