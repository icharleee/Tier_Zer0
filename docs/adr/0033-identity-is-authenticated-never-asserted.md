# ADR-0033: Identity is authenticated, never asserted

- **Status:** Accepted (Founder Resolution 023, AGC Review Session 018 — freeze exemption per ONT-PRN-011: the governing constraint for Slice 1F-A, ratified at its gate)
- **Date:** 2026-07-13
- **Constitutional articles:** II (Human judgment is final), VI (Privacy and legal authority), VIII (Justice requires transparency)
- **Supersedes:** none (closes the Slice 1B trust-boundary limit that actor identity was asserted by the trusted service)

## Context

From Slice 1B onward, ARGUS recorded a known trust-boundary limit: the domain `actor_id` attributed to every constitutional action was a free string *asserted* by the trusted Python service. Authentication was deferred slice after slice; Session 017 placed it first in the 1F decomposition. Slice 1F-A closes the limit — the point where a domain `Actor` stops being a caller-supplied string and becomes something *derived from an authenticated principal*.

The distinction this ADR fixes is foundational for everything 1F-B and 1F-C build: **authentication answers who presented the request — it does not answer what that actor may do, what they may see, or whether anything they create is true.**

## Decision

Founder Resolution 023 is recorded (stable identifier **ONT-PRN-028**):

> **Identity is authenticated, never asserted.** The actor attributed to a constitutional action must derive from an authenticated principal context established at a trusted transport boundary and must never be determined, overridden, or substituted by caller-controlled payload data.
>
> **Corollary (attribution only):** Authentication establishes attribution only. It confers no authority, no access, no credibility, no evidentiary weight, and no epistemic standing.

The corollary is not decorative. Without it, later code could quietly read *authenticated human* as *trusted human* or *authorized human* — different concepts. An authenticated principal's records are neither more permitted nor more true by virtue of authentication.

Normative consequences (detailed in [ACTOR_CONTEXT.md](../domain/ACTOR_CONTEXT.md)):

1. **Three distinct layers, one identity invariant** (the ONT-PRN-015 discipline applied to identity): the transport boundary *proves* a principal; the domain *derives* the actor; the persistence layer *verifies* the two agree at execution time. Authentication itself is a declared single-implementation surface (the database cannot verify an HTTP credential); the binding rule is triangulated.
2. **Identity fields are absent from constitutional command schemas.** A caller-controlled command carries no `actor_id`, `created_by`, `human_authority`, or `principal_id`; where a client supplies one anyway, the request is refused — matching an authenticated identity by payload is still payload assertion.
3. **Attribution ≠ authority.** Any human identity carried alongside a SERVICE principal is *attribution metadata only*; it is never proof that the human authorized the current action. (The legacy `Actor.human_authority` field name is retained for schema compatibility; its 1F-A meaning is narrowed to attribution and flagged for 1F-B review.)
4. **The persistence guard fails closed** within the authenticated application transaction: transaction-scoped principal context (`SET LOCAL`, never a persistent GUC on a pooled connection); no fallback to caller-supplied identity for transport-originated writes. Trusted internal fixture/bootstrap transactions are a distinct, explicitly documented execution context to which H10 does not apply.

## Governance review

1. **Constitutional Review** — PASS: Article VI (identity is a precondition of authority and access, established rigorously) and Article VIII (attribution in the audit trail becomes trustworthy) served, while Article IX is protected by the attribution-only corollary — authentication manufactures no credibility.
2. **Domain Review** — PASS: extends the ladder's separation discipline (Evidence ≠ Observation ≠ Interpretation) to *authentication ≠ actor attribution ≠ authority ≠ epistemic meaning*; no epistemic object is added or changed.
3. **Architectural Review** — PASS: enforceable at three independent layers required to agree; testable (binding matrix dual-rendered; refusal codes; the principal-leak and fail-closed tests); reversible before implementation.

## Consequences

- Slice 1F-A ships the identity seam only: the authenticated principal model, the binding rule, the FastAPI transport boundary, and the database principal guard. Authority and visibility (SEALED access, elevated verification, case access) are **1F-B**; the visible review surface is **1F-C**.
- Every later constitutional command surfaced through the authenticated API inherits the binding rule and the guard; extending the guard across all mutation paths is mechanical follow-on as each command is exposed.

## Alternatives considered

- **Accept an `actor_id` field and compare it to the principal** — rejected (Amendment 3): teaches clients that identity belongs in payloads; the stronger rule is that constitutional command schemas contain no identity field at all.
- **A persistent connection GUC for the principal** — rejected (Amendment 4): principal leakage across pooled connections; `SET LOCAL` transaction scope is mandatory.
- **Audit-append as the sole enforcement point** — rejected (Amendment: guard placement): the principal check belongs at the beginning of the constitutional mutation path; audit-layer checking remains only as defense-in-depth.

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

**Affected Articles:** II, VI, VIII (attribution made trustworthy without conferring authority or credibility). Others untouched.

**Compliant?** YES

**Explanation:** ARGUS may trust the authentication boundary to tell it who is acting; it may not trust the actor to tell ARGUS who they are — and knowing who acted is never confused with deciding whether they were allowed to act, or whether what they created is true.
