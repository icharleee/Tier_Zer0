#!/usr/bin/env python3
"""Constitutional Coverage reporter — skeleton (ADR-0007 §8).

Alongside code coverage, ARGUS reports per-article test coverage: an article
is covered when at least one test cites an ontology identifier mapped to it
(ADR-0010: every domain test declares the rule it protects). A future
Verification Standard formalizes the mapping; this skeleton makes the metric
exist from the first slice.

Usage: python tools/constitutional_coverage.py [tests-dir]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Article -> ontology identifiers whose tests evidence that article.
# Mapping v0 (slice 1); grows with the ontology and the slices.
ARTICLE_MAP: dict[str, list[str]] = {
    "Article I — Evidence before opinion": ["ONT-PRN-005", "ONT-EVA-001"],
    "Article II — Human judgment is final": ["ONT-PRN-007"],
    "Article III — Conclusions explain themselves": ["ONT-PRN-005", "ONT-AUD-001"],
    "Article IV — Alternatives remain possible": ["ONT-INT-001", "ONT-HYP-001"],
    "Article V — Evidence is immutable": ["ONT-EVA-001", "ONT-PRN-006"],
    "Article VI — Privacy and legal authority": ["ONT-CAS-001"],
    "Article VII — Scientific integrity": ["ONT-PRN-009", "ONT-PRN-012"],
    "Article VIII — Justice requires transparency": ["ONT-AUD-001", "ONT-PRN-012"],
    "Article IX — Certainty never exceeds evidence": ["ONT-PRN-002", "ONT-UNK-001"],
}

ONT_RE = re.compile(r"ONT-[A-Z]{3}-\d{3}")


def main() -> int:
    tests_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[1] / "tests"
    cited: set[str] = set()
    for path in tests_dir.rglob("test_*.py"):
        cited.update(ONT_RE.findall(path.read_text()))

    print("Constitutional Coverage (v0 skeleton)")
    print("=" * 54)
    covered = 0
    for article, ids in ARTICLE_MAP.items():
        hits = sorted(set(ids) & cited)
        status = "COVERED" if hits else "uncovered"
        if hits:
            covered += 1
        print(f"{status:>9}  {article}")
        if hits:
            print(f"           via {', '.join(hits)}")
    print("=" * 54)
    print(f"{covered}/{len(ARTICLE_MAP)} articles have at least one citing test.")
    print(f"Ontology identifiers cited anywhere in tests: {len(cited)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
