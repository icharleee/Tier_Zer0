# ODE-0001: Ontology-Driven Engineering — Axioms and Method

- **Document version:** 0.18.0 (Draft)
- **Program:** Ontology-Driven Engineering (ODE)
- **Date:** 2026-07-13
- **Origin:** Named by AGC Review Session 001 (ADR-0010); axioms established by AGC Review Session 002; first implementation: ARGUS

## Abstract

Ontology-Driven Engineering (ODE) is a software engineering methodology in which the ontology defines meaning, the schema defines structure, implementation realizes behavior, and verification proves conformance. This paper states its five axioms, the derivation chain they generate, and the conditions under which the methodology applies. ODE emerged from the construction of ARGUS but is independent of it: any domain where the cost of meaning-drift is high — medicine, aviation, intelligence, finance, scientific research — is a candidate.

## 1. Two research programs

This paper marks the separation of two questions that were briefly entangled:

- **Investigation Systems Science (ISS)** asks: *how do investigations work?* It is domain science — theory about evidence, fragmentation, and epistemic integrity.
- **Ontology-Driven Engineering (ODE)** asks: *how should complex systems be engineered?* It is methodology — theory about how meaning, structure, behavior, and proof should relate in any engineered system.

The programs are related (ARGUS applies ODE to the ISS domain) but independent: neither depends on the other's results.

## 2. The five axioms

**Axiom I — Reality precedes representation.**
The system models a reality it did not create and cannot fully capture. Every artifact in the system is a representation, and no representation may be mistaken for the thing it represents. (In ARGUS: ONT-PRN-001.)

**Axiom II — Ontology defines meaning.**
There is exactly one source of truth for what the system's concepts mean, and it is a governed, versioned ontology — not a database, an API, or the accumulated habits of the codebase. Meaning changes are made in the ontology first and propagate downward, never the reverse. (In ARGUS: ONT-PRN-008, Founder Resolution 003.)

**Axiom III — Structure derives from ontology.**
Schemas, data models, and contracts are translations of ontological rules into structure. The translation itself is a recorded artifact (a derivation specification), so that "derives from" is a checkable claim, not a slogan.

**Axiom IV — Behavior implements structure.**
Code realizes the derived structure. Implementation artifacts are permanently replaceable and carry no independent authority; an implementation that disagrees with the ontology is defective by definition. (In ARGUS: ONT-PRN-010, Founder Resolution 005.)

**Axiom V — Verification proves conformance.**
Tests derive from the ontology, not from the implementation, and each declares which ontological rule it protects. Verification therefore proves conformance to meaning — not conformance of the code to itself. (In ARGUS: ONT-PRN-009, Founder Resolution 004.)

That is the methodology. Everything else is implementation.

## 3. The derivation chain

The axioms generate a one-directional chain:

```
Reality
  → Ontology                  (meaning; Axioms I–II)
  → Derivation Specification  (translation; Axiom III)
  → Schema                    (structure; Axiom III)
  → Implementation            (behavior; Axiom IV)
  → Verification              (proof; Axiom V)
  → Operation
```

Two properties distinguish ODE from requirements-driven and model-driven predecessors:

1. **Immutable referents.** Ontological concepts carry stable identifiers, so every downstream artifact — a schema constraint, a failing test, an audit finding — can cite the exact rule it serves, across decades and rewrites.
2. **A recorded translation layer.** The step from meaning to structure is itself a governed document, making derivation auditable rather than tribal.

## 4. When ODE applies

ODE's overhead is justified when meaning-drift is expensive: systems whose outputs carry legal, medical, safety, or scientific weight; systems intended to outlive their first implementation; systems built by many hands over long periods. It is unjustified for exploratory prototypes and short-lived tools, where the ontology would outweigh the product.

## 5. Hypotheses and first empirical results

ODE began as theory; ARGUS Slice 1B provides its first data. Recorded per AGC Review Session 005 — carefully, as evidence, not proof:

> **Hypothesis H1:** Independent implementations derived from a common ontology can converge on identical constitutional behavior without sharing implementation code.

