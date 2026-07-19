# ARGUS Authenticated Actor Context Specification

- **Document version:** 0.1.0 (Slice 1F-A gate, incorporating the four AGC Session 018 amendments)
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md) 1.17.0 (ONT-PRN-028) via the [Derivation Specification](DERIVATION_SPECIFICATION.md), with the actor model from the [Domain Schema Specification](DOMAIN_SCHEMA_SPECIFICATION.md) C1 and ADR-0033
- **Consumed by:** the domain binding rule (`argus.domain.actor_binding`), the transport boundary (`argus.api`), the database principal guard (`argus_private.assert_transaction_principal`), and the H10 suite (triangulation leg 3, ONT-PRN-015)

**The governing rule (AGC Session 018):** *ARGUS may trust the authentication boundary to tell it who is acting. It may not trust the actor to tell ARGUS who they are.* And the corollary: *knowing who acted must never be confused with deciding whether they were allowed to act — or whether what they created is true.*

## 1. Scope — identity only

Slice 1F-A adds no epistemic object and no representational dimension. It adds the seam beneath every existing actor: where a domain `Actor` stops being a caller-supplied string and becomes something derived from an authenticated principal. It is **identity only**. It decides *who* is acting — never *what* they may do or see (authority/visibility, deferred to 1F-B), never how state is presented (1F-C), and never the epistemic standing of anything (Article IX). Four concepts are kept distinct, and the handoff is clean:

```
authentication      →   who authenticated?        (this slice: the transport boundary proves it)
actor attribution   →   who is attributed?        (this slice: derived from the principal)
authority           →   what may they do or see?  (1F-B)
epistemic meaning   →   is what they made true?    (never — Article IX)
```

## 2. The AuthenticatedPrincipal (Amendment 2)

Established **only** by a `PrincipalVerifier` from a trusted transport credential — never constructed from request data. It carries only the authenticated identity facts 1F-A needs:

```
AuthenticatedPrincipal:
  principal_id            # the verified identity
  principal_class         # HUMAN | SERVICE
  authentication_method   # how the principal was proven (e.g. "dev-token")
  human_attribution?      # SERVICE only: the human identity associated with a
                          # mechanical action, for traceability
```

It carries **no** permission set, **no** case access, **no** visibility grants, **no** sealed-content rights — those are 1F-B. `human_attribution` is **attribution metadata only**: it must never be interpreted as proof that the human authorized the current action. (The domain `Actor.human_authority` field name is retained for schema compatibility; its 1F-A meaning is narrowed to attribution and flagged for 1F-B review — an authenticated service must not smuggle an authority model into an attribution field.)

The `PrincipalVerifier` is a protocol. Slice 1F-A ships one implementation — a dev/test credential verifier — **declared as a single implementation** (the honest bound, §6); production identity providers are protocol-bound followers, exactly as MinIO follows the ContentStore contract. The verifier returns authenticated identity facts only; it never returns permissions, access, or credibility.

## 3. The binding rule

`bind_actor(principal, *, requires_class) → Actor | refusal`, a pure function:

- **HUMAN** principal → `Actor(HUMAN, actor_id = principal_id)`.
- **SERVICE** principal performing a mechanical SystemProcess action → `Actor(SYSTEM, actor_id = principal_id, human_authority = principal.human_attribution)` — the human identity traces to what the service was provisioned with (authenticated at provisioning), never a payload value.
- No path constructs an `Actor` whose `actor_id` or `human_authority` comes from request data.
- If the action requires a class the principal cannot satisfy (e.g., a HUMAN-only transition requested by a SERVICE principal) → refusal `principal-class-mismatch`.

The endpoint layer must **never** construct `Actor(...)` directly from request fields; it calls `bind_actor` on the verified principal. Transport authentication (`api/authentication.py`, `api/dependencies.py`) and domain attribution (`domain/actor_binding.py`) live in separate modules so the separation stays visible in the code.

## 4. Identity-free command schemas (Amendment 3)

Constitutional command schemas contain **no identity field**. A `CreateCaseRequest` is `{title, legal_authority_basis}`, never `{title, actor_id, …}`. The transport dependency supplies the principal separately. Two situations are distinguished normatively:

- **Any caller-controlled identity field present** (`actor_id`, `created_by`, `human_authority`, `principal_id`, or any extra field, under strict parsing) → refuse `identity-input-prohibited`. This is refused **even when the supplied identity matches the authenticated principal** — matching caller assertion is still caller assertion; identity is transport-derived, not payload-confirmed.
- **No identity field** (the normal path): `credential → verified principal → actor binding → domain action`.

`identity-substitution` is reserved for a legacy/compatibility path that explicitly includes a claimed identity conflicting with the principal; 1F-A's new schemas forbid the field outright, so `identity-input-prohibited` is the code new command paths emit.

