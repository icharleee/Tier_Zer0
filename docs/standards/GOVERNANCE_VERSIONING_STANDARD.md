# Governance Versioning Standard

- **Document version:** 1.0.0
- **Status:** Active
- **Established by:** [ADR-0008](../adr/0008-establish-arb-and-documentation-governance.md)

## Scope

This standard applies to governance documents: the Project Brief, the Engineering Constitution, ISS research papers, implementation Standards (including this one), and the ARGUS Lexicon.

It does **not** apply to ADRs. ADRs are immutable and unversioned — they are superseded, never revised.

## Versioning rules

Governance documents carry a semantic version `MAJOR.MINOR.PATCH`:

| Component | Increment when |
|---|---|
| **MAJOR** | The philosophy or meaning changed. A reader holding the old version would be *misled* about what ARGUS believes or requires. |
| **MINOR** | An article, definition, or section was expanded or added. The old version is incomplete but not wrong. |
| **PATCH** | Grammar, clarification, or wording. No semantic change; a careful reader of both versions reaches identical conclusions. |

## Requirements

1. Every governed document declares its version in a header near the top (`Document version: X.Y.Z`).
2. Every governed document keeps a **Version history** table: version, date, nature of change.
3. Semantic changes (MAJOR, and MINOR where the addition is architecturally significant) to the Constitution or the Project Brief additionally require an ADR, per ADR-0001.
4. Semantic changes to Lexicon definitions are MAJOR for that document and require Architecture Review Board review; adding a new term is MINOR.
5. Draft documents version as `0.Y.Z` until first ratification at `1.0.0`.
6. Version history is append-only. Nothing disappears.

## Version history

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-13 | Initial standard, established by ADR-0008 / Founder Resolution 002. |
