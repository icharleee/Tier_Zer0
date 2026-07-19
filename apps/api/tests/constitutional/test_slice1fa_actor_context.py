"""Slice 1F-A — Authenticated actor context (ODE Hypothesis H10).

H10 (refined, AGC Session 018): independent constitutional command paths
can derive actor attribution from authenticated principal context while
refusing caller-controlled identity substitution and preserving the
separation between authentication, actor attribution, authority, and
epistemic meaning.

Expectations transcribed from ACTOR_CONTEXT.md 0.1.0 (triangulation leg 3).
Honest bound: authentication is a declared single implementation; the
triangulated pair is the binding rule and the database consistency guard.
"""

from __future__ import annotations

import dataclasses

import pytest
from sqlalchemy import select, text

from argus.domain import actor_binding as ab
from argus.domain.actor_binding import AuthenticatedPrincipal, PrincipalClass, bind_actor
from argus.domain.actors import ActorClass
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import AuditEntry, Case

HUMAN_A = AuthenticatedPrincipal("det.reyes", PrincipalClass.HUMAN, "dev-token")
HUMAN_B = AuthenticatedPrincipal("det.morgan", PrincipalClass.HUMAN, "dev-token")
SERVICE = AuthenticatedPrincipal(
    "ingest-verifier-01", PrincipalClass.SERVICE, "dev-token",
    human_attribution="det.reyes",
)


def _code(exc) -> str:
    return str(exc).rsplit(":", 1)[-1] if "ONT-PRN-007" in str(exc) else str(exc)


class TestBindingRule:
    def test_binding_matrix(self):
        """ONT-PRN-028: the actor is derived from the principal; a
        transcription of ACTOR_CONTEXT.md §3."""
        # HUMAN principal -> HUMAN actor with actor_id = principal_id.
        a = bind_actor(HUMAN_A)
        assert a.actor_class is ActorClass.HUMAN and a.actor_id == "det.reyes"
        # SERVICE principal -> SYSTEM actor; human_authority from attribution.
        s = bind_actor(SERVICE, requires_class=ActorClass.SYSTEM)
        assert s.actor_class is ActorClass.SYSTEM and s.actor_id == "ingest-verifier-01"
        assert s.human_authority == "det.reyes"  # from provisioning, not payload

    def test_unauthenticated(self):
        with pytest.raises(ConstitutionalViolation) as e:
            bind_actor(None)
        assert "unauthenticated" in str(e.value)

    def test_principal_class_mismatch(self):
        # SERVICE principal cannot perform a HUMAN-only action.
        with pytest.raises(ConstitutionalViolation) as e:
            bind_actor(SERVICE, requires_class=ActorClass.HUMAN)
        assert "principal-class-mismatch" in str(e.value)
        # HUMAN principal cannot be bound as SYSTEM.
        with pytest.raises(ConstitutionalViolation) as e:
            bind_actor(HUMAN_A, requires_class=ActorClass.SYSTEM)
        assert "principal-class-mismatch" in str(e.value)
        # No AI principal path exists.
        with pytest.raises(ConstitutionalViolation) as e:
            bind_actor(HUMAN_A, requires_class=ActorClass.AI)
        assert "principal-class-mismatch" in str(e.value)

    def test_identity_input_prohibited(self):
        """Amendment 3: any caller identity field is refused — including
        when it MATCHES the principal (matching assertion is still
        assertion)."""
        for field in ("actor_id", "created_by", "human_authority", "principal_id"):
            with pytest.raises(ConstitutionalViolation) as e:
                ab.reject_identity_input({"title": "x", field: "det.reyes"})
            assert "identity-input-prohibited" in str(e.value)
        # Matching the authenticated identity does not help.
        with pytest.raises(ConstitutionalViolation) as e:
            ab.reject_identity_input({"actor_id": HUMAN_A.principal_id})
        assert "identity-input-prohibited" in str(e.value)
        # A clean command passes.
        ab.reject_identity_input({"title": "x", "legal_authority_basis": "warrant"})

    def test_authentication_confers_no_authority(self):
        """The corollary, structural (ADR-0033): the principal carries no
        permission set / access / visibility, and binding performs no
        resource authorization."""
        field_names = {f.name for f in dataclasses.fields(AuthenticatedPrincipal)}
        assert field_names == {
            "principal_id", "principal_class", "authentication_method",
            "human_attribution",
        }
        # No authority-shaped attributes leaked backward from 1F-B.
        for forbidden in ("permissions", "roles", "case_access", "visibility",
                          "sealed", "grants", "scopes"):
            assert forbidden not in field_names
        # bind_actor's only inputs are the principal and the required class —
        # it takes no resource to authorize against.
        import inspect
        params = set(inspect.signature(bind_actor).parameters) - {"principal"}
        assert params == {"requires_class"}


