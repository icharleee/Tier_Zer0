# ADR-0034: Authority governs actions and visibility, never epistemic standing

- **Status:** Accepted (Founder Resolution 024, AGC Review Session 019 — freeze exemption per ONT-PRN-011: the governing constraint for Slice 1F-B, proposed at the Slice 1F-A completion review)
- **Date:** 2026-07-13
- **Constitutional articles:** II (Human judgment is final), VI (Privacy and legal authority), IX (Certainty never exceeds evidence)
- **Supersedes:** none (the authority half of the identity → authority → presentation decomposition, following ONT-PRN-028)

## Context

Slice 1F-A established *who* is acting (ONT-PRN-028: identity is authenticated, never asserted). Slice 1F-B must establish *what* an authenticated principal may do and see — without letting permission bleed into truth. The danger the decomposition was designed to prevent: an authority layer that quietly reads *authorized* as *credible*, so that a privileged user's records become treated as more true than a less-privileged user's. They are not. Authority is permission; it is not epistemic standing.

## Decision

Founder Resolution 024 is recorded (stable identifier **ONT-PRN-029**):

> **Authority governs permitted actions and visibility, never epistemic standing.** Granting or denying authority must not change the meaning, admissibility, credibility, or truth status of any constitutional record.

Normative consequences:

1. **Two distinct questions, never collapsed:** *may this principal perform this action?* (action authority) and *may this principal view this information?* (visibility authority). They diverge — a principal may view SEALED metadata but not content, create an Observation but not dispose a Contradiction — so one coarse role enum cannot express them.
2. **Capabilities, resource-scoped, not titles.** Constitutional checks depend on explicit capabilities bound to a resource scope (`principal × capability × resource`), not on organizational job titles that become accidental bundles. An authority decision takes `(principal, action, resource, context)` and returns `ALLOW` / `DENY` with a machine-readable reason. No outcome named `TRUSTED` or `PREFERRED` exists — authority is permission, not status.
3. **Epistemic neutrality.** No authority grant or denial alters any record's stored fields, derived states, admissibility, or the reconstruction's epistemic content. Two principals with different visibility receive identical epistemic state for the fields both are authorized to see; the underlying record is singular (the O14 test).
4. **Authentication is not authority** (ONT-PRN-028 corollary, restated): being authenticated confers no capability. And **the trusted-internal execution context is not a user superuser** — it is infrastructure (fixtures, bootstrap, migrations), explicitly separated at the gate; an authenticated user lacking authority is denied by the authority layer, never quietly satisfied by an internal bypass.

## Governance review

1. **Constitutional Review** — PASS: Article IX protected — privilege never manufactures credibility; Article VI operationalized — legal authority becomes an explicit, checkable capability rather than an implicit trust.
2. **Domain Review** — PASS: extends the separation discipline (authentication ≠ attribution ≠ authority ≠ epistemic meaning) into enforcement; adds no epistemic object.
3. **Architectural Review** — PASS: enforceable as a pure `(principal, action, resource, context) → ALLOW/DENY` decision, dual-renderable and conformance-testable; the action/visibility split is structural.

## Consequences

- The Slice 1F-B gate must present the capability set, the resource-scope model, and the action-vs-visibility split before code (ONT-PRN-024).
- Authority-decision vocabulary joins the contamination discipline: no credibility/preference/truth stems on its structured surfaces.

## Alternatives considered

- **Role titles (DETECTIVE, SUPERVISOR, ADMIN)** — rejected: bundles that drift into accidental grants; capabilities are explicit and auditable.
- **Global (unscoped) capabilities** — rejected: one authenticated investigator would gain every Case; authority must be resource-scoped.
- **A single "authorized" flag reused as a trust signal** — rejected: exactly the collapse of authority into epistemic standing this resolution forbids.

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

**Affected Articles:** II, VI, IX (permission made explicit and checkable, kept apart from truth). Others untouched.

**Compliant?** YES

**Explanation:** A privileged user may see more or do more; their privilege never makes the underlying record more true.
