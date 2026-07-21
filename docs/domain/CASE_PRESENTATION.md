# ARGUS Case Presentation Specification

- **Document version:** 0.1.0 (Slice 1F-C gate, incorporating the five AGC Session 022 amendments)
- **Date:** 2026-07-13
- **Derived from:** the [Ontology](ONTOLOGY.md) 1.19.0 (ONT-PRN-031) via the [Derivation Specification](DERIVATION_SPECIFICATION.md), consuming the Slice 1F-B authorized projection (ONT-PRN-029/030) unchanged
- **Consumed by:** the renderer (`argus.presentation`), the presentation-conformance scanner, and the H12 suite (triangulation leg 3, ONT-PRN-015)

**The governing rule (AGC Session 022):** *The interface may help a human find constitutional information. It may not tell the human which constitutional information deserves belief.* Corollary: *nothing becomes more likely, more credible, or more true merely because the interface places it first, makes it larger, repeats it, colors it, or gives it the first focus.*

## 1. Scope and status

One read-only page — `GET /cases/{case_id}/review` — rendering the Slice 1F-B authorized projection. No editing, annotations, case selection, navigation shell, dashboards, review status, approval controls, persistence mutation, or client-side ranking/filters. Review-workflow mutation is NOT AUTHORIZED for H12. The page is a projection of a projection: it has no epistemic standing, no identity, no lifecycle.

## 2. The non-interference rule (Amendment 1)

> **Presentation metadata may describe the structure and visibility of constitutional records, but it may not paraphrase, summarize, infer, evaluate, or synthesize their epistemic content.**

The renderer **may add:** headings; field labels; section landmarks; technical ordering; accessibility descriptions; explicit visibility and retraction labels. It **may not add:** summaries of meaning; generated narrative; inferred relationships; evaluative adjectives; comparative descriptions; explanatory conclusions. `Hypothesis HYP-000002 / Health: DEGRADED / Challenged by: CON-000001` exposes existing state; *"This hypothesis is less reliable because it faces a contradiction"* creates interpretation — the first is required, the second prohibited, and the distinction is part of the content-parity test.

## 3. Content parity: two content classes (Amendment 2)

> **Every epistemically meaningful value in the authorized projection must be represented exactly once in its proper structural context. Any visible value not derived from the projection must belong to the closed presentation vocabulary and must carry no epistemic judgment.**

**Projection-derived content** — preserved exactly (or through a normative display mapping declared here): citations; statements; reasoning; statuses; disposition values; boundary relationships; retraction reasons; current and historical values; visibility state.

**Presentation-only structural content** — introduced only from the **closed presentation vocabulary**: the page title (`Case Review`); section headings (`Case`, `Evidence Artifacts`, `Observations`, `Interpretations`, `Unknowns`, `Contradictions`, `Hypotheses`, `Hypothesis Alternatives`); structural field labels (`Citation`, `Status`, `Statement`, `Method`, `Meaning`, `Reasoning`, `Uncertainty`, `Question`, `Impact`, `Description`, `Scope`, `Basis`, `Members`, `Links`, `Resolution`, `Disposition`, `Health`, `Testability`, `Challenge condition`, `Retraction reason`, `Grounded by`, `Derived from`, `Contextualized by`, `Limited by Unknown`, `Challenged by Contradiction`, `Alternative pair`); temporal labels (`At creation`, `Currently`); visibility labels (`Content withheld`, `Metadata withheld`, `Authority required`); accounting labels (`retracted records present`); and the neutral health/integrity definitions of §7. Anything visible outside these two classes is a violation.

The suite tests **both completeness and unauthorized duplication**: a value absent is a failure; a Hypothesis statement repeated in a summary panel, page header, "key findings" area, or metadata description is also a failure — repetition must not become prominence. (The false-positive guard: `Case Review` appearing in the DOM but not the JSON is *correct*, because it belongs to the closed vocabulary.)

## 4. Peer symmetry: equal presentation rules, not equal dimensions (Amendment 4)

> **Peer records receive equal presentation rules, even when their constitutional content differs in length or structure.**

Required for peers (all live Hypotheses; all Interpretations; likewise per class): same component template; same heading level; same field order; same available controls; same initial collapsed/expanded state; same typography classes; same landmark semantics; same placement rules; **no conditional prominence class based on health, disposition, or identity**. Not required — and truncation to achieve it is prohibited: equal card height; equal text length; equal row counts.

## 5. Retraction visibility (Amendment 5 — preferred structure adopted)

All Hypotheses (and all class-V records) render **in citation order within one section**, retracted ones inline with explicit text — `Status: RETRACTED` and `Retraction reason: …` — never a separate "failed hypotheses" grouping, never styling as discarded/false/disproven, never erasure. The section header carries the visible count (`N retracted records present`) whenever any retracted record exists.

## 6. Expansion, ordering, and identity

- **All constitutional records are initially expanded.** No collapse controls in the H12 reference surface; if `<details>` ever appears, every peer record has the same `open` state.
- **Citation order is the default and only order.** Any future user-selected sort must be non-epistemic and labeled *organizational, not evidentiary*; sorting by health as likelihood is prohibited.
- **Citations are constitutional identity and remain visible.** `Hypothesis — HYP-000001`, never `First Hypothesis`, `Main Hypothesis`, or `Hypothesis #1` — ordinals are a presentation invention that implies sequence or progression.

