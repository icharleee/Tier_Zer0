"""Semantic contamination test (ADR-0022, Resolution 013 / ONT-PRN-018).

No epistemic layer may carry the vocabulary of the layers above it — the
ladder's separations (ONT-PRN-004) made mechanically enforceable. The
registry below is transcribed from the Derivation Specification D-PRN-018
(triangulation leg 3, ONT-PRN-015): expectations come from the normative
artifact, never from implementation constants.

Vocabulary is the tripwire, not the whole defense: reviews still judge
semantics. Release-blocking (Constitution, Enforcement §3).
"""

from __future__ import annotations

from argus.domain.models import Base

# Transcribed from DERIVATION_SPECIFICATION.md §D-PRN-018.
OBSERVATION_STEMS = (
    "confiden", "infer", "probab", "interpret", "hypoth", "rank",
    "suspic", "intent", "meaning", "likelihood", "predict", "score",
)
INTERPRETATION_STEMS = ("hypoth", "likelihood", "predict", "verdict", "guilt")
CONTAMINATION_REGISTRY: dict[str, tuple[str, ...]] = {
    "observations": OBSERVATION_STEMS,
    "observation_groundings": OBSERVATION_STEMS,
    "source_locators": OBSERVATION_STEMS + ("statement", "claim"),
    # Interpretation additionally forbids preference vocabulary (H4/Article IV).
    "interpretations": INTERPRETATION_STEMS + ("rank", "preferred", "primary", "weight", "confiden", "probab", "score"),
    "interpretation_groundings": INTERPRETATION_STEMS + ("rank", "preferred", "primary", "weight"),
}


def test_epistemic_layers_reject_semantic_contamination():
    """ONT-PRN-018 → Articles I, IV, IX: every epistemic table's columns are
    scanned against the normative registry; a violating column name fails
    the build and names itself."""
    violations = []
    for table_name, stems in CONTAMINATION_REGISTRY.items():
        table = Base.metadata.tables.get(table_name)
        assert table is not None, f"registry names unknown table {table_name}"
        for column in table.columns:
            for stem in stems:
                if stem in column.name.lower():
                    violations.append(f"{table_name}.{column.name} (stem: {stem})")
    assert not violations, "semantic contamination detected:\n" + "\n".join(violations)


def test_registry_covers_every_epistemic_table():
    """The registry must grow with the ladder: any table for a ladder object
    (observations, interpretations, hypotheses, and their junctions) must
    have a registry entry before it ships."""
    ladder_markers = ("observation", "interpret", "hypoth")
    for table_name in Base.metadata.tables:
        if any(m in table_name for m in ladder_markers):
            assert table_name in CONTAMINATION_REGISTRY, (
                f"{table_name} is an epistemic table without a contamination "
                "registry entry (ADR-0022: the registry grows one layer ahead)"
            )