@pytest.mark.postgres
class TestExperimentH10:
    @pytest.fixture()
    def client(self, pg_engine):
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session, sessionmaker

        from argus.api.app import create_app

        factory = sessionmaker(bind=pg_engine, class_=Session)
        app = create_app(session_factory=factory)
        return TestClient(app, raise_server_exceptions=True)

    def _cmd(self, **extra):
        body = {"title": "Authenticated case", "legal_authority_basis": "Warrant 1F-A"}
        body.update(extra)
        return body

    def test_api_records_authenticated_principal(self, client, pg_session):
        """H10 core: the action binds to the authenticated principal; the
        recorded actor and audit attribution equal principal_id."""
        r = client.post("/cases", json=self._cmd(),
                        headers={"Authorization": "Bearer human-reyes"})
        assert r.status_code == 201, r.text
        case_id = r.json()["id"]
        assert r.json()["responsible_actor"] == "det.reyes"
        case = pg_session.get(Case, case_id)
        assert case is not None and case.responsible_actor == "det.reyes"
        entry = pg_session.execute(select(AuditEntry).where(
            AuditEntry.case_id == case_id,
            AuditEntry.action == "case-created")).scalars().one()
        assert entry.actor_class == "HUMAN" and entry.actor_id == "det.reyes"

    def test_unauthenticated_refused_no_write(self, client, pg_session):
        """No principal -> refused; nothing written, nothing audited."""
        before_cases = pg_session.execute(select(Case)).scalars().all()
        before = len(before_cases)
        r = client.post("/cases", json=self._cmd())  # no Authorization header
        assert r.status_code == 401
        assert "unauthenticated" in r.json()["detail"]
        pg_session.rollback()
        after = len(pg_session.execute(select(Case)).scalars().all())
        assert after == before

    def test_identity_input_prohibited_over_http(self, client):
        """Amendment 3 at the transport boundary: a caller identity field is
        refused even when it names the authenticated principal."""
        r = client.post("/cases", json=self._cmd(actor_id="det.reyes"),
                        headers={"Authorization": "Bearer human-reyes"})
        assert r.status_code == 403
        assert "identity-input-prohibited" in r.json()["detail"]
        # A different claimed identity is refused the same way.
        r2 = client.post("/cases", json=self._cmd(created_by="det.morgan"),
                         headers={"Authorization": "Bearer human-reyes"})
        assert r2.status_code == 403
        assert "identity-input-prohibited" in r2.json()["detail"]

    def test_no_impersonation_authenticated_identity_wins(self, client, pg_session):
        """Authenticated as morgan, the recorded actor is morgan — never a
        payload claim. (The command carries no identity field; this proves
        the derived identity is the authenticated one.)"""
        r = client.post("/cases", json=self._cmd(),
                        headers={"Authorization": "Bearer human-morgan"})
        assert r.status_code == 201
        assert r.json()["responsible_actor"] == "det.morgan"

    def test_db_guard_actor_principal_mismatch(self, pg_session):
        """The persistence guard: a bound principal inconsistent with the
        actor is refused at the database (defense-in-depth for the
        storage_ref class of service-layer inconsistency)."""
        pg_session.execute(text(
            "SELECT set_config('argus.actor_principal', 'det.reyes', true), "
            "set_config('argus.actor_principal_class', 'HUMAN', true)"))
        # Consistent: passes.
        pg_session.execute(text(
            "SELECT argus_private.assert_transaction_principal('HUMAN', 'det.reyes', '')"))
        # Inconsistent actor_id: refused.
        with pytest.raises(Exception) as e:
            pg_session.execute(text(
                "SELECT argus_private.assert_transaction_principal('HUMAN', 'det.morgan', '')"))
        assert "actor-principal-mismatch" in str(e.value)
        pg_session.rollback()

    def test_principal_does_not_leak_across_transactions(self, pg_session):
        """Amendment 4: SET LOCAL is transaction-scoped. A principal bound in
        one transaction is gone in the next — no leakage across a pooled
        connection."""
        pg_session.execute(text(
            "SELECT set_config('argus.actor_principal', 'det.reyes', true), "
            "set_config('argus.actor_principal_class', 'HUMAN', true)"))
        assert pg_session.execute(text(
            "SELECT current_setting('argus.actor_principal', true)")).scalar() == "det.reyes"
        pg_session.commit()  # ends the transaction; SET LOCAL expires
        leaked = pg_session.execute(text(
            "SELECT current_setting('argus.actor_principal', true)")).scalar()
        assert leaked in (None, "")  # no principal bound in the new transaction
        # And assert_transaction_principal fails closed with none bound.
        with pytest.raises(Exception) as e:
            pg_session.execute(text(
                "SELECT argus_private.assert_transaction_principal('HUMAN', 'det.reyes', '')"))
        assert "unauthenticated" in str(e.value)
        pg_session.rollback()

    def test_audit_trigger_rejects_mismatched_actor(self, pg_session, investigator):
        """Defense-in-depth: with a principal bound, an audit insert whose
        actor disagrees is rejected at the persistence boundary — proving
        the guard is not only in application code."""
        from argus.ingestion.service import create_case

        # A case created in a trusted-internal transaction (no principal).
        case = create_case(pg_session, title="guard target",
                           legal_authority_basis="w", responsible=investigator)
        # Now bind a principal and attempt an inconsistent audit append.
        pg_session.execute(text(
            "SELECT set_config('argus.actor_principal', 'det.reyes', true), "
            "set_config('argus.actor_principal_class', 'HUMAN', true)"))
        with pytest.raises(Exception) as e:
            pg_session.execute(text(
                "SELECT argus_private.append_audit_event("
                "replace(gen_random_uuid()::text,'-',''), :c, 'HUMAN', 'det.morgan', "
                "NULL, 'case-designation-changed', 'Case', :c, 'SUCCEEDED', NULL)"),
                {"c": case.id})
        assert "actor-principal-mismatch" in str(e.value)
        pg_session.rollback()

    def test_same_object_different_authors_epistemically_identical(
        self, pg_session, store
    ):
        """Article IX / ONT-PRN-028 corollary: two authenticated authors
        create semantically identical admissible records; differences are
        confined to attribution/audit fields — epistemic content is
        identical. Who authored != what the claim means."""
        from argus.ingestion.interpretations import create_interpretation
        from argus.ingestion.observations import create_observation, create_source_locator
        from argus.ingestion.service import (
            create_artifact_record, create_case, stage_upload, verify_and_activate,
        )
        from argus.domain.actors import human, system

        reyes, morgan = human("det.reyes"), human("det.morgan")
        verifier = system("v01", human_authority="det.reyes")

        def build(author):
            case = create_case(pg_session, title="epistemic-equality",
                               legal_authority_basis="w", responsible=author)
            staged = stage_upload(store, b"ARGUS-1FA-" + author.actor_id.encode() + b"\x00" * 40)
            art = create_artifact_record(pg_session, staged, case=case, actor=author,
                                         media_type="image/png",
                                         acquisition_description="synthetic")
            verify_and_activate(pg_session, store, art, verifier)
            loc = create_source_locator(pg_session, artifact=art, scheme="byte-range",
                                        payload={"start": 0, "end": 8}, actor=author)
            obs = create_observation(pg_session, case=case, locator_ids=[loc.id],
                                     statement="Blue sedan visible.",
                                     method_description="Direct visual review.",
                                     actor=author)
            interp = create_interpretation(
                pg_session, case=case, groundings=[(obs.id, "SUPPORTING")],
                meaning_statement="The vehicle is stationary.",
                reasoning_description="Frame comparison.",
                uncertainty_status="ACKNOWLEDGED",
                uncertainty_explanation="No material uncertainty identified; provisional.",
                actor=author)
            return obs, interp

        o1, i1 = build(reyes)
        o2, i2 = build(morgan)
        # Epistemic fields identical; only authorship differs.
        assert o1.statement == o2.statement
        assert (i1.meaning_statement, i1.reasoning_description,
                i1.uncertainty_status, i1.uncertainty_explanation) == (
                i2.meaning_statement, i2.reasoning_description,
                i2.uncertainty_status, i2.uncertainty_explanation)
        assert o1.created_by_id != o2.created_by_id  # attribution differs
        assert i1.created_by_id == "det.reyes" and i2.created_by_id == "det.morgan"

    def test_refusal_codes_are_canonical(self):
        """All five 1F-A codes are ONT-PRN-007-family stable identifiers."""
        codes = {ab.UNAUTHENTICATED, ab.IDENTITY_INPUT_PROHIBITED,
                 ab.IDENTITY_SUBSTITUTION, ab.PRINCIPAL_CLASS_MISMATCH,
                 ab.ACTOR_PRINCIPAL_MISMATCH}
        assert all(c.startswith("ONT-PRN-007:") for c in codes)
        assert len(codes) == 5
