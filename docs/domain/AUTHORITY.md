# ARGUS Authority and Visibility Specification

- **Document version:** 0.1.0 (Slice 1F-B gate, incorporating the five AGC Session 020 amendments)
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md) 1.18.0 (ONT-PRN-029, ONT-PRN-030) via the [Derivation Specification](DERIVATION_SPECIFICATION.md), building on ONT-PRN-028 (authenticated identity) and the Slice 3A/1E visibility envelope
- **Consumed by:** the authority decision (`argus.domain.authority`), its PostgreSQL rendering (`argus_private.authorize`), the transport authority provider (`argus.api`), and the H11 suite (triangulation leg 3, ONT-PRN-015)

**The governing rule (AGC Session 020):** *Authority may change the projection a principal is permitted to receive and the actions they are permitted to invoke. It must never change the constitutional record being projected.* And the visibility corollary: *withholding must be explicit when existence may be known — but secrecy itself must not become an existence leak.*

## 1. Scope

Slice 1F-B adds no epistemic object and no representational dimension. It answers two questions 1F-A left open — *may this principal perform this action?* (action authority) and *may this principal see this information?* (visibility authority) — kept distinct, because they diverge. It never touches epistemic standing: a privileged user may see or do more; their privilege never makes the underlying record more true (ONT-PRN-029).

## 2. Capabilities — closed, exact, no inheritance (Amendment 1)

The capability set is closed for 1F-B. Each stands alone: **there is no implicit capability inheritance.** `SEALED_METADATA_READ` does not imply `SEALED_CONTENT_READ`; `SEALED_CONTENT_READ` does not imply `SEALED_VERIFY`; `CASE_READ` does not imply any action capability.

**Action authority** (each authorizes exactly one constitutional command; the broad `CASE_WRITE` is deliberately **not a constitutional check** — the decision function evaluates the narrowest meaningful capability, per least privilege):

| Capability | Authorizes | Does not authorize |
|---|---|---|
| `OBSERVATION_CREATE` | creating an Observation | any other create, any retraction, any disposition |
| `INTERPRETATION_CREATE` | creating an Interpretation | — |
| `HYPOTHESIS_CREATE` | creating a Hypothesis | — |
| `UNKNOWN_RESOLVE` | resolving an Unknown | creating one, linking one |
| `CONTRADICTION_DISPOSE` | disposing a Contradiction | creating one, linking one |
| `RETRACTION_PERFORM` | retracting a class-V record | any creation |

**Visibility authority:**

| Capability | Authorizes | Does not authorize |
|---|---|---|
| `CASE_READ` | knowing a Case's records exist; reading non-protected fields | reading SEALED metadata or content |
| `SEALED_METADATA_READ` | the withheld metadata of a SEALED artifact | its content bytes |
| `SEALED_CONTENT_READ` | receiving SEALED content bytes (audited) | invoking verification |
| `SEALED_VERIFY` | invoking integrity verification that internally reads bytes; receiving the integrity *result* only | receiving the content bytes themselves |

## 3. Resource scope — Case only (Amendment 5)

Every grant is `scope_type = CASE`, `scope_id = <case_id>`. **The global `*` scope is NOT authorized in 1F-B** (it becomes an implicit administrator — the broad privilege this slice exists to prevent). Future scopes (`ORGANIZATION`, `GLOBAL`, `RESOURCE`) do not exist until their containment semantics are defined. A grant for Case A never authorizes Case B; test infrastructure needing universal access generates explicit per-Case grants.

## 4. The authority decision (dual-rendered)

A pure function, rendered in Python (`argus.domain.authority.authorize`) and PostgreSQL (`argus_private.authorize`), conformance-swept over the same normalized grant facts:

```
authorize(required_capability, resource_case_id, grants) -> AuthorityDecision
AuthorityDecision: ALLOW | DENY(reason)
```

Reasons (no scoring, no trust level, no confidence, no partial authority):

- `CAPABILITY_NOT_GRANTED` — no grant carries the required capability at all.
- `RESOURCE_SCOPE_MISMATCH` — a grant carries the capability but for a different Case.

`UNAUTHENTICATED` is handled before `authorize` (authority presupposes identity, ONT-PRN-028). The enforcement layer maps outcomes to canonical codes: `ONT-PRN-007:unauthenticated`; `ONT-PRN-029:action-not-authorized` / `ONT-PRN-029:visibility-not-authorized` (per whether the capability is an action or visibility one); `ONT-PRN-029:out-of-scope-resource`.

## 5. The two-stage visibility ladder (Amendment 2)

Visibility is **separately derived**, not forced through the action binary. Withholding is exposed **only once existence may be disclosed** — otherwise explicit withholding itself leaks sensitive existence:

