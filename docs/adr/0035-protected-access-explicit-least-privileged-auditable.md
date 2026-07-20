# ADR-0035: Protected access is explicit, least-privileged, attributable, and auditable

- **Status:** Accepted (Founder Resolution 025, AGC Review Session 019 — freeze exemption per ONT-PRN-011: the access-discipline constraint for Slice 1F-B, proposed at the Slice 1F-A completion review)
- **Date:** 2026-07-13
- **Constitutional articles:** VI (Privacy and legal authority), VIII (Justice requires transparency), IX (Certainty never exceeds evidence)
- **Supersedes:** none (pairs with ADR-0034; carries the Slice 3A/1E visibility-envelope discipline into enforced access)

## Context

Slice 3A and 1E established that a SEALED artifact is *existence-plus-status with its withholding declared* — never silently omitted. Slice 1F-B turns that from a rendering convention into an enforced access decision: some principals will be authorized to read protected content, most will not. The failure mode to prevent: letting a lack of access read as a lack of evidence. A user who cannot see content must learn *record exists, content withheld, authority insufficient* — not *record absent*.

## Decision

Founder Resolution 025 is recorded (stable identifier **ONT-PRN-030**):

> **Access to protected information must be explicit, least-privileged, attributable, and auditable; absence of access must never be represented as absence of evidence.**

Normative consequences:

1. **Explicit withholding preserves a singular record** (O14). An unauthorized principal receives the visibility envelope (`state: SEALED`, `content_visible: false`, `withholding_basis: AUTHORITY_REQUIRED`), never omission. There are not two epistemic realities — one record, differently visible.
2. **Protected-content access is a read that alters no epistemic state but appends to access history.** This refines the earlier "ordinary reads are pure" principle (Slices 3A/1E): an *ordinary* constitutional read still emits no audit mutation; **protected-content access** is read-only with respect to the evidence yet **appends an access event** to the audit history. The evidence object remains byte-identical; the access record is a new fact. That is not a contradiction — the read does not change the evidence, it changes the record of who looked.
3. **Least privilege, resource-scoped, attributable.** Access capabilities are the minimum required, bound to a resource, and attributed to the authenticated principal (ONT-PRN-028). `SEALED_CONTENT_READ` and `SEALED_VERIFY` are **distinct** capabilities — inspecting content and running a verification process are not the same grant.
4. **The Slice 1E doctrine survives elevated access.** `SEALED_VERIFY` under authority still classifies *storage integrity*, never *authenticity* (ONT-PRN-026): "verification succeeded" means the bytes match the recorded digest, not that the evidence is authentic.

## Governance review

1. **Constitutional Review** — PASS: Article VIII — every protected access is visible and attributable in the audit history; Article VI — sealed material is reachable only through explicit, least-privileged, audited authority; Article IX — access never converts into authenticity or truth.
2. **Domain Review** — PASS: extends the visibility envelope (ADR-0024/3A) into an enforced, audited decision; the `SEALED_CONTENT_READ` / `SEALED_VERIFY` split mirrors the eligibility-vs-sufficiency discipline (ONT-PRN-014).
3. **Architectural Review** — PASS: the access-event-on-protected-read is the first legitimate read that appends audit history; documented as a deliberate, bounded refinement rather than an erosion of read purity.

## Consequences

- Slice 1F-B introduces the protected-access audit event and the `SEALED_METADATA_READ` / `SEALED_CONTENT_READ` / `SEALED_VERIFY` capability distinctions; the H11 experiment proves access emits the event while the evidence stays byte-identical, and that denial yields explicit withholding, never absence.
- The reconstruction and reconciliation surfaces gain an authority-aware rendering path that still never omits a record silently.

## Alternatives considered

- **Omit records a principal cannot fully see** — rejected: absence of access misread as absence of evidence; the visibility envelope is mandatory.
- **Treat protected reads as fully pure (no access event)** — rejected: Article VIII requires protected access to be attributable and auditable; the access history is exactly what makes sealed material safe to expose at all.
- **One SEALED capability for both viewing and verifying** — rejected: viewing content and running verification are different powers under different future policy.

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

**Affected Articles:** VI, VIII, IX (protected access made explicit, least-privileged, and auditable; absence of access kept distinct from absence of evidence). Others untouched.

**Compliant?** YES

**Explanation:** A user who may not see content learns that the content exists and is withheld — never that it is absent — and every authorized look is itself a recorded fact.