Slice 1B is the first experimental data point: the Python domain layer and the PostgreSQL persistence boundary independently enforce the same constitutional rules — the same transition registry, the same actor constraints, the same audit obligations — derived separately from Entity Lifecycles 2.0.0, with a conformance suite proving behavioral agreement. One experiment is not proof. It is evidence.

**Status: Supported (n = 1).** We do not claim ODE is correct; we record that the experiment has not falsified it.

> **Hypothesis H2:** Behavior derived independently from a common ontology can converge across implementations without shared executable logic.

Slice 1B tested rule *transitions*; Slice 1C tests derived *behavior* — constitutional predicates (permission questions computed from constitutional state) rendered independently in Python and PostgreSQL against a canonical decision matrix. Different experiment, same methodology. H2 is a stronger claim than H1: not merely that implementations enforce the same rules, but that they independently arrive at the same *decisions*. It also suggests ODE may eventually distinguish structural derivation, behavioral derivation, and verification derivation.

**Status: Supported (n = 1)** — Slice 1C's conformance sweep: 16/16 canonical-matrix rows derived identically (structural verdict, contextual verdict, reason codes) by two renderings sharing no executable logic.

> **Hypothesis H3 (refined per AGC Session 008):** Independent implementations of epistemic admissibility converge when derived from a shared ontology and provenance model.

Registered ahead of Slice 1D, which introduces the first **epistemic object** — an Observation is the first entity that makes a claim about reality. The refinement matters: Observation creation is about *admissibility* ("this claim is constitutionally allowed to exist"), not reasoning — reasoning begins at Interpretation. The experimental surface is the validator pair (Python and PostgreSQL renderings of the admissibility rules), testing SourceLocator grounding, provenance enforcement, eligibility enforcement, and audit emission as epistemic behaviors.

**Status: Supported (n = 1)** — Slice 1D: the canonical refusal matrix (ten scenarios) derived identically by both validators, zero divergences; verdict confirmed by AGC Session 006.

> **Observation O3:** Separating admissibility from persistence reduced implementation complexity while increasing independent verifiability — validators became pure, creation became mechanical, database functions became smaller, tests became simpler (Resolution 012 / ONT-PRN-017: persistence implements admissibility, not defines it).

> **Hypothesis H4 (refined at the Slice 2A plan review, for falsifiability):** Independent implementations can preserve multiple admissible Interpretations over the same grounded Observations without assigning epistemic priority, comparative strength, or preferred status to any Interpretation.

The refinement distinguishes *technical ordering* (creation order, citation identifiers, indexes — unavoidable and non-evidentiary) from *epistemic preference* (ranking fields, preferred constraints, promotion on retraction, asymmetric exposure — forbidden). Article IV is not about having an interpretation but about protecting alternatives; the experiment requires at least two admissible interpretations of the same grounded observations, exposed symmetrically. The prior experiments each tested a different derivation category — transitions (H1), predicates (H2), admissibility (H3) — and H4 adds preservation of plurality.

**Status: Supported (n = 1)** — Slice 2A: two interpretations over identical grounding; no ranking surface (schema and pg_constraint scans); retraction of one left the sibling byte-identical; verdict confirmed by AGC Session 007.

> **Observation O4:** Epistemic plurality can be preserved without introducing computational preference when preference is excluded structurally rather than procedurally — not "developers remembered not to rank," but "the architecture made ranking impossible."

> **Hypothesis H5 (refined per AGC Session 007):** Independent implementations preserve explicit epistemic boundaries without transforming absence into evidence, inference, or implied support for any competing interpretation.

Registered ahead of Slice 2B (*Unknowns and Evidentiary Limits*) — the first explicit representation of **negative knowledge** (Resolution 015 / ONT-PRN-020). Connects directly to Article IX: representing uncertainty is not the same as representing the limits that produce it.

**Final refinement (AGC Session 008):** *Independent implementations preserve explicit epistemic boundaries while ensuring that neither absence nor newly acquired knowledge automatically changes previously admitted reasoning.* Knowledge changes; the system does not; humans decide what to do next.

