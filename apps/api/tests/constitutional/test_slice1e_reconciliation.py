"""Slice 1E — Storage reconciliation (ODE Hypothesis H9).

H9 (refined, AGC Session 016): independent implementations can classify
integrity divergence among persisted representations of constitutional
records from the same observed storage facts while preserving provenance,
lifecycle state, and epistemic neutrality — without silently repairing
data or converting storage agreement into evidentiary truth.

Expectations transcribed from STORAGE_RECONCILIATION.md 0.1.0
(triangulation leg 3). The dual-rendering claim is honestly bounded: it
applies to the CLASSIFICATION of shared observed facts; probing is a
declared single implementation.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from argus import reconciliation_scan as rs
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import AuditEntry, EvidenceArtifact
from argus.domain.transitions import seal_artifact
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)

# Transcribed from STORAGE_RECONCILIATION.md §4–5: the canonical
# classification matrix with its normative precedence. Facts are
# (verification_performed, present, readable, digest_match, size_match,
# location_match) → (condition, divergence_reasons).
F = ("verification_performed", "present", "readable",
     "digest_match", "size_match", "location_match")
CLASSIFICATION_MATRIX = {
    "matched-all-invariants": ((True, True, True, True, True, True), ("MATCHED", ())),
    "sealed-or-unsupported-or-quarantined": ((False, True, True, True, True, True), ("UNVERIFIED", ())),
    "unverified-precedes-missing": ((False, False, False, False, False, False), ("UNVERIFIED", ())),
    "missing": ((True, False, False, False, False, False), ("MISSING", ())),
    "missing-precedes-unreadable": ((True, False, False, False, False, True), ("MISSING", ())),
    "unreadable": ((True, True, False, False, False, True), ("UNREADABLE", ())),
    "digest-divergent": ((True, True, True, False, True, True),
                         ("DIVERGENT", ("DIGEST_MISMATCH",))),
    "size-divergent (case F)": ((True, True, True, True, False, True),
                                ("DIVERGENT", ("SIZE_MISMATCH",))),
    "location-divergent (case G)": ((True, True, True, True, True, False),
                                    ("DIVERGENT", ("STORAGE_LOCATION_MISMATCH",))),
    "matching-hash-hides-nothing": ((True, True, True, True, False, False),
                                    ("DIVERGENT", ("SIZE_MISMATCH", "STORAGE_LOCATION_MISMATCH"))),
    "all-divergent": ((True, True, True, False, False, False),
                      ("DIVERGENT", ("DIGEST_MISMATCH", "SIZE_MISMATCH",
                                     "STORAGE_LOCATION_MISMATCH"))),
}

TRUTH_STEMS = ("authentic", "truth", "correct", "winner", "authoritat",
               "prevail", "repair", "restor", "verdict", "conclu")


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}", v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item, path + "[]")


class TestClassifierPython:
    def test_classification_matrix(self):
        """ONT-PRN-026 → Articles I, IX: the canonical precedence, rendered
        in Python, against the transcription."""
        for name, (facts, (condition, reasons)) in CLASSIFICATION_MATRIX.items():
            kwargs = dict(zip(F, facts))
            assert rs.classify_storage_integrity(**kwargs) == condition, name
            if condition == "DIVERGENT":
                assert rs.storage_divergence_reasons(
                    digest_match=kwargs["digest_match"],
                    size_match=kwargs["size_match"],
                    location_match=kwargs["location_match"],
                ) == reasons, name

    def test_matched_requires_all_invariants(self):
        """Amendment 2: flipping ANY single invariant off MATCHED."""
        base = dict(zip(F, (True,) * 6))
        assert rs.classify_storage_integrity(**base) == "MATCHED"
        for flag in F:
            flipped = {**base, flag: False}
            assert rs.classify_storage_integrity(**flipped) != "MATCHED", flag

    def test_no_truth_conditions_exist(self):
        """ADR-0031: the condition set is closed; no truth vocabulary."""
        conditions = {rs.MATCHED, rs.MISSING, rs.DIVERGENT, rs.UNREADABLE, rs.UNVERIFIED}
        assert len(conditions) == 5
        for value in conditions:
            assert not any(s in value.lower() for s in TRUTH_STEMS)
        for forbidden in ("CORRECT", "AUTHORITATIVE", "TRUE_VERSION", "WINNER"):
            assert forbidden not in conditions

    def test_unknown_case_refused_empty_valid(self, session, case, store):
        with pytest.raises(ConstitutionalViolation) as err:
            rs.reconcile_case_storage(session, store, "nonesuch")
        assert "unknown-case" in str(err.value)
        report = rs.reconcile_case_storage(session, store, case.id)
        assert report["results"] == [] and report["stalled_verification"] == []
        assert sum(report["operational_summary"].values()) == 0


@pytest.mark.postgres
class TestExperimentH9:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 1E reconciliation",
            legal_authority_basis="Test warrant 2026-SYN-1E", responsible=investigator,
        )

    def _artifact(self, pg_session, store, pg_case, investigator, verifier,
                  content, *, activate=True):
        staged = stage_upload(store, content)
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="application/octet-stream",
            acquisition_description="Synthetic 1E storage fixture.",
        )
        if activate:
            verify_and_activate(pg_session, store, artifact, verifier)
        return artifact

    @pytest.fixture()
    def nine_artifacts(self, pg_session, pg_admin_engine, store, pg_case,
                       investigator, verifier):
        """The Session 016 fixture: A matched, B missing, C digest-divergent
        (same length), D unreadable, E sealed, F' length-changing corruption
        (SIZE_MISMATCH live, alongside DIGEST_MISMATCH), G location-
        divergent, H untamperable (see test), I pending verification."""
        mk = lambda tag, **kw: self._artifact(
            pg_session, store, pg_case, investigator, verifier,
            b"ARGUS-1E-" + tag + b"-" + b"\x00" * 64, **kw)
        a = mk(b"A")
        b = mk(b"B")
        (store._permanent / b.hash_digest).unlink()  # external loss
        c = mk(b"C")
        original = (store._permanent / c.hash_digest).read_bytes()
        corrupted = b"X" + original[1:]  # same length: pure DIGEST_MISMATCH
        (store._permanent / c.hash_digest).write_bytes(corrupted)
        d = mk(b"D")
        target = store._permanent / d.hash_digest
        target.unlink()
        target.mkdir()  # present but unreadable, regardless of uid
        e = mk(b"E")
        seal_artifact(pg_session, e, investigator,
                      legal_basis="Protective order 2026-SYN-1E-PO")
        f = mk(b"F")
        (store._permanent / f.hash_digest).write_bytes(b"short")  # length changes too
        g = mk(b"G")
        with pg_admin_engine.begin() as conn:  # storage_ref is CT, unguarded
            conn.execute(text(
                "UPDATE evidence_artifacts SET storage_ref = 'legacy/misplaced' "
                "WHERE id = :id"), {"id": g.id})
        i = mk(b"I", activate=False)  # PENDING_VERIFICATION
        return {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f, "g": g, "i": i}

    def test_h9_acceptance_divergence_without_verdict(
        self, pg_session, store, pg_case, nine_artifacts
    ):
        """The Session 016 acceptance sequence: conditions classified,
        nothing labeled true or false, nothing mutated, nothing repaired.
        (ONT-PRN-026/027 → Articles I, II, V, VIII, IX.)"""
        art = nine_artifacts
        pg_session.expire_all()
        statuses_before = {
            a.id: (a.status.value, a.hash_digest, a.storage_ref, a.retracted_at)
            for a in pg_session.execute(select(EvidenceArtifact)).scalars()
        }
        audit_before = pg_session.execute(text(
            "SELECT count(*) FROM audit_entries WHERE case_id = :c"),
            {"c": pg_case.id}).scalar()

        report = rs.reconcile_case_storage(pg_session, store, pg_case.id)
        by_id = {r["artifact_id"]: r for r in report["results"]}

        assert by_id[art["a"].id]["condition"] == "MATCHED"
        assert by_id[art["b"].id]["condition"] == "MISSING"
        assert by_id[art["c"].id]["condition"] == "DIVERGENT"
        assert by_id[art["c"].id]["divergence_reasons"] == ["DIGEST_MISMATCH"]
        assert by_id[art["d"].id]["condition"] == "UNREADABLE"
        assert by_id[art["e"].id]["condition"] == "UNVERIFIED"
        assert by_id[art["f"].id]["condition"] == "DIVERGENT"
        assert by_id[art["f"].id]["divergence_reasons"] == ["DIGEST_MISMATCH", "SIZE_MISMATCH"]
        assert by_id[art["g"].id]["condition"] == "DIVERGENT"
        assert by_id[art["g"].id]["divergence_reasons"] == ["STORAGE_LOCATION_MISMATCH"]

        # I: verification process not yet completed ≠ unverified permanent
        # representation — separate section, never classified.
        assert art["i"].id not in by_id
        assert [s["artifact_id"] for s in report["stalled_verification"]] == [art["i"].id]

        # Summary reconciles: sum of counts == classified artifacts.
        summary = report["operational_summary"]
        assert sum(summary.values()) == len(report["results"]) == 7
        assert summary == {"matched_count": 1, "missing_count": 1,
                           "divergent_count": 3, "unreadable_count": 1,
                           "unverified_count": 1}

        # No truth surface anywhere in the report.
        for path, value in _walk(report):
            key = path.rsplit(".", 1)[-1].lower()
            assert not any(s in key for s in TRUTH_STEMS), path
            if isinstance(value, str):
                assert value not in ("CORRECT", "AUTHORITATIVE", "TRUE_VERSION", "WINNER")

        # Non-effects: no retraction, no transition, no provenance change,
        # no audit emission — detect ≠ decide ≠ mutate.
        pg_session.expire_all()
        statuses_after = {
            a.id: (a.status.value, a.hash_digest, a.storage_ref, a.retracted_at)
            for a in pg_session.execute(select(EvidenceArtifact)).scalars()
        }
        assert statuses_before == statuses_after
        audit_after = pg_session.execute(text(
            "SELECT count(*) FROM audit_entries WHERE case_id = :c"),
            {"c": pg_case.id}).scalar()
        assert audit_before == audit_after

        # Purity: identical canonical bytes over unchanged DB + store.
        again = rs.reconcile_case_storage(pg_session, store, pg_case.id)
        assert rs.canonical_report_bytes(report) == rs.canonical_report_bytes(again)

    def test_sealed_metadata_only(self, pg_session, store, pg_case, nine_artifacts):
        """Gate decision: the default scan never opens SEALED content.
        observed.present = storage-level existence without content access."""
        e = nine_artifacts["e"]
        report = rs.reconcile_case_storage(pg_session, store, pg_case.id)
        entry = next(r for r in report["results"] if r["artifact_id"] == e.id)
        assert entry["visibility"] == {
            "state": "SEALED", "content_visible": False,
            "verification_performed": False,
            "withholding_basis": "AUTHORITY_REQUIRED",
        }
        assert entry["observed"]["present"] is True  # existence, not a read
        assert entry["observed"]["recomputed_digest"] is None
        assert "recorded" not in entry  # digest-bearing details withheld, declared

    def test_metadata_tamper_structurally_impossible(
        self, pg_session, pg_admin_engine, nine_artifacts
    ):
        """Cases F/H in their isolated DB-tamper form are unreachable: the
        immutability trigger blocks recorded size and algorithm changes at
        every layer, INCLUDING the tamper role. The classifier still covers
        those conditions (matrix rows) for facts a future backend could
        legitimately observe."""
        from sqlalchemy.exc import DBAPIError

        a = nine_artifacts["a"]
        for tamper in (
            "UPDATE evidence_artifacts SET size_bytes = size_bytes + 1 WHERE id = :id",
            "UPDATE evidence_artifacts SET hash_algorithm = 'sha3-512' WHERE id = :id",
        ):
            with pytest.raises(DBAPIError) as err, pg_admin_engine.begin() as conn:
                conn.execute(text(tamper), {"id": a.id})
            assert "content-immutable" in str(err.value)

    def test_h9_classifier_conformance(self, pg_session):
        """H9: the SQL and Python classifiers derive identical conditions
        and reasons from the same observed facts, across the transcribed
        matrix — both compared against the transcription."""
        divergences = []
        for name, (facts, (condition, reasons)) in CLASSIFICATION_MATRIX.items():
            kwargs = dict(zip(F, facts))
            py_cond = rs.classify_storage_integrity(**kwargs)
            pg_cond = pg_session.execute(text(
                "SELECT argus_private.classify_storage_integrity(:v, :p, :r, :d, :s, :l)"
            ), {"v": facts[0], "p": facts[1], "r": facts[2],
                "d": facts[3], "s": facts[4], "l": facts[5]}).scalar()
            if not (py_cond == pg_cond == condition):
                divergences.append(f"{name}: py={py_cond} pg={pg_cond} expected={condition}")
            if condition == "DIVERGENT":
                pg_reasons = tuple(pg_session.execute(text(
                    "SELECT argus_private.storage_divergence_reasons(:d, :s, :l)"
                ), {"d": facts[3], "s": facts[4], "l": facts[5]}).scalar())
                py_reasons = rs.storage_divergence_reasons(
                    digest_match=facts[3], size_match=facts[4], location_match=facts[5])
                if not (py_reasons == pg_reasons == reasons):
                    divergences.append(
                        f"{name}: py={py_reasons} pg={pg_reasons} expected={reasons}")
        assert not divergences, "H9 falsified for:\n" + "\n".join(divergences)
