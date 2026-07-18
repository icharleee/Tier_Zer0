# ADR-0032: No silent repair of constitutional history

- **Status:** Accepted (Founder Resolution 022, AGC Review Session 015 — freeze exemption per ONT-PRN-011: the second governing constraint for Slice 1E, fixed before its gate)
- **Date:** 2026-07-13
- **Constitutional articles:** II (Human judgment is final), V (Evidence is immutable), VIII (Justice requires transparency)
- **Supersedes:** none

## Context

A reconciliation mechanism that can detect a missing or divergent stored representation will be tempted to fix it — restore the copy, rewrite the pointer, refresh the digest. Every such repair is a mutation of constitutional history performed on the system's own initiative. ARGUS already separates detection from disposition everywhere (degraded grounding surfaces and awaits humans; contradictions never auto-dispose; even UNSUPPORTED hypotheses are never auto-retracted). Session 015 extends the same pattern to storage.

## Decision

Founder Resolution 022 is recorded (stable identifier **ONT-PRN-027**):

> **No reconciliation operation may silently repair constitutional history. Detection, proposed remediation, and authorized mutation must remain separate operations.**

The pattern, made explicit: **detect ≠ decide ≠ mutate.**

Normative consequences:

1. A reconciliation scan is a pure read: it reports `MISSING`, `DIVERGENT`, `UNREADABLE` (and the rest of the closed condition set) and mutates nothing — no content, no metadata, no provenance, no lifecycle state, no epistemic record.
2. Restoration or repair, where it ever exists, is an explicit, separately audited, authorized action under its own operation — never a side effect of scanning, and never automatic on detection. (Existing example of the discipline: integrity-failure quarantine is already a distinct audited transition; a scan may inform it, never perform it.)
3. Proposed remediation, if ever modeled, is a proposal object awaiting authorization — not an action.

## Governance review

1. **Constitutional Review** — PASS: Article V — history is not rewritten by daemons; Article II — repair is a judgment; Article VIII — every repair that does occur is visible, attributed, and audited.
2. **Domain Review** — PASS: the third instance of the detect/decide/mutate separation (after boundary surfacing and quarantine disposition); no new ontology required.
3. **Architectural Review** — PASS: structurally enforceable — the scan path holds no write privileges it could misuse (read-only functions, least-privilege roles); repair, when authorized, enters through the controlled-function pattern with its own audit events.

## Consequences

- Slice 1E ships **detection only**; any repair capability sits behind a second, later gate with its own plan, constraints, and audit surface (Session 015: "Detection first. Repair later.").
- The H9 experiment must prove a scan mutates nothing and that a second scan over unchanged storage is identical.

## Alternatives considered

- **Self-healing storage** — rejected: silent repair converts tamper-evidence into tamper-concealment; a corrected copy that hides the fact of corruption destroys exactly what the audit chain exists to preserve.
- **Auto-quarantine on divergence within the scan** — rejected: quarantine is a lifecycle transition with its own audit and actor semantics; the scan informs it, a separate invocation performs it.

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

**Affected Articles:** II, V, VIII (repair as an attributed human-authorized act, never a silent side effect). Others untouched.

**Compliant?** YES

**Explanation:** Makes it structurally impossible for the system to fix its own history without anyone deciding, seeing, or answering for the fix.