**Status: Supported (n = 1)** — Slice 2B: the bounded Interpretation remained byte-identical through linking, UNDER_REVIEW, and human resolution with evidence; dispositions derived identically in both renderings; verdict confirmed by AGC Session 009.

> **Observation O6:** Explicitly represented ignorance is computationally stable; implicit ignorance expressed as missing data is not. NULL cannot have provenance, citations, audit history, operational stewardship, explicit resolution, or constitutional constraints — `UNK-000001` can. Empirical, not philosophical: demonstrated in Slice 2B.

> **Observation O5:** Negative knowledge becomes computationally useful only after it is represented explicitly rather than implicitly through missing data. NULL is not Unknown; missing rows are not Unknown; Unknown is a deliberate epistemic object.

> **Hypothesis H6 (refined at the Slice 2C plan review):** Independent implementations can preserve a formally scoped incompatibility among multiple constitutionally admissible claims without changing their admissibility, assigning epistemic priority, or adjudicating which claim survives.

The dimension added (ONT-PRN-022): joint incompatibility becomes representable — coexistence concerns what the ledger may preserve; incompatibility concerns what reality may permit. The decisive rule: a Contradiction may state that claims cannot all fit the same reality; it may never decide which claim reality favors.

**Status: Supported (n = 1)** — Slice 2C: the canonical contradiction matrix transcribed independently and derived identically by both renderings; both member Interpretations byte-identical through creation, review, and human disposition; no adjudicative surface (schema and pg_constraint scans); verdict confirmed by AGC Session 011.

> **Observation O7:** Formal incompatibility can be represented as a durable boundary without converting conflict into computational adjudication when scope, membership, health, and disposition are modeled separately.

> **Hypothesis H7 (refined at the Slice 2D gate review, AGC Session 012):** Independent implementations can admit plural, provisional explanatory structures while preserving derivational support, falsifiability, explicit alternative and boundary articulation, uncertainty, and non-preference — without automatically revising, promoting, refuting, or adjudicating any explanation.

Registered ahead of Slice 2D (*Hypotheses*) — the first object that attempts to *explain* reality, governed by ONT-PRN-023 (Resolution 018 / ADR-0028): an explanation is admissible only when the system can state what supports it, what limits it, what could challenge it, and what remains unknown. The Session 012 refinement makes the experiment falsifiable along two axes the original wording left implicit: *historical articulation vs. current derived state* (a creation-time absence explanation must survive later alternative linking), and the complete negative-obligation set (no automatic revision, promotion, or refutation from any boundary event or sibling retraction). The decisive rule: ARGUS may preserve explanations for examination; it may never convert explanation into verdict.

**Status: Supported (n = 1)** — Slice 2D, verdict confirmed by AGC Session 013 through independent invariants: two Hypotheses coexist without preference; creation-time alternative articulation immutable while current alternative state changes derivationally; boundary links remain boundary-owned; boundary disposition changes no Hypothesis bytes; retraction of one Hypothesis promotes no other; derivational health surfaced rather than acted upon; Python and PostgreSQL renderings agree (17-row conformance sweep, zero divergences on the first run — not itself proof of broader convergence, but meaningful evidence that the derivation discipline is becoming repeatable); fingerprints use normative, versioned definitions; prohibited ranking and verdict surfaces structurally absent. The decisive result: *a Hypothesis may gain alternatives, lose current support, encounter answered Unknowns, and face disposed Contradictions without ARGUS rewriting, promoting, refuting, or adjudicating it.*

**Standing limitations (publication mandatory, per Sessions 012–013):** no evidentiary sufficiency model; no formal comparative assessment; no calibrated confidence; no AI provenance at Hypothesis; no authenticated actor identity; no end-user review workflow; and — added by Session 013 — no formal mechanism yet distinguishes creation admissibility from later human endorsement or institutional adoption (a warning that future workflow must never smuggle epistemic truth into administrative approval, not permission to build an "accepted hypothesis" state).

> **Observation O8 (promoted from candidate observation 1, AGC Session 013):** Epistemic representation develops through an alternating rhythm of positive structures that express what may be claimed and negative boundary structures that express where those claims must stop.

