"""Presentation-conformance scanner (Slice 1F-C; CASE_PRESENTATION.md §12).

Checks a rendered page against the authorized projection it claims to
present. The scanner is the tripwire, not the whole defense: reviews still
judge semantics (ONT-PRN-018 discipline applied to markup). It is part of
the deliverable — the same instrument runs against the production page and
against red-team fixtures that must fail it (the O12 discipline applied to
presentation).

Implemented on the stdlib HTML parser so the runtime package gains no
dependency; the H12 test suite layers richer structural assertions on top
with BeautifulSoup (test-only).
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

# Transcribed from CASE_PRESENTATION.md §9 — attribute/class/id/data-*/
# aria-label/title stems that create hidden epistemic hierarchy.
ATTRIBUTE_STEMS = (
    "featured", "best", "primary", "leading", "preferred", "winner",
    "confiden", "probab", "truth", "true-state", "false-state", "rank",
    "score", "weight", "verdict", "accept", "approve", "confirm",
    "validat", "likel",
)
SCANNED_ATTRIBUTES = ("class", "id", "aria-label", "title")  # plus every data-*

# Transcribed from CASE_PRESENTATION.md §9 — conservative visible-text
# phrases that would synthesize preference or conclusions.
VISIBLE_PHRASES = (
    "primary hypothesis", "leading hypothesis", "best explanation",
    "main hypothesis", "preferred", "winner", "confidence", "probability",
    "accepted", "approved", "confirmed", "validated", "more likely",
    "less likely", "weakened by", "is weaker", "is stronger",
    "this hypothesis is less reliable",
)

_CITATION_RE = re.compile(r"Hypothesis — (HYP-\d{6})")


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.attr_values: list[tuple[str, str]] = []  # (attribute, value)
        self.details_open: list[bool] = []
        self._skip_depth = 0
        self.text_chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip_depth += 1
        if tag == "details":
            self.details_open.append(any(a == "open" for a, _ in attrs))
        for name, value in attrs:
            if value is None:
                continue
            if name in SCANNED_ATTRIBUTES or name.startswith("data-"):
                self.attr_values.append((name, value))

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth and data.strip():
            self.text_chunks.append(data)


def _parse(html: str) -> _Page:
    page = _Page()
    page.feed(html)
    return page


def scan_presentation(html: str, projection: dict) -> list[str]:
    """Return the list of constitutional violations found (empty = clean)."""
    violations: list[str] = []
    page = _parse(html)
    visible = " ".join(page.text_chunks)
    visible_lower = visible.lower()

    # 1. Attribute contamination (hidden semantics need no visible word).
    for name, value in page.attr_values:
        low = value.lower()
        for stem in ATTRIBUTE_STEMS:
            if stem in low:
                violations.append(f"attribute-contamination: {name}='{value}' (stem: {stem})")

    # 2. Visible-phrase contamination (synthesized preference/conclusion).
    for phrase in VISIBLE_PHRASES:
        if phrase in visible_lower:
            violations.append(f"phrase-contamination: '{phrase}'")

    hypotheses = projection.get("hypotheses", [])

    # 3. Citation order: hypothesis cards appear in projection (citation)
    #    order — the only authorized order.
    rendered = _CITATION_RE.findall(visible)
    expected = [h["citation"] for h in hypotheses]
    if rendered != expected:
        violations.append(
            f"order-violation: hypotheses rendered {rendered}, projection order {expected}"
        )

    # 4. Completeness and single occurrence: every explanatory statement
    #    exactly once (repetition must not become prominence; absence is
    #    concealment).
    for h in hypotheses:
        n = visible.count(h["explanatory_statement"])
        if n == 0:
            violations.append(f"completeness-violation: {h['citation']} statement absent")
        elif n > 1:
            violations.append(
                f"duplication-violation: {h['citation']} statement appears {n} times"
            )

    # 5. Retraction visibility: retracted records carry the explicit label
    #    and their reason; collapse is never concealment.
    for h in hypotheses:
        if h.get("retraction"):
            if f"{h['citation']}" not in visible or "RETRACTED" not in visible:
                violations.append(f"retraction-hidden: {h['citation']}")
            reason = h["retraction"].get("reason")
            if reason and reason not in visible:
                violations.append(f"retraction-reason-hidden: {h['citation']}")

    # 6. Uniform expansion: if <details> exists, every peer has the same
    #    open state (no card gains prominence through expansion).
    if page.details_open and len(set(page.details_open)) > 1:
        violations.append("expansion-asymmetry: mixed <details> open states")

    return violations