## 5. The database principal guard (Amendment 4)

Defense-in-depth at the persistence boundary, generalizing the O12 lesson (integration constraints as discovery instruments) to identity. The service, inside the request transaction, binds the principal with **`SET LOCAL`** — transaction-scoped, never a persistent GUC on a pooled connection (principal leakage across pooled connections is the failure class this prevents):

```
SET LOCAL argus.actor_principal        = <principal_id>
SET LOCAL argus.actor_principal_class  = <principal_class>
SET LOCAL argus.human_attribution      = <human_attribution or ''>
```

`argus_private.assert_transaction_principal(p_actor_class, p_actor_id, p_human_attribution)` runs at the **beginning of the constitutional mutation path** (not only at audit append — a badly structured function could otherwise mutate before the check):

1. No principal context bound → `ONT-PRN-007:unauthenticated` (**fail closed**). The authenticated application transaction always binds a principal before mutating; there is no fallback to a caller-supplied identity for transport-originated writes.
2. Bound principal inconsistent with the actor — HUMAN actor_id ≠ bound principal_id, or class disagreement, or SERVICE human_attribution ≠ bound attribution → `ONT-PRN-007:actor-principal-mismatch`.
3. Consistent → proceed.

`argus_private.append_audit_event` additionally verifies consistency **when** a principal is bound, as defense-in-depth — never as the first line.

**Honest trust-boundary statement** (in the spirit of the Slice 1B audit-chain language): the trusted service sets both the GUC and the function arguments, so this guard does **not** establish independent authentication and does not defend against a fully-compromised service that lies consistently to both. It detects *inconsistency* between the bound principal and the attributed actor — precisely the class the storage_ref defect belonged to — and makes the binding invariant checkable at the persistence boundary rather than only in application code.

**Trusted internal context.** Existing non-API fixture, bootstrap, migration, and offline-maintenance transactions do not bind a principal and do not call `assert_transaction_principal`; they are a distinct execution context to which H10 does not apply. This is not a fallback reachable from the transport boundary — the API path always binds a principal. Future maintenance processes needing this context receive an explicit `trusted_internal_process` marker with separately documented semantics; the guard is never weakened to accommodate them.

## 6. Honest bounds and dual rendering

As H9 separated single-implementation *probing* from dual-rendered *classification*, 1F-A separates:

- **Authentication** (declared single implementation, stated in every H10 report): credential → `AuthenticatedPrincipal`.
- **The binding rule** (the triangulated pair): a pure function from `(principal, requires_class)` to `Actor | refusal`, rendered in Python and transcribed as the canonical matrix; the database guard independently enforces the actor↔principal consistency subset.

## 7. Canonical refusal matrix

| Condition | Code | Layer |
|---|---|---|
| No verified principal on a constitutional command | `ONT-PRN-007:unauthenticated` | transport, DB guard |
| Caller-controlled identity field present (even matching) | `ONT-PRN-007:identity-input-prohibited` | transport (schema) |
| Legacy/compat path claims an identity conflicting with the principal | `ONT-PRN-007:identity-substitution` | binding |
| Action requires a class the principal cannot satisfy | `ONT-PRN-007:principal-class-mismatch` | binding |
| Recorded actor inconsistent with the transaction-bound principal | `ONT-PRN-007:actor-principal-mismatch` | DB guard |

## 8. Non-effects

Authentication, binding, and the guard are pure with respect to constitutional state: verifying a principal and binding an actor mutate nothing, emit no audit event, and create no record. Rejected commands write nothing and audit nothing (a rejection may be separately recorded via the existing `record_rejection` path in its own transaction, unchanged by this slice). Binding decides who is acting; it never alters any record's epistemic fields or derived states — a record authored under an authenticated principal is byte-for-byte epistemically identical to the same record authored under the pre-1F-A path (only attribution/audit fields carry the identity).

## 9. Verifying tests

The H10 suite transcribes this specification: the binding matrix; TestClient refusals (unauthenticated, identity-input-prohibited including the matching-identity case, principal-class-mismatch); SERVICE `human_attribution` provenance; the DB guard mismatch and the **principal-leak-across-transactions** test (SET LOCAL scope); purity; binding-rule conformance; the structural authentication ≠ authorization test (the principal carries no permission set; `bind_actor` performs no resource authorization); and the symmetric identity ≠ epistemic meaning test (two authenticated authors, identical epistemic fields and derived predicates, differences confined to attribution/audit).

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative specification at the Slice 1F-A gate, incorporating the four AGC Session 018 amendments: attribution-only principal separated from authority semantics, identity-free command schemas (refuse even matching caller identity), the SET LOCAL fail-closed database principal guard placed at mutation entry, and the honest single-implementation authentication bound. |