Demonstrated sequence: Interpretation (positive meaning structure) → Unknown (negative knowledge boundary) → Contradiction (negative incompatibility boundary) → Hypothesis (positive explanatory structure); paired cycles Interpretation-bounded-by-Unknown and Hypothesis-bounded-by-Contradiction. Two completed cycles establish a credible pattern; they do not prove all future epistemic architectures must alternate this way — recorded as an ODE observation, **deliberately not constitutionalized** (Session 013: proportional to the evidence).

> **Hypothesis H8 (refined at the Slice 3A gate review, AGC Session 014):** Independent implementations can compose the complete authorized epistemic graph of a Case into semantically and canonically equivalent read models while preserving provenance, plurality, boundary structure, temporal truth, visibility constraints, and non-preference — without constructing a privileged narrative or introducing new epistemic meaning.

Registered ahead of Slice 3A (*Case Reconstruction Read Model*) — the first **integration** experiment: H1–H7 mostly asked *can one concept remain constitutional?*; H8 asks *can all constitutional concepts remain constitutional when viewed together?* The final clause is the true integration threat: a collection of constitutionally safe objects can still become unconstitutional if the read model arranges them into an implied answer. H8 is tested through semantic structural equality and strengthened by canonical byte identity; a byte divergence fails implementation conformance but does not prove epistemic divergence until classified (Session 014). The question: can ARGUS render the full topology of an investigation without collapsing it into a single story?

**Status: Supported (n = 1)** — Slice 3A, verdict confirmed by AGC Session 015: semantic equivalence across the complete topology; canonical byte identity after normative serialization; SEALED material accounted for without unauthorized disclosure; historical articulations coexisting with current derived conditions; structurally symmetric Hypothesis shapes; manifest-reconciled completeness; and a deliberately corrupted audit chain surfaced as `CHAIN_INVALID` without suppressing epistemic records or inventing an explanation — degraded trust infrastructure did not make the records pretend to cease existing. The wording **"complete *authorized* epistemic graph" is retained deliberately** (Session 015): the reconstruction remains bounded by visibility rules, current ontology authorization, manifest scope, and the absent authority model. The system transitioned from locally constitutional objects to a globally constitutional view without introducing a new epistemic authority: the read model can reveal what exists, was claimed, interpreted, unknown, incompatible, hypothesized, retracted, and changed in derived condition — it still cannot say *therefore, this is what happened*.

> **Observation O9 (promoted from candidate at AGC Session 015):** Constitutional guarantees established locally do not automatically compose; system-level projections require independent constraints for completeness, symmetry, visibility, non-effects, and non-preference.

Promotion despite n = 1 rests on the demonstrated **existence of failure classes local slices cannot express** — privileged placement, undocumented ordering, asymmetric schema, silent omission, visibility ambiguity, aggregation drift, composition-created narrative: every local validator could remain perfectly correct while the global view violated the Constitution. Status (updated by AGC Session 017): **supported across two distinct integration surfaces — global read-model composition (Slice 3A: locally safe epistemic records, unsafe composition remains possible) and storage reconciliation (Slice 1E: locally passing persistence behavior, cross-representation inconsistency remains possible).** Same deeper result on both: local correctness does not guarantee global constitutional integrity. Retained as an ODE observation, not elevated to a universal principle; confidence substantially higher at n = 2.

*Candidate observation O10 (registered at AGC Session 015, deliberately not promoted — one instance is not enough):* Mature constitutional infrastructure reduces later implementation divergence by allowing new capabilities to reuse previously proven canonical semantics rather than inventing new normalization rules. First evidence: Slice 3A's predicted timestamp/JSON divergence hotspot disappeared into the chain_version=1 serializers that were independently specified and parity-tested in Slice 1B. Also recorded as evidence supporting Principle P1 (architectural compounding: earlier rigor → reusable invariant → later integration cost falls), not as a new principle.

> **Hypothesis H9 (refined at the Slice 1E gate review, AGC Session 016):** Independent implementations can classify integrity divergence among persisted representations of constitutional records from the same observed storage facts while preserving provenance, lifecycle state, and epistemic neutrality — without silently repairing data or converting storage agreement into evidentiary truth.

