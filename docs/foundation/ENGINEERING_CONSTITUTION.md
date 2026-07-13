# The ARGUS Engineering Constitution

**Status:** Governing document — binding on every schema, migration, API, validation rule, database constraint, and test in this repository.

This is the supreme engineering law of the ARGUS project. Where any implementation, convention, or convenience conflicts with this document, the Constitution prevails. Changes to this document require an Architecture Decision Record (see [`docs/adr/`](../adr/README.md)) explaining the change and its consequences.

---

## Prime Directive

**ARGUS must never distort reality in pursuit of certainty.**

## Covenant

ARGUS remains accountable to:

- **Reality before reputation.**
- **Evidence before narrative.**
- **Truth before outcome.**

---

## Article I — Evidence Before Opinion

Every analytical artifact in the system must be grounded in evidence that precedes it.

**Engineering obligations:**

- No `Interpretation`, `Hypothesis`, or AI-generated statement may exist without at least one traceable reference to an `Observation`, which in turn references an `EvidenceArtifact` via a `SourceLocator`.
- Schemas must make ungrounded claims unrepresentable (non-nullable foreign keys, required reference collections), not merely discouraged.
- Reviews must reject any feature that lets opinion enter the system ahead of, or detached from, evidence.

## Article II — Human Judgment Is Final

ARGUS stops before judgment. Judgment belongs to humans.

**Engineering obligations:**

- No code path may compute, store, or emit a determination of guilt, a resolved contradiction, or a closed unknown on behalf of the system or its AI components.
- State transitions that represent human decisions (resolving a contradiction, closing an unknown, accepting an interpretation) must require an authenticated human actor recorded in the audit history.
- AI output is always a *proposal* pending human review; the schema must distinguish proposed from human-accepted states.

## Article III — Every Analytical Conclusion Must Explain Itself

**Engineering obligations:**

- Every analytical record carries its reasoning: source references, method, and (for AI output) model identifier, model version, prompt/workflow version, uncertainty explanation, and review status.
- "Explain itself" is a data requirement, not a UI feature: the explanation must be stored with the conclusion and survive export.
- **No provenance, no claim.** Writes lacking provenance fields must be rejected at the persistence boundary.

## Article IV — Alternative Explanations Must Always Remain Possible

**Engineering obligations:**

- The data model must support multiple concurrent `Hypothesis` records over the same evidence without privileging one.
- No workflow may force convergence to a single hypothesis, delete competing hypotheses, or hide them by default.
- Confidence representations must never be allowed to round up to certainty (see Article IX).

## Article V — Evidence Is Immutable

**Engineering obligations:**

- `EvidenceArtifact` records are append-only. There is no update or delete path for evidence content.
- Corrections are expressed as *retractions and replacements*: a new record superseding the old, with the old record preserved and the linkage explicit.
- Content addressing (e.g., cryptographic hashes) should anchor artifacts so tampering is detectable.
- Nothing disappears. History is preserved.

## Article VI — Privacy and Legal Authority Must Be Respected

**Engineering obligations:**

- Access to case data is scoped by legal authority; authorization is enforced at the service boundary, not the client.
- Data handling must support jurisdictional requirements: retention, sealing, disclosure obligations, and chain-of-custody documentation.
- Personally identifying information is handled under least-privilege access and is auditable (every access is an `AuditEntry`).

## Article VII — Scientific Integrity Before Convenience

**Engineering obligations:**

- Analytical methods must be reproducible: same inputs, same versioned method, same outputs.
- Shortcuts that trade correctness, calibration, or traceability for speed of delivery are constitutional violations, not engineering trade-offs.
- Known limitations of any method must be recorded alongside its results.

## Article VIII — Justice Requires Transparency

**Engineering obligations:**

- Every analytical step must be auditable end-to-end by an external party (e.g., defense counsel) without access to internal tooling.
- The audit history (`AuditEntry`) is itself append-only and covers reads of sensitive material as well as writes.
- Exports must carry full provenance so claims remain verifiable outside the system.

## Article IX — Certainty Must Never Exceed the Evidence

**Engineering obligations:**

- Uncertainty is a first-class, mandatory attribute of analytical output — never an optional annotation.
- `Unknown` records represent missing information explicitly; absence of data must never be silently treated as evidence of absence.
- Displays and APIs must not collapse graded uncertainty into binary conclusions.

---

## Structural Doctrine

These distinctions are load-bearing and must never be collapsed, in schema, API, or UI:

```
Observation    ≠  Interpretation
Interpretation ≠  Hypothesis
Hypothesis     ≠  Judgment
```

- **Observation** — what the evidence shows, with a `SourceLocator` into an `EvidenceArtifact`.
- **Interpretation** — what an observation may mean, referencing the observation(s) it interprets.
- **Hypothesis** — a candidate explanation composed from interpretations, always coexisting with alternatives.
- **Judgment** — a human act, outside ARGUS.

`Contradiction` and `Unknown` are explicit first-class objects, never derived UI decorations.

---

## Boundaries of the AI

The AI **may**: organize, summarize, identify patterns, suggest contradictions, suggest unknowns, propose hypotheses.

The AI **may NOT**: determine guilt, resolve contradictions, close unknowns, create judgments, fabricate missing evidence, hide uncertainty.

These prohibitions must be enforced structurally — by schema constraints, authorization rules, and API design — not by convention alone.

---

## Enforcement

1. Every pull request must be reviewable against this document; reviewers cite the article a change reinforces or endangers.
2. If a requested implementation would violate the Constitution: **stop, explain why, and propose a constitutionally compliant alternative.**
3. Tests that verify constitutional guarantees (immutability, provenance requirements, human-only transitions) are release-blocking and may not be skipped or deleted to make a build pass.