```
no CASE_READ            -> resource not disclosed (generic denial; existence not leaked)
CASE_READ               -> existence visible; protected fields explicitly withheld
+ SEALED_METADATA_READ  -> permitted SEALED metadata visible
+ SEALED_CONTENT_READ   -> content visible (via the content endpoint; audited)
```

The projected artifact envelope (richer than the base reconstruction's, which stays unchanged for H8):

```
visibility:
  state: FULL | SEALED
  existence_visible: true          # the endpoint is CASE_READ-gated; existence is disclosable
  metadata_visible: <bool>         # FULL: true; SEALED: has SEALED_METADATA_READ
  content_visible: <bool>          # FULL: true; SEALED: has SEALED_CONTENT_READ
  withholding_basis: null | AUTHORITY_REQUIRED
```

The underlying constitutional record is **singular**; only the projection changes (O14). A principal with no `CASE_READ` receives a generic resource denial — never a SEALED envelope that would confirm the artifact exists.

**Refined ONT-PRN-030 (normative):** *When a principal is authorized to know that a constitutional record exists but lacks authority to view protected portions of that record, the system must represent withholding explicitly rather than representing the record as absent.* Absence of access becomes explicit withholding only inside the entitled-to-existence stage.

## 6. Protected-content access: audit before disclosure (Amendment 3)

Reading SEALED content under `SEALED_CONTENT_READ` is the first read that appends audit history — a bounded refinement of the "ordinary reads are pure" principle (Slices 3A/1E): the *evidence* is untouched and byte-identical; the *access record* is a new fact. **Content is disclosed only when access attribution has been durably recorded:**

```
authorize(SEALED_CONTENT_READ, case, grants)
  -> attempt protected read into memory
  -> append 'sealed-content-accessed' audit event  (attributed to the principal)
  -> commit the audit transaction
  -> return bytes
```

Because object-store reads and PostgreSQL writes cannot be one transaction, the consistency boundary is stated honestly: **if the audit append fails, the content is not returned**; if the read fails, no success event is recorded (a `sealed-content-access-failed` event is appended when a failed *authorized* attempt is to be recorded). The definition of protected access is therefore: *authorized + content successfully retrieved + access attribution durably recorded = content may be disclosed.* The evidence object remains byte-identical either way.

## 7. SEALED_VERIFY without SEALED_CONTENT_READ (Amendment, verification)

`SEALED_VERIFY` authorizes invoking integrity verification that internally reads bytes for the integrity computation; the principal receives the **integrity result only**, never the bytes. Verification authority does not imply disclosure authority. And the Slice 1E doctrine survives elevation: the result is *storage integrity* (`MATCHED`/`DIVERGENT`/… , ONT-PRN-026), **never authenticity** — `MATCHED` means the bytes match the recorded digest, not that the evidence is authentic.

## 8. The AuthorityProvider returns facts, never decisions (Amendment 4)

`AuthorityProvider` (a protocol; one declared dev/test implementation for 1F-B, persisted grants deferred) returns only normalized grant facts:

```
AuthorityGrant: principal_id, capability, scope_type (CASE), scope_id
```

It must not return `ALLOW`/`DENY`, interpret epistemic state, inspect record truth, decide a visibility outcome, decide an action outcome, or silently expand capability scope. The provider answers *what grants exist?*; the dual-rendered `authorize` answers *do those grants authorize this action on this resource?* If the provider decided, the triangulated decision layer would be ceremonial.

## 9. Non-effects and epistemic neutrality

Authority grants and denials mutate no stored field, no derived state, no admissibility, and no reconstruction epistemic content. Two principals with different visibility receive **identical epistemic state for the fields both may see** (the O14 falsifier). A denied action writes nothing. **Trusted-internal execution is not user authority** (the Session 019 boundary, fixed here): the no-principal internal context is infrastructure; an authenticated user lacking a capability is denied by the authority layer, never satisfied by an internal bypass.

## 10. Verifying tests

The H11 suite transcribes this specification: the seventeen acceptance tests (twelve from Session 019 plus the five Session 020 additions — no existence leak without CASE_READ; protected content withheld if audit persistence fails; SEALED_VERIFY without SEALED_CONTENT_READ; capability non-inheritance; provider-facts-not-outcome + dual-render conformance), and the O14 falsifier (different projections, singular record, identical shared epistemic fields).

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative specification at the Slice 1F-B gate, incorporating the five AGC Session 020 amendments: closed exact capabilities with no inheritance, the two-stage visibility ladder (secrecy is not an existence leak), audit-before-disclosure for protected content, the facts-only AuthorityProvider, and Case-scope-only grants. |