Registered ahead of Slice 1E (*Storage + Reconciliation*) — the persistence-failure frontier: constitutional discipline has survived object creation and composition; the next test is whether it survives storage degradation. Governed by ONT-PRN-026 (Resolution 021: representational agreement is never evidentiary truth, representational disagreement never epistemic falsity) and ONT-PRN-027 (Resolution 022: detect ≠ decide ≠ mutate — no silent repair of constitutional history). The Session 016 refinement bounds the dual-rendering claim honestly: **the experiment applies to the classification of shared observations, not to independent filesystem probing** — the probe is a declared single implementation; the classifiers are the triangulated pair. This limitation is stated in every H9 report and remains attached to the verdict.

**Status: Supported (n = 1)** — Slice 1E, verdict confirmed by AGC Session 017: zero classifier divergences across the normative matrix; probing separated from classification; full-invariant MATCHED semantics; diagnostic divergence reasons; sealed-content non-access; stalled verification distinct from permanent UNVERIFIED; no mutation, no audit emission, repeat-scan determinism; no truth-bearing vocabulary on the report surface.

> **The storage_ref discovery (formal record, AGC Session 017).** The first reconciliation scan exposed a real defect invisible to all 95 prior tests: on the PostgreSQL path, the pending ORM `storage_ref` mutation was discarded (raw SQL execution without autoflush, then `expire()`), so every activated artifact's persisted pointer violated the content-addressing rule while content bytes, hashes, activation, lifecycle tests, and immutability all remained correct. Only the new cross-representation invariant (`STORAGE_LOCATION_MISMATCH` under the strengthened MATCHED) could express the fault. ARGUS behaved exactly as ONT-PRN-027 intends: observe divergence → classify → surface the diagnostic reason → **stop**; the repair was a separate engineering change. Recorded as a concrete supporting case for **ONT-PRN-011** with the direction of authority intact: implementation revealed a violated invariant, existing constitutional meaning stayed unchanged, and implementation was corrected to conform — never the ontology rewritten to excuse behavior. A related specification finding: the classifier's F/H matrix rows stay although current DB tampering cannot manufacture them (the Slice 1B immutability trigger blocks even the tamper role) — *unreachable in the current implementation ≠ impossible in the architecture's external environment*; future stores, imports, migrations, and older records may still present those facts.

> **Observation O11 (promoted from candidate at AGC Session 017):** Integrity reasoning remains constitutionally bounded when raw infrastructure observations, derived integrity classifications, and epistemic judgments are represented as distinct layers.

Structurally analogous to the foundational Evidence ≠ Observation ≠ Interpretation separation. The live defect strengthened the observation: the layering made a real system fault precisely describable — *observed location differs from expected location → DIVERGENT/STORAGE_LOCATION_MISMATCH → no epistemic inference* — without ever drifting into "the stored artifact is invalid." Status: **supported by the first storage-reconciliation experiment (n = 1)**; not a principle yet — the future MinIO adapter is the repeat test.

*Candidate observation O12 (registered at AGC Session 017, deliberately not promoted — one case):* Integration constraints can function as **discovery instruments**: an invariant introduced to verify system-wide consistency may reveal defects in earlier implementations that were locally valid under narrower test surfaces. Distinct from O9: O9 says local guarantees do not automatically survive composition; O12 says system-level invariants can actively reveal hidden local defects. First strong example: the storage_ref defect.

> **Hypothesis H10 (proposed at AGC Session 017, ahead of Slice 1F-A):** Independent API paths can bind constitutionally meaningful actions to authenticated actor context while preventing caller-controlled identity substitution and preserving the separation between identity, authority, and epistemic meaning.

Registered ahead of Slice 1F-A (*Authenticated Actor Context*) — the first of the three 1F sub-slices Session 017 decomposed (identity → authority → presentation; H11 *authority and visibility* and H12 *the visible review surface* are reserved for the later sub-slices as separate experiments). Core invariant: **authenticated principal ≠ domain actor claim** — the acting identity derives from authenticated context, never from a payload. **Status: Untested.**