## 7. Health, integrity, and iconography

`CURRENT`/`DEGRADED`/`UNSUPPORTED` and `CHAIN_VALID`/`CHAIN_INVALID` render as **text labels**; text is the primary and sufficient signal. Prohibited: green-true/red-false color semantics; ✓/✗/⚠ or equivalent icons as the sole or primary signal (conventional icons imply correct/false/dangerous/failed). A neutral marker may supplement the label; the label must stand alone. The page carries the neutral definitions, e.g. *`DEGRADED`: one or more derivational foundations are no longer current* — never *"this hypothesis may be wrong."* Integrity wording remains ONT-PRN-026-true: `CHAIN_VALID` is chain integrity, never "verified evidence."

## 8. Visibility parity: presentation is downstream of authority

> **The presentation layer may enforce defensive omission of fields absent from its input, but it may not independently expand visibility beyond the authorized projection or reinterpret grant facts.**

The flow is `authenticated principal → 1F-B authorized projection → 1F-C presentation`. The renderer receives the projection only: it does not request grants, does not call `authorize()`, and cannot promote a SEALED projection into visible content. Authority logic is never duplicated in templates. The route applies the same generic-denial behavior as 1F-B **before rendering begins** — a principal without `CASE_READ` receives the identical 404, so the page adds no existence channel.

## 9. Contamination: text, attributes, and CSS (Session 022 addition)

The prohibited-vocabulary discipline covers the whole rendered surface — **visible text, class names, IDs, `data-*` attributes, `aria-label`s, and `title`s** — because `<section class="leading-hypothesis">` creates hidden semantics even when no prohibited word is visible. Registry (stems, transcribed by the scanner): attributes/classes — `featured`, `best`, `primary`, `leading`, `preferred`, `winner`, `confiden`, `probab`, `truth`, `true-state`, `false-state`, `rank`, `score`, `weight`, `verdict`, `accept`, `approve`, `confirm`, `validat`, `likel`; visible-text phrases (conservative) — `primary hypothesis`, `leading hypothesis`, `best explanation`, `main hypothesis`, `preferred`, `winner`, `confidence`, `probability`, `accepted`, `approved`, `confirmed`, `validated`, `more likely`, `less likely`, `weakened by`, `is weaker`, `is stronger`, `this hypothesis is less reliable`. CSS class names and selectors are part of conformance review; scanning remains the tripwire, review still judges semantics.

## 10. Accessibility-semantic source parity (Amendment 3 — honest bound)

> **The H12 suite verifies accessibility-relevant source semantics and focus order through static DOM inspection. It does not constitute full browser or assistive-technology conformance testing.**

Static inspection asserts: source order equals intended reading order; heading hierarchy; landmark markup; label relationships; peer depth (sibling cards are peers at the same tree depth); focusable-element order privileging no Hypothesis (initial focus at the page landmark); presence of accessible names; absence of unauthorized controls. It cannot prove browser-computed roles, CSS-visual reordering, clipping behavior, screen-reader interpretation, or live keyboard focus — a later browser-driven adapter (Playwright/Axe or equivalent) may repeat this checklist against a real accessibility snapshot. The term used everywhere is **accessibility-semantic source parity**; claiming full accessibility-tree conformance is NOT AUTHORIZED.

## 11. The renderer and view model

`authorized projection → presentation view model → Jinja2 template`. The view model may perform: closed label mapping; the projection's canonical technical ordering; visibility-safe formatting; grouping by constitutional class. It may not perform: prioritization; health-based sorting; summarization; relationship inference; narrative generation. The authorized projection — not the template — remains the source of constitutional content.

## 12. The conformance scanner and red-team discipline

A presentation-conformance scanner (part of the deliverable, not only the tests) checks a rendered page against a projection: attribute/phrase contamination; hypothesis citation order; completeness and single-occurrence; retraction visibility; uniform expansion state. The red-team obligation (the O12 discipline applied to presentation): **synthetic violating HTML fixtures** — never dangerous variants in the production template — must be shown to fail the scanner, covering at least: a featured-Hypothesis slot; primary/leading vocabulary; health-based ordering; first-card-only expansion; hidden retraction; truth-semantic CSS class; a synthesized summary; mismatched DOM order. Route-level: sealed existence visible without `CASE_READ` fails the generic-denial test.

## 13. Verifying tests

The H12 suite transcribes this specification: the fifteen Session 021 assertions, the five Session 022 additions (no synthesized epistemic content; no unauthorized duplication; CSS/attribute contamination; projection-only authority behavior — the renderer takes only projections and holds no grants/authorize access; peer-rule equality by normalized structural comparison, stronger than shared-template naming), the content-parity sweep in both directions, and the red-team fixture set.

## Version history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-07-13 | Initial normative specification at the Slice 1F-C gate, incorporating the five AGC Session 022 amendments: the non-interference rule, two content classes with a closed presentation vocabulary and single-occurrence parity, honest accessibility-semantic source-parity bounds, peer symmetry as equal rules not equal dimensions, and inline retraction visibility. |
