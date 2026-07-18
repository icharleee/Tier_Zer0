"""Slice 3A — Case Reconstruction read model (ODE Hypothesis H8).

H8 (refined, AGC Session 014): independent implementations can compose the
complete authorized epistemic graph of a Case into semantically and
canonically equivalent read models while preserving provenance, plurality,
boundary structure, temporal truth, visibility constraints, and
non-preference — without constructing a privileged narrative or
introducing new epistemic meaning.

Expectations transcribed from CASE_RECONSTRUCTION.md 0.1.0 (triangulation
leg 3, ONT-PRN-015). H8 is tested through semantic structural equality and
strengthened by canonical byte identity.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy import select, text

from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import Base
from argus.domain.transitions import seal_artifact
from argus.ingestion.contradictions import (
    create_contradiction,
    dispose_contradiction,
    link_contradiction,
)
from argus.ingestion.hypotheses import create_hypothesis, retract_hypothesis
from argus.ingestion.interpretations import create_interpretation
from argus.ingestion.observations import create_observation, create_source_locator
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)
from argus.ingestion.unknowns import create_unknown, link_unknown, resolve_unknown
from argus.reconstruction import canonical_bytes, reconstruct_case

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128 + b"ARGUS-SYNTHETIC-3A"
SEALED_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 96 + b"ARGUS-SEALED-3A"

MEANING_A = "The visible vehicle is stationary throughout 19:42:00-19:42:10."
MEANING_B = "The visible vehicle changes position during 19:42:00-19:42:10."
SCOPE = "Same vehicle, same camera, same coordinate frame, same interval 19:42:00-19:42:10."
BASIS = ("A single vehicle cannot be both stationary throughout and changing "
         "position during the same interval in the same coordinate frame.")
UNC = "No material uncertainty has been identified from the cited observations, but the interpretation remains provisional."
STATEMENT_1 = "The sedan visible at 19:42 was already parked before the recording interval began."
STATEMENT_2 = "The sedan visible at 19:42 was completing a parking maneuver as the recording interval began."
STATEMENT_3 = "The sedan visible at 19:42 was briefly stopped mid-street before continuing."
H_REASONING = "Composed from the admitted motion-state interpretations over the cited frames."
TESTABILITY = "Additional footage covering 19:41:00-19:42:00 would bear on this explanation."
CHALLENGE = "Footage showing the parking spot empty at 19:41:30 would challenge this explanation."
ALT_ABSENCE = ("No alternative explanation is currently articulated: the alternative "
               "space considered (arrival or departure during the interval) is not "
               "yet supported by any grounded Interpretation.")
NO_UNK = ("No specific unresolved gap is presently articulated for this explanation; "
          "unknowns may exist that have not been recognized.")
NO_CON = ("No formal contradiction is currently linked; this does not assert the "
          "explanation is uncontradicted in reality.")
ALT_RELATION = "Both explanations account for the same admitted motion-state interpretations."

# Transcribed from CASE_RECONSTRUCTION.md §5 — the closed Reconstruction
# Manifest: every mapped constitutional table classified. When a future
# table appears without a classification here, the coverage test fails —
# the reconstruction can never remain silently "complete."
MANIFEST = {
    "cases": "NODE",
    "case_authorities": "NODE",
    "evidence_artifacts": "NODE",
    "source_locators": "NODE",
    "observations": "NODE",
    "observation_groundings": "RELATIONSHIP",
    "interpretations": "NODE",
    "interpretation_groundings": "RELATIONSHIP",
    "unknowns": "NODE",
    "unknown_links": "RELATIONSHIP",
    "unknown_resolutions": "DISPOSITION",
    "contradictions": "NODE",
    "contradiction_members": "RELATIONSHIP",
    "contradiction_dispositions": "DISPOSITION",
    "contradiction_links": "RELATIONSHIP",
    "hypotheses": "NODE",
    "hypothesis_groundings": "RELATIONSHIP",
    "hypothesis_alternatives": "RELATIONSHIP",
    "audit_entries": "SUMMARY_METADATA",
    "case_audit_heads": "SUMMARY_METADATA",
}

# Transcribed from CASE_RECONSTRUCTION.md §4 — the prohibited-key registry
# (structured surface; one conformance mechanism, not the rule itself).
PROHIBITED_KEY_STEMS = (
    "verdict", "conclu", "narrat", "preferred", "featured", "leading",
    "primary", "rank", "weight", "score", "confiden", "probab", "winner",
    "theory", "accept", "likelihood", "predict", "refut", "promot", "best",
)


def _walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}"
            yield from _walk_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_keys(item, path + "[]")


def _shape(obj):
    """Schema shape, values erased: uniform per-class structure is the
    constitutional rule (Session 014, Amendment 3)."""
    if isinstance(obj, dict):
        return {k: _shape(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_shape(i) for i in obj]
    return "·"


class TestPythonRendering:
    def test_unknown_case_refused(self, session):
        """ONT-CAS-001:unknown-case — the single refusal condition."""
        with pytest.raises(ConstitutionalViolation) as err:
            reconstruct_case(session, "nonesuch")
        assert "unknown-case" in str(err.value)

    def test_empty_case_valid(self, session, case):
        """Emptiness is not an error: an empty case reconstructs to a valid
        document with empty sections and a genesis-consistent chain."""
        doc = reconstruct_case(session, case.id)
        for section in ("evidence_artifacts", "source_locators", "observations",
                        "interpretations", "unknowns", "contradictions",
                        "hypotheses", "hypothesis_alternatives"):
            assert doc[section] == []
        assert doc["case"]["id"] == case.id
        assert doc["case"]["authorities"]  # authority basis recorded at creation
        assert doc["audit_chain"]["entry_count"] >= 1  # case-created
        assert doc["audit_chain"]["integrity_status"] == "CHAIN_VALID"

    def test_reconstruction_pure_and_deterministic(self, session, case):
        """Non-effects: a pure read — twice-identical bytes, no new audit
        entries, no evaluation-time values in the canonical payload."""
        from argus.domain.models import AuditEntry
        before = len(session.execute(select(AuditEntry)).scalars().all())
        b1 = canonical_bytes(reconstruct_case(session, case.id))
        b2 = canonical_bytes(reconstruct_case(session, case.id))
        assert b1 == b2
        after = len(session.execute(select(AuditEntry)).scalars().all())
        assert before == after

    def test_no_prohibited_keys(self, session, case):
        """The structured-surface tripwire over every canonical-payload key."""
        doc = reconstruct_case(session, case.id)
        violations = [
            p for p in _walk_keys(doc)
            if any(s in p.rsplit(".", 1)[-1].lower() for s in PROHIBITED_KEY_STEMS)
        ]
        assert not violations, violations

    def test_manifest_covers_registry(self):
        """Amendment 4: every mapped constitutional table must be classified
        in the manifest — a future object cannot leave the reconstruction
        silently complete."""
        unclassified = [t for t in Base.metadata.tables if t not in MANIFEST]
        assert not unclassified, (
            f"tables missing a Reconstruction Manifest classification: {unclassified}"
        )
        valid = {"NODE", "RELATIONSHIP", "DISPOSITION", "DERIVED_STATE",
                 "SUMMARY_METADATA", "EXCLUDED_BY_DESIGN"}
        assert set(MANIFEST.values()) <= valid


@pytest.mark.postgres
class TestExperimentH8:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 3A reconstruction",
            legal_authority_basis="Test warrant 2026-SYN-3A", responsible=investigator,
        )

    @pytest.fixture()
    def topology(self, pg_session, store, pg_case, investigator, verifier):
        """The full authorized epistemic graph: two artifacts (one SEALED),
        grounded observation, competing interpretations, a resolved Unknown,
        a disposed Contradiction challenging two alternative Hypotheses, and
        one retracted Hypothesis."""
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 3A video still.",
        )
        verify_and_activate(pg_session, store, artifact, verifier)
        staged2 = stage_upload(store, SEALED_IMAGE)
        sealed = create_artifact_record(
            pg_session, staged2, case=pg_case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic sealed exhibit.",
        )
        verify_and_activate(pg_session, store, sealed, verifier)
        seal_artifact(pg_session, sealed, investigator,
                      legal_basis="Protective order 2026-SYN-3A-PO")
        locator = create_source_locator(
            pg_session, artifact=artifact, scheme="byte-range",
            payload={"start": 8, "end": 100}, actor=investigator,
        )
        obs = create_observation(
            pg_session, case=pg_case, locator_ids=[locator.id],
            statement="Blue sedan visible.", method_description="Direct visual review.",
            actor=investigator,
        )
        a = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement=MEANING_A,
            reasoning_description="Position comparison across the cited frames.",
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator,
        )
        b = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement=MEANING_B,
            reasoning_description="Position comparison across the cited frames.",
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator,
        )
        unknown = create_unknown(
            pg_session, case=pg_case,
            question="Who was driving the sedan between 19:41 and 19:43?",
            actor=investigator,
        )
        contradiction = create_contradiction(
            pg_session, case=pg_case,
            members=[("Interpretation", a.id), ("Interpretation", b.id)],
            description="Interpretations assert mutually exclusive motion states under identical scope.",
            contradiction_type="DESCRIPTIVE", scope_definition=SCOPE,
            incompatibility_basis=BASIS, actor=investigator,
        )
        h1 = create_hypothesis(
            pg_session, case=pg_case,
            groundings=[(a.id, "DERIVED_FROM"), (b.id, "DERIVED_FROM")],
            explanatory_statement=STATEMENT_1, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator,
            alternative_absence_explanation=ALT_ABSENCE,
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON,
        )
        h2 = create_hypothesis(
            pg_session, case=pg_case,
            groundings=[(a.id, "DERIVED_FROM"), (b.id, "DERIVED_FROM")],
            explanatory_statement=STATEMENT_2, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator,
            alternatives=[(h1.id, ALT_RELATION)],
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON,
        )
        h3 = create_hypothesis(
            pg_session, case=pg_case,
            groundings=[(a.id, "DERIVED_FROM")],
            explanatory_statement=STATEMENT_3, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator,
            alternative_absence_explanation=ALT_ABSENCE,
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON,
        )
        for h in (h1, h2):
            link_unknown(pg_session, unknown=unknown, target_type="Hypothesis",
                         target_id=h.id,
                         nature="The driver's identity limits this explanation.",
                         actor=investigator)
            link_contradiction(pg_session, contradiction=contradiction,
                               hypothesis_id=h.id,
                               explanation="The scoped incompatibility bears on this explanation.",
                               actor=investigator)
        resolve_unknown(
            pg_session, unknown=unknown, resolution_type="UNRESOLVABLE",
            rationale="No admissible source identifies the driver; the gap is permanent for this corpus.",
            answering_claims=None, actor=investigator,
        )
        dispose_contradiction(
            pg_session, contradiction=contradiction, outcome="EXPLAINED",
            rationale="On review, the intervals differ by one frame; scopes were not identical.",
            informing_refs=None, actor=investigator,
        )
        retract_hypothesis(pg_session, h3, investigator,
                           reason="Author withdrew the mid-street account after frame re-review.")
        return {"case": pg_case, "sealed": sealed, "h1": h1, "h2": h2, "h3": h3}

    def _pg_doc(self, pg_session, case_id) -> dict:
        return json.loads(pg_session.execute(
            text("SELECT argus_private.case_reconstruction(:id)::text"),
            {"id": case_id},
        ).scalar())

    def test_h8_semantic_equality(self, pg_session, topology):
        """Level 1 — the H8 requirement: same nodes, relationships, stored
        and derived values, visibility states, historical/current
        distinctions, retraction states (jsonb equality is
        representation-independent)."""
        case = topology["case"]
        py_doc = reconstruct_case(pg_session, case.id)
        assert pg_session.execute(
            text("SELECT argus_private.case_reconstruction(:id) = CAST(:doc AS jsonb)"),
            {"id": case.id, "doc": json.dumps(py_doc)},
        ).scalar() is True

    def test_h8_canonical_byte_identity(self, pg_session, topology):
        """Level 2 — the strengthened conformance test: identical bytes under
        the chain_version=1 canonical serialization (both canonicalizers
        independently rendered and parity-proven)."""
        case = topology["case"]
        py_bytes = canonical_bytes(reconstruct_case(pg_session, case.id))
        pg_bytes = pg_session.execute(
            text("SELECT argus_private.canonical_jsonb(argus_private.case_reconstruction(:id))"),
            {"id": case.id},
        ).scalar()
        assert py_bytes == pg_bytes

    def test_manifest_completeness(self, pg_session, topology):
        """Amendment 4: for every in-scope class, DB count for the case ==
        reconstruction representation count at its manifest location."""
        case = topology["case"]
        doc = reconstruct_case(pg_session, case.id)

        def db_count(sql):
            return pg_session.execute(text(sql), {"c": case.id}).scalar()

        assert 1 == 1 and doc["case"]["id"] == case.id
        assert len(doc["case"]["authorities"]) == db_count(
            "SELECT count(*) FROM case_authorities WHERE case_id = :c")
        assert len(doc["evidence_artifacts"]) == db_count(
            "SELECT count(*) FROM evidence_artifacts WHERE case_id = :c")
        assert len(doc["source_locators"]) == db_count(
            "SELECT count(*) FROM source_locators WHERE case_id = :c")
        assert len(doc["observations"]) == db_count(
            "SELECT count(*) FROM observations WHERE case_id = :c")
        assert sum(len(o["groundings"]) for o in doc["observations"]) == db_count(
            "SELECT count(*) FROM observation_groundings g JOIN observations o ON o.id = g.observation_id WHERE o.case_id = :c")
        assert len(doc["interpretations"]) == db_count(
            "SELECT count(*) FROM interpretations WHERE case_id = :c")
        assert sum(len(i["groundings"]) for i in doc["interpretations"]) == db_count(
            "SELECT count(*) FROM interpretation_groundings g JOIN interpretations i ON i.id = g.interpretation_id WHERE i.case_id = :c")
        assert len(doc["unknowns"]) == db_count(
            "SELECT count(*) FROM unknowns WHERE case_id = :c")
        assert sum(len(u["links"]) for u in doc["unknowns"]) == db_count(
            "SELECT count(*) FROM unknown_links l JOIN unknowns u ON u.id = l.unknown_id WHERE u.case_id = :c")
        assert sum(1 for u in doc["unknowns"] if u["resolution"]) == db_count(
            "SELECT count(*) FROM unknown_resolutions r JOIN unknowns u ON u.id = r.unknown_id WHERE u.case_id = :c")
        assert len(doc["contradictions"]) == db_count(
            "SELECT count(*) FROM contradictions WHERE case_id = :c")
        assert sum(len(k["members"]) for k in doc["contradictions"]) == db_count(
            "SELECT count(*) FROM contradiction_members m JOIN contradictions k ON k.id = m.contradiction_id WHERE k.case_id = :c")
        assert sum(len(k["links"]) for k in doc["contradictions"]) == db_count(
            "SELECT count(*) FROM contradiction_links l JOIN contradictions k ON k.id = l.contradiction_id WHERE k.case_id = :c")
        assert sum(1 for k in doc["contradictions"] if k["disposition"]) == db_count(
            "SELECT count(*) FROM contradiction_dispositions d JOIN contradictions k ON k.id = d.contradiction_id WHERE k.case_id = :c")
        assert len(doc["hypotheses"]) == db_count(
            "SELECT count(*) FROM hypotheses WHERE case_id = :c")
        assert sum(len(h["groundings"]) for h in doc["hypotheses"]) == db_count(
            "SELECT count(*) FROM hypothesis_groundings g JOIN hypotheses h ON h.id = g.hypothesis_id WHERE h.case_id = :c")
        assert len(doc["hypothesis_alternatives"]) == db_count(
            "SELECT count(*) FROM hypothesis_alternatives a JOIN hypotheses h ON h.id = a.hypothesis_a_id WHERE h.case_id = :c")
        assert doc["audit_chain"]["entry_count"] == db_count(
            "SELECT count(*) FROM audit_entries WHERE case_id = :c")

    def test_structural_symmetry(self, pg_session, topology):
        """Amendment 3 + acceptance test 11: the live Hypotheses have
        identical schema shapes — no extra fields from health, alternative
        status, disposition, or sibling retraction."""
        case, h1, h2 = topology["case"], topology["h1"], topology["h2"]
        doc = reconstruct_case(pg_session, case.id)
        by_id = {h["id"]: h for h in doc["hypotheses"]}
        assert _shape(by_id[h1.id]) == _shape(by_id[h2.id])
        # Ordering is citation only; no privileged slot exists anywhere.
        assert [h["citation"] for h in doc["hypotheses"]] == sorted(
            h["citation"] for h in doc["hypotheses"])

    def test_sealed_visibility_envelope(self, pg_session, topology):
        """Amendment 5: SEALED is existence-plus-status with the withholding
        declared — never silent omission; both renderings agree exactly."""
        case, sealed = topology["case"], topology["sealed"]
        for doc in (reconstruct_case(pg_session, case.id),
                    self._pg_doc(pg_session, case.id)):
            entry = next(a for a in doc["evidence_artifacts"] if a["id"] == sealed.id)
            assert set(entry) == {"id", "ontology_class", "status", "created_at",
                                  "retraction", "visibility"}
            assert entry["status"] == "SEALED"
            assert entry["visibility"] == {
                "state": "SEALED", "content_visible": False,
                "provenance_detail_visible": False,
                "withholding_basis": "AUTHORITY_REQUIRED",
            }
            full = next(a for a in doc["evidence_artifacts"] if a["id"] != sealed.id)
            assert full["visibility"]["state"] == "FULL"
            assert "hash_digest" in full and "hash_digest" not in entry

    def test_retracted_records_visible(self, pg_session, topology):
        """Article VIII: retracted records are present and labeled — no
        selective omission by any epistemic state."""
        case, h3 = topology["case"], topology["h3"]
        doc = reconstruct_case(pg_session, case.id)
        entry = next(h for h in doc["hypotheses"] if h["id"] == h3.id)
        assert entry["retraction"] is not None
        assert entry["retraction"]["reason"]
        assert entry["explanatory_statement"] == STATEMENT_3  # content preserved

    def test_historical_and_current_side_by_side(self, pg_session, topology):
        """ONT-PRN-025: stored articulations beside derived states, neither
        merged nor concealed."""
        case, h1 = topology["case"], topology["h1"]
        doc = reconstruct_case(pg_session, case.id)
        entry = next(h for h in doc["hypotheses"] if h["id"] == h1.id)
        # Historical truth of the creation moment...
        assert entry["alternative_articulation_at_creation"] == "NONE_CURRENTLY_ARTICULATED_AT_CREATION"
        assert entry["alternative_absence_explanation"] == ALT_ABSENCE
        # ...beside the current derived condition.
        assert entry["derived"]["current_alternative_state"] == "ALTERNATIVES_CURRENT"
        assert entry["derived"]["unknown_boundary_state"] == "LIMITS_RESOLVED"
        assert entry["derived"]["contradiction_boundary_state"] == "CHALLENGES_DISPOSED"
        con = doc["contradictions"][0]
        assert con["disposition"] is not None and con["derived"]["status"] == "EXPLAINED"
        assert len(con["links"]) == 2  # disposed Contradiction remains linked

    def test_broken_chain_surfaced_not_hidden(
        self, pg_session, pg_admin_engine, topology
    ):
        """Amendment 6 + acceptance test 13: CHAIN_INVALID never prevents
        reconstruction — the projection surfaces the integrity problem and
        presents the records (surface, never silently repair)."""
        case = topology["case"]
        with pg_admin_engine.begin() as conn:
            conn.execute(text(
                "UPDATE audit_entries SET canonical_payload = 'tampered-payload' "
                "WHERE id = (SELECT id FROM audit_entries WHERE case_id = :c "
                "ORDER BY seq LIMIT 1)"), {"c": case.id})
        py_doc = reconstruct_case(pg_session, case.id)
        assert py_doc["audit_chain"]["integrity_status"] == "CHAIN_INVALID"
        assert pg_session.execute(
            text("SELECT argus_private.audit_chain_status(:c)"), {"c": case.id}
        ).scalar() == "CHAIN_INVALID"
        # The epistemic records remain present; no conclusion is generated.
        assert py_doc["hypotheses"] and py_doc["interpretations"]
        pg_doc = self._pg_doc(pg_session, case.id)
        assert pg_doc["audit_chain"]["integrity_status"] == "CHAIN_INVALID"

    def test_pg_purity_and_unknown_case(self, pg_session, topology):
        """Non-effects at the database rendering, and the refusal code."""
        from sqlalchemy.exc import DBAPIError

        case = topology["case"]
        before = pg_session.execute(text(
            "SELECT count(*) FROM audit_entries WHERE case_id = :c"), {"c": case.id}
        ).scalar()
        b1 = pg_session.execute(text(
            "SELECT argus_private.canonical_jsonb(argus_private.case_reconstruction(:id))"),
            {"id": case.id}).scalar()
        b2 = pg_session.execute(text(
            "SELECT argus_private.canonical_jsonb(argus_private.case_reconstruction(:id))"),
            {"id": case.id}).scalar()
        assert b1 == b2
        after = pg_session.execute(text(
            "SELECT count(*) FROM audit_entries WHERE case_id = :c"), {"c": case.id}
        ).scalar()
        assert before == after
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.case_reconstruction('nonesuch')"))
            pg_session.commit()
        pg_session.rollback()
        assert "unknown-case" in str(err.value)