*Candidate observation 1 (first repetition recorded, AGC Session 009):* the ladder alternates between positive structures and negative boundaries. One full cycle now exists (Evidence/Observation/Interpretation positive → Unknown negative, built to constrain Interpretation). If Slice 2C–2D produce the Hypothesis-positive/Contradiction-negative pairing, two complete cycles exist — only then does this elevate to a principle. *(Condition met at Slice 2D; promoted to Observation O8 by AGC Session 013 — as an observation, not an ontology principle.)*

*Candidate observation 2 (AGC Session 009):* complex systems become trustworthy when every increase in expressive power is preceded by an increase in structural constraint — provenance before Observation; grounding before Interpretation; admissibility before Unknown; Unknown and Contradiction before Hypothesis. Recorded as candidate (ADR-0026 §3); elevate if the pattern holds through Slice 2D. *(Condition met; promoted to Principle P1 by AGC Session 013 — see §6.)*

> **Observation O2:** Independent verification derived directly from the ontology detected implementation divergence without sharing executable logic.

In Slice 1C, the test suite transcribed the canonical matrix as its own literal — a third derivation, independent of both implementations (**triangulation**, formalized as Resolution 010 / ONT-PRN-015: normative specification, executable implementation, independent verification; no implementation verified only against itself). The H2 sweep caught a real PostgreSQL parsing defect (`array || 'literal'` read as an array literal) precisely because its expectations came from the transcribed matrix rather than from the function under test.

> **Observation O1:** During the implementation of Slice 1B, multiple architectural refinements emerged from executable constraints rather than design discussion — a real PostgreSQL syntax error caught by the live database, a lock-order inconsistency exposed by concurrency design, and a three-way lifecycle duplication identified before drift (leading to Resolution 008) — supporting the hypothesis that implementation is an effective source of ontology validation when governed by a one-directional derivation chain.

## 6. Principles

The first ODE principle, promoted from candidate observation 2 by AGC Session 013 after surviving the full implemented epistemic ladder:

> **Principle P1 — Constraint precedes expressive power.** Every increase in a system's epistemic expressive power should be preceded by structural constraints capable of limiting, tracing, and refusing that new expression.

Evidence, by slice (the record cites experiments, not proof):

| New expressive power | Constraint established beforehand | Slice |
|---|---|---|
| Observation | Evidence provenance and rung separation | 1D (after 1A–1C) |
| Interpretation | Grounding, uncertainty, and non-preference | 2A |
| Unknown | Non-conclusion and boundary immutability | 2B |
| Contradiction | Scope, symmetry, and anti-adjudication | 2C |
| Hypothesis | Unknowns, Contradictions, falsifiability, and alternative articulation | 2D |

Hypothesis was not introduced and constrained afterward: its obligation floor existed before its schema did (ONT-PRN-023 at Session 011, the Session 012 amendments at the gate, the Invariant Matrix rows before code). That is a stronger result than ontology-first development alone — it demonstrates **constraint-before-expression as a repeatable engineering method**. Within ARGUS the principle is enforced by Founder Resolution 019 / ONT-PRN-024 (ADR-0029); whether it should bind all future ontology extensions *constitutionally* is deliberately deferred (Session 013).

**Status: Supported across the currently implemented epistemic ladder (Slices 1D–2D).** Not proven; recorded with its evidence.

## 7. Open questions

