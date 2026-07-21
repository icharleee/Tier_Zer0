"""The review-surface renderer (Slice 1F-C; ONT-PRN-031).

Pure and downstream of authority: render_case_review takes ONLY the
authorized projection. It holds no grants, imports no authority module,
and makes no authority decision of any kind — the presentation layer may
defensively omit fields absent from its input, but it can never expand
visibility beyond the projection or reinterpret grant facts
(CASE_PRESENTATION.md §8).

The view model performs closed label mapping and visibility-safe
formatting only; the template is thin. Neither prioritizes, sorts by
health, summarizes, infers relationships, or generates narrative — the
authorized projection, not the template, is the source of constitutional
content.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
)

# Closed neutral definitions (CASE_PRESENTATION.md §7): descriptive of
# state, never of truth.
STATE_DEFINITIONS = (
    ("CURRENT", "Every required derivational foundation remains current."),
    ("DEGRADED", "One or more derivational foundations are no longer current."),
    ("UNSUPPORTED", "No required derivational foundation remains current; the historical record is preserved and awaits human review."),
    ("CHAIN_VALID", "The append-only audit chain passed its integrity verification. This describes chain integrity only — never the truth of any record."),
    ("CHAIN_INVALID", "The append-only audit chain failed its integrity verification. The records remain presented; the integrity problem is surfaced."),
)


def render_case_review(projection: dict) -> str:
    """Render the authorized projection as the read-only review page."""
    template = _env.get_template("case_review.html")
    retracted_hypotheses = sum(
        1 for h in projection.get("hypotheses", []) if h.get("retraction")
    )
    return template.render(
        p=projection,
        retracted_hypotheses=retracted_hypotheses,
        state_definitions=STATE_DEFINITIONS,
    )
