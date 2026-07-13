# The ARGUS Research Corpus

This directory holds ARGUS's research — the project's equivalent of scientific papers. Research papers develop theory; they are **not implementation documents**, and they justify concepts before those concepts are engineered.

Per AGC Review Session 002, the corpus contains **two independent research programs**:

## Investigation Systems Science (ISS)

*Asks: how do investigations work?*

| ID | Title | Status |
|---|---|---|
| ISS-0001 | What Is an Investigation? | Planned |
| ISS-0002 | Fragmentation Theory | Planned |
| ISS-0003 | Epistemic Integrity | Planned |
| ISS-0004 | The Anatomy of Evidence | Planned |

## Ontology-Driven Engineering (ODE)

*Asks: how should complex systems be engineered?*

ODE is independent of ISS: it could be applied to medicine, aviation, intelligence, finance, or scientific research. ARGUS is simply its first implementation.

| ID | Title | Status |
|---|---|---|
| [ODE-0001](ODE-0001-ontology-driven-engineering.md) | Ontology-Driven Engineering: Axioms and Method | Draft 0.1.0 |

**Registry note (append-only honesty):** ADR-0010 registered the ODE paper as "ISS-0005" before the two programs were recognized as independent (AGC Session 002). No ISS-0005 was ever drafted; the paper is allocated as ODE-0001 and the ISS-0005 number is retired unused to avoid ambiguity. The reference inside the immutable ADR-0010 resolves here.

## Conventions

Papers are numbered sequentially within their program as `ISS-NNNN-short-title.md` / `ODE-NNNN-short-title.md`. Research papers are governed documents: semantic versions per the [Governance Versioning Standard](../standards/GOVERNANCE_VERSIONING_STANDARD.md), [Lexicon](../../glossary/LEXICON.md) vocabulary, ontology references by stable identifier (ADR-0011).