- How does an ODE system evolve its ontology under live load — what is the migration discipline when meaning (not just structure) changes?
- What tooling makes derivation checkable mechanically (ontology-to-schema linting, test-annotation verification)?
- Can derivation specifications be partially generated, and where must human translation judgment remain?
- What does ODE conformance certification look like for a third party auditing a system's claim to be ontology-driven?

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial draft: program separation, the five axioms (AGC Session 002), derivation chain, applicability, open questions. |
| 0.2.0 | 2026-07-13 | Added Hypothesis H1 and Observation O1 with Slice 1B as the first experimental data point (AGC Review Session 005). |
| 0.3.0 | 2026-07-13 | Registered Hypothesis H2 (behavioral convergence via constitutional predicates), Slice 1C as its first experiment (Slice 1C plan review / ADR-0018). |
| 0.4.0 | 2026-07-13 | H1 and H2 marked Supported (n = 1 each); Observation O2 (triangulated verification detects divergence) and Hypothesis H3 (epistemic-constraint convergence, untested) registered per AGC Review Session 007 / ADR-0019. |
| 0.5.0 | 2026-07-13 | H3 refined to epistemic admissibility (AGC Session 008 / ADR-0020): the experiment targets the validator pair, not insertion. |
| 0.6.0 | 2026-07-13 | H3 marked Supported (n = 1); Observation O3 (admissibility/persistence separation) and Hypothesis H4 (preservation of competing interpretations, untested) registered per AGC Review Session 006. |
| 0.7.0 | 2026-07-13 | H4 refined for falsifiability at the Slice 2A plan review: technical ordering distinguished from epistemic preference. |
| 0.8.0 | 2026-07-13 | H4 marked Supported (n = 1); Observation O4 (structural exclusion of preference) and Hypothesis H5 (epistemic boundaries, refined wording, untested) registered per AGC Review Session 007. |
| 0.9.0 | 2026-07-13 | H5 finally refined (knowledge changes; the system does not); Observation O5 (explicit negative knowledge) registered; positive/negative alternation recorded as a candidate observation (AGC Session 008). |
| 0.10.0 | 2026-07-13 | H5 marked Supported (n = 1); Observation O6 (explicit ignorance is computationally stable — empirical); rhythm candidate's first repetition recorded; trustworthiness-via-constraint registered as candidate observation 2 (AGC Session 009 / ADR-0026). |
| 0.11.0 | 2026-07-13 | Hypothesis H6 registered as refined at the Slice 2C plan review (scoped incompatibility without adjudication), untested. |
| 0.12.0 | 2026-07-13 | H6 marked Supported (n = 1); Observation O7 (incompatibility as durable boundary without adjudication) registered; Hypothesis H7 (provisional explanatory structures, untested) registered per AGC Review Session 011 / ADR-0028. Header version corrected (had lagged at 0.1.0 since the initial draft). |
| 0.13.0 | 2026-07-13 | H7 refined at the Slice 2D gate review (AGC Session 012): plural explanatory structures, derivational support, historical-vs-current articulation, and the complete non-adjudication obligation set — precise enough to falsify. |
| 0.14.0 | 2026-07-13 | H7 marked Supported (n = 1) with the seven standing limitations; Observation O8 (positive/negative rhythm) promoted from candidate 1 — observation, not ontology principle; Principle P1 (constraint precedes expressive power, §6) promoted from candidate 2 with per-slice evidence; Hypothesis H8 (compositional integrity, untested) registered ahead of Slice 3A — per AGC Session 013. |
| 0.15.0 | 2026-07-13 | H8 refined at the Slice 3A gate review (AGC Session 014): semantic + canonical equivalence, visibility constraints, and the no-new-epistemic-meaning clause; candidate observation O9 (local constitutionality does not automatically survive composition) registered, deliberately unpromoted. |
| 0.16.0 | 2026-07-13 | H8 marked Supported (n = 1); O9 promoted to ODE observation (failure classes local slices cannot express); candidate O10 registered (architectural compounding, also recorded as P1 evidence); Hypothesis H9 (storage reconciliation without truth conversion or silent repair, untested) registered ahead of Slice 1E — per AGC Session 015. |
| 0.17.0 | 2026-07-13 | H9 refined at the Slice 1E gate review (AGC Session 016): classification of shared observed facts as the dual-rendering surface, with the probing limitation stated; candidate O11 (storage fact ≠ integrity classification ≠ epistemic judgment) registered, deliberately unpromoted. |
| 0.18.0 | 2026-07-13 | H9 marked Supported (n = 1); the storage_ref discovery formally recorded (ONT-PRN-011 supporting case; F/H reachability finding); O9 evidence updated to two integration surfaces; O11 promoted with the Session 017 wording; candidate O12 (integration constraints as discovery instruments) registered; Hypothesis H10 registered untested ahead of Slice 1F-A (H11/H12 reserved) — per AGC Session 017. |
