"""Slice 1F-B — Authority and visibility (ODE Hypothesis H11).

H11 (refined, AGC Session 020): independent authority-decision
implementations can derive resource-scoped action and visibility
permissions from authenticated principal context and normalized capability
grants while preserving epistemic neutrality, explicit authorized
withholding, least privilege, and attributable protected access.

Expectations transcribed from AUTHORITY.md 0.1.0 (triangulation leg 3).
Honest bound: the AuthorityProvider is a declared single-implementation
grant-fact source; the triangulated pair is the authorize decision (Python
+ PostgreSQL) and protected-content enforcement is application-layer.
"""

from __future__ import annotations

import base64
import inspect

import pytest
from sqlalchemy import select, text

from argus.domain import authority as auth
from argus.domain.authority import (
    AuthorityGrant, Capability, Decision, authorize, project_artifact_visibility,
)
from argus.domain.models import AuditEntry, EvidenceArtifact, Observation
from argus.domain.transitions import seal_artifact
from argus.ingestion.observations import create_observation, create_source_locator
from argus.ingestion.service import (
    create_artifact_record, create_case, stage_upload, verify_and_activate,
)

SYNTHETIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 96 + b"ARGUS-1FB"


def _g(pid, cap, case_id):
    return AuthorityGrant(pid, cap, "CASE", case_id)


# Transcribed from AUTHORITY.md §4: the authorize decision matrix.
# (grants for principal, required capability, resource case) -> outcome
AUTHORIZE_MATRIX = {
    "allow-exact": (((Capability.OBSERVATION_CREATE, "cA"),), Capability.OBSERVATION_CREATE, "cA", "ALLOW"),
    "scope-mismatch": (((Capability.OBSERVATION_CREATE, "cB"),), Capability.OBSERVATION_CREATE, "cA", "RESOURCE_SCOPE_MISMATCH"),
    "capability-not-granted": (((Capability.CASE_READ, "cA"),), Capability.OBSERVATION_CREATE, "cA", "CAPABILITY_NOT_GRANTED"),
    "no-grants": ((), Capability.CASE_READ, "cA", "CAPABILITY_NOT_GRANTED"),
    "no-inheritance-metadata-not-content": (((Capability.SEALED_METADATA_READ, "cA"),), Capability.SEALED_CONTENT_READ, "cA", "CAPABILITY_NOT_GRANTED"),
    "no-inheritance-content-not-verify": (((Capability.SEALED_CONTENT_READ, "cA"),), Capability.SEALED_VERIFY, "cA", "CAPABILITY_NOT_GRANTED"),
    "no-inheritance-caseread-not-action": (((Capability.CASE_READ, "cA"),), Capability.OBSERVATION_CREATE, "cA", "CAPABILITY_NOT_GRANTED"),
}


class TestAuthorizeDecision:
    def test_authorize_matrix(self):
        """ONT-PRN-029: capability + Case scope; no inheritance."""
        for name, (grant_specs, required, case, expected) in AUTHORIZE_MATRIX.items():
            grants = tuple(_g("p", cap, cid) for cap, cid in grant_specs)
            d = authorize(required, case, grants)
            got = "ALLOW" if d.allowed else d.reason
            assert got == expected, name

    def test_capability_non_inheritance(self):
        """Amendment 1: every capability stands alone."""
        grants = (_g("p", Capability.SEALED_METADATA_READ, "cA"),
                  _g("p", Capability.CASE_READ, "cA"))
        assert not authorize(Capability.SEALED_CONTENT_READ, "cA", grants).allowed
        assert not authorize(Capability.SEALED_VERIFY, "cA", grants).allowed
        assert not authorize(Capability.OBSERVATION_CREATE, "cA", grants).allowed
        assert authorize(Capability.CASE_READ, "cA", grants).allowed

    def test_case_scope_isolation(self):
        """Amendment 5: a Case-A grant never authorizes Case B; no '*'."""
        grants = (_g("p", Capability.OBSERVATION_CREATE, "cA"),)
        assert authorize(Capability.OBSERVATION_CREATE, "cA", grants).allowed
        d = authorize(Capability.OBSERVATION_CREATE, "cB", grants)
        assert not d.allowed and d.reason == auth.RESOURCE_SCOPE_MISMATCH
        # There is no wildcard scope value that grants everything.
        wild = (_g("p", Capability.OBSERVATION_CREATE, "*"),)
        assert not authorize(Capability.OBSERVATION_CREATE, "cA", wild).allowed

    def test_provider_facts_only(self):
        """Amendment 4: the provider surface exposes no decision method."""
        from argus.api.authority_provider import AuthorityProvider, DevAuthorityProvider
        methods = {n for n, _ in inspect.getmembers(DevAuthorityProvider, inspect.isfunction)}
        assert "grants_for" in methods
        for forbidden in ("authorize", "decide", "allow", "deny", "can", "permit"):
            assert forbidden not in methods
        # The protocol declares only grants_for.
        proto = {n for n in dir(AuthorityProvider) if not n.startswith("_")}
        assert proto == {"grants_for"}

    def test_two_stage_visibility_projection(self):
        """Amendment 2: the projected envelope derives from capabilities;
        the record is singular, only the projection changes (O14)."""
        # CASE_READ only: sealed metadata and content withheld, existence shown.
        base = (_g("p", Capability.CASE_READ, "cA"),)
        v = project_artifact_visibility(sealed=True, case_id="cA", grants=base)
        assert v == {"state": "SEALED", "existence_visible": True,
                     "metadata_visible": False, "content_visible": False,
                     "withholding_basis": "AUTHORITY_REQUIRED"}
        # + SEALED_METADATA_READ: metadata revealed, content still withheld.
        v2 = project_artifact_visibility(
            sealed=True, case_id="cA",
            grants=base + (_g("p", Capability.SEALED_METADATA_READ, "cA"),))
        assert v2["metadata_visible"] and not v2["content_visible"]
        assert v2["withholding_basis"] == "AUTHORITY_REQUIRED"
        # FULL artifact: everything visible under CASE_READ.
        vf = project_artifact_visibility(sealed=False, case_id="cA", grants=base)
        assert vf["state"] == "FULL" and vf["content_visible"] and vf["withholding_basis"] is None


@pytest.mark.postgres
class TestExperimentH11:
    @pytest.fixture()
    def verifier_registry(self):
        from argus.domain.actor_binding import AuthenticatedPrincipal, PrincipalClass
        from argus.api.authentication import DevTokenVerifier
        reg = {
            f"tok-{name}": AuthenticatedPrincipal(name, PrincipalClass.HUMAN, "dev-token")
            for name in ("alice", "bob", "carol", "dave")
        }
        return DevTokenVerifier(reg)

    @pytest.fixture()
    def world(self, pg_session, store, investigator, verifier):
        """Two cases; case A has a FULL artifact, a SEALED artifact, an
        observation, and a live locator for action-authority tests."""
        cases = {}
        for tag in ("A", "B"):
            case = create_case(pg_session, title=f"case-{tag}",
                               legal_authority_basis="w", responsible=investigator)
            cases[tag] = case
        a = cases["A"]
        # FULL artifact + locator + observation.
        staged = stage_upload(store, SYNTHETIC + b"-full")
        full = create_artifact_record(pg_session, staged, case=a, actor=investigator,
                                      media_type="image/png", acquisition_description="full")
        verify_and_activate(pg_session, store, full, verifier)
        loc = create_source_locator(pg_session, artifact=full, scheme="byte-range",
                                    payload={"start": 0, "end": 8}, actor=investigator)
        create_observation(pg_session, case=a, locator_ids=[loc.id],
                           statement="Blue sedan visible.",
                           method_description="Direct visual review.", actor=investigator)
        # SEALED artifact.
        staged2 = stage_upload(store, SYNTHETIC + b"-sealed")
        sealed = create_artifact_record(pg_session, staged2, case=a, actor=investigator,
                                        media_type="image/png", acquisition_description="sealed")
        verify_and_activate(pg_session, store, sealed, verifier)
        seal_artifact(pg_session, sealed, investigator, legal_basis="protective order")
        # seal_artifact does not commit on the PostgreSQL path; commit so the
        # fixture holds no FOR UPDATE lock on the audit head (the TestClient
        # uses a separate connection and would otherwise block forever).
        pg_session.commit()
        return {"caseA": a, "caseB": cases["B"], "full": full, "sealed": sealed, "locator": loc}

    def _client(self, pg_engine, verifier_registry, provider, store):
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session, sessionmaker
        from argus.api.app import create_app
        factory = sessionmaker(bind=pg_engine, class_=Session)
        app = create_app(session_factory=factory, verifier=verifier_registry,
                         authority_provider=provider, content_store=store)
        return TestClient(app, raise_server_exceptions=True)

    def _provider(self, grants: dict):
        from argus.api.authority_provider import DevAuthorityProvider
        return DevAuthorityProvider(grants)

    def _h(self, tok):
        return {"Authorization": f"Bearer {tok}"}

    def test_h11_visibility_varies_record_singular(
        self, pg_engine, pg_session, store, world, verifier_registry
    ):
        """Tests 1, 2, 3, 4 + O14 falsifier: two principals, different
        SEALED visibility, IDENTICAL epistemic state; the record is
        singular."""
        a = world["caseA"]
        provider = self._provider({
            "alice": (_g("alice", Capability.CASE_READ, a.id),),  # metadata withheld
            "bob": (_g("bob", Capability.CASE_READ, a.id),
                    _g("bob", Capability.SEALED_METADATA_READ, a.id)),  # metadata visible
        })
        client = self._client(pg_engine, verifier_registry, provider, store)
        ra = client.get(f"/cases/{a.id}", headers=self._h("tok-alice")).json()
        rb = client.get(f"/cases/{a.id}", headers=self._h("tok-bob")).json()

        sealed_id = world["sealed"].id
        va = next(x for x in ra["evidence_artifacts"] if x["id"] == sealed_id)
        vb = next(x for x in rb["evidence_artifacts"] if x["id"] == sealed_id)
        # (3) unauthorized: explicit SEALED withholding, existence visible.
        assert va["visibility"]["existence_visible"] and not va["visibility"]["metadata_visible"]
        assert "metadata" not in va
        # (4) authorized: metadata visible.
        assert vb["visibility"]["metadata_visible"] and "metadata" in vb
        # (1)(2) O14: projections differ, but epistemic state is identical.
        assert va["visibility"] != vb["visibility"]
        for section in ("observations", "interpretations", "unknowns",
                        "contradictions", "hypotheses"):
            assert ra[section] == rb[section]

    def test_h11_no_existence_leak_without_case_read(
        self, pg_engine, pg_session, store, world, verifier_registry
    ):
        """Test 13: no CASE_READ -> generic denial identical to a
        nonexistent resource; secrecy is not an existence leak."""
        a = world["caseA"]
        provider = self._provider({"carol": ()})  # carol has no grants
        client = self._client(pg_engine, verifier_registry, provider, store)
        r_real = client.get(f"/cases/{a.id}", headers=self._h("tok-carol"))
        r_fake = client.get("/cases/does-not-exist", headers=self._h("tok-carol"))
        assert r_real.status_code == 404 and r_fake.status_code == 404
        assert r_real.json() == r_fake.json() == {"detail": "resource not available"}
        # And a SEALED content request leaks nothing either.
        r_c = client.get(f"/artifacts/{world['sealed'].id}/content",
                         headers=self._h("tok-carol"))
        assert r_c.status_code == 404 and r_c.json() == {"detail": "resource not available"}

    def test_h11_case_read_but_no_content_authority(
        self, pg_engine, store, world, verifier_registry
    ):
        """Test 13 second half: CASE_READ but no SEALED_CONTENT_READ ->
        explicit visibility denial (existence known), not generic 404."""
        a = world["caseA"]
        provider = self._provider({"alice": (_g("alice", Capability.CASE_READ, a.id),)})
        client = self._client(pg_engine, verifier_registry, provider, store)
        r = client.get(f"/artifacts/{world['sealed'].id}/content", headers=self._h("tok-alice"))
        assert r.status_code == 403
        assert "visibility-not-authorized" in r.json()["detail"]

    def test_h11_protected_access_audited_evidence_unchanged(
        self, pg_engine, pg_session, store, world, verifier_registry
    ):
        """Tests 4, 5, 6: authorized SEALED content is returned AND an
        access event is appended; the evidence object is byte-identical."""
        a, sealed = world["caseA"], world["sealed"]
        provider = self._provider({"bob": (
            _g("bob", Capability.CASE_READ, a.id),
            _g("bob", Capability.SEALED_CONTENT_READ, a.id))})
        client = self._client(pg_engine, verifier_registry, provider, store)

        before = pg_session.get(EvidenceArtifact, sealed.id)
        snap = (before.hash_digest, before.size_bytes, before.status.value, before.storage_ref)
        n_before = pg_session.execute(select(AuditEntry).where(
            AuditEntry.case_id == a.id,
            AuditEntry.action == "sealed-content-accessed")).scalars().all()

        r = client.get(f"/artifacts/{sealed.id}/content", headers=self._h("tok-bob"))
        assert r.status_code == 200
        assert base64.b64decode(r.json()["content_base64"]) == SYNTHETIC + b"-sealed"

        pg_session.expire_all()
        after = pg_session.get(EvidenceArtifact, sealed.id)
        assert (after.hash_digest, after.size_bytes, after.status.value, after.storage_ref) == snap
        n_after = pg_session.execute(select(AuditEntry).where(
            AuditEntry.case_id == a.id,
            AuditEntry.action == "sealed-content-accessed")).scalars().all()
        assert len(n_after) == len(n_before) + 1
        assert n_after[-1].actor_id == "bob"  # attributed to the accessing principal

    def test_h11_content_withheld_if_audit_fails(
        self, pg_engine, pg_session, store, world, verifier_registry, monkeypatch
    ):
        """Test 14: if the access audit fails, protected content is NOT
        disclosed and the evidence is unchanged."""
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session, sessionmaker
        from argus.api.app import create_app

        a, sealed = world["caseA"], world["sealed"]
        provider = self._provider({"bob": (
            _g("bob", Capability.CASE_READ, a.id),
            _g("bob", Capability.SEALED_CONTENT_READ, a.id))})
        # A non-raising client so we observe the 500 a real caller receives —
        # the point is that the caller gets NO content, not an exception.
        factory = sessionmaker(bind=pg_engine, class_=Session)
        app = create_app(session_factory=factory, verifier=verifier_registry,
                         authority_provider=provider, content_store=store)
        client = TestClient(app, raise_server_exceptions=False)

        import argus.domain.audit as audit_mod

        real_emit = audit_mod.emit

        def boom(session, **kw):
            if kw.get("action") == "sealed-content-accessed":
                raise RuntimeError("simulated audit persistence failure")
            return real_emit(session, **kw)

        monkeypatch.setattr(audit_mod, "emit", boom)
        r = client.get(f"/artifacts/{sealed.id}/content", headers=self._h("tok-bob"))
        # Audit failed -> content is NOT disclosed (the coupling holds).
        assert r.status_code >= 500
        assert "content_base64" not in r.text
        # Evidence untouched, and no spurious access event recorded.
        pg_session.expire_all()
        art = pg_session.get(EvidenceArtifact, sealed.id)
        assert art.status.value == "SEALED"
        accessed = pg_session.execute(select(AuditEntry).where(
            AuditEntry.case_id == a.id,
            AuditEntry.action == "sealed-content-accessed")).scalars().all()
        assert accessed == []

    def test_h11_sealed_verify_returns_integrity_not_content(
        self, pg_engine, store, world, verifier_registry
    ):
        """Tests 15: SEALED_VERIFY yields the integrity result only, never
        bytes; and integrity != authenticity."""
        a, sealed = world["caseA"], world["sealed"]
        provider = self._provider({"dave": (
            _g("dave", Capability.CASE_READ, a.id),
            _g("dave", Capability.SEALED_VERIFY, a.id))})
        client = self._client(pg_engine, verifier_registry, provider, store)
        r = client.post(f"/artifacts/{sealed.id}/verify", headers=self._h("tok-dave"))
        assert r.status_code == 200
        body = r.json()
        assert body["integrity_status"] == "MATCHED"  # storage consistency only
        assert "content_base64" not in body and "content" not in body
        # SEALED_VERIFY does NOT grant content access.
        rc = client.get(f"/artifacts/{sealed.id}/content", headers=self._h("tok-dave"))
        assert rc.status_code == 403 and "visibility-not-authorized" in rc.json()["detail"]

    def test_h11_action_authority_and_scope(
        self, pg_engine, pg_session, store, world, verifier_registry
    ):
        """Tests 7, 8, 9: read authority without OBSERVATION_CREATE cannot
        write; a Case-B grant cannot write in Case A; denied writes
        nothing."""
        a, b, loc = world["caseA"], world["caseB"], world["locator"]
        body = {"locator_id": loc.id, "statement": "Second observation.",
                "method_description": "Review."}
        provider = self._provider({
            "alice": (_g("alice", Capability.CASE_READ, a.id),),               # read only
            "bob": (_g("bob", Capability.CASE_READ, a.id),
                    _g("bob", Capability.OBSERVATION_CREATE, b.id)),           # write, wrong case
            "carol": (_g("carol", Capability.CASE_READ, a.id),
                      _g("carol", Capability.OBSERVATION_CREATE, a.id)),       # write, right case
        })
        client = self._client(pg_engine, verifier_registry, provider, store)

        n0 = len(pg_session.execute(select(Observation).where(Observation.case_id == a.id)).scalars().all())
        # (7) read authority cannot write.
        r_alice = client.post(f"/cases/{a.id}/observations", json=body, headers=self._h("tok-alice"))
        assert r_alice.status_code == 403 and "action-not-authorized" in r_alice.json()["detail"]
        # (8) Case-B grant cannot write in Case A.
        r_bob = client.post(f"/cases/{a.id}/observations", json=body, headers=self._h("tok-bob"))
        assert r_bob.status_code == 403 and "out-of-scope-resource" in r_bob.json()["detail"]
        # (9) denied writes nothing.
        pg_session.expire_all()
        n1 = len(pg_session.execute(select(Observation).where(Observation.case_id == a.id)).scalars().all())
        assert n1 == n0
        # Properly authorized write succeeds.
        r_carol = client.post(f"/cases/{a.id}/observations", json=body, headers=self._h("tok-carol"))
        assert r_carol.status_code == 201, r_carol.text
        pg_session.expire_all()
        n2 = len(pg_session.execute(select(Observation).where(Observation.case_id == a.id)).scalars().all())
        assert n2 == n0 + 1

    def test_h11_authentication_grants_no_authority(
        self, pg_engine, store, world, verifier_registry
    ):
        """Test 11: an authenticated principal with no grants is denied —
        authentication alone confers nothing."""
        a = world["caseA"]
        provider = self._provider({})  # nobody has any grant
        client = self._client(pg_engine, verifier_registry, provider, store)
        r = client.get(f"/cases/{a.id}", headers=self._h("tok-alice"))
        assert r.status_code == 404  # generic denial (no CASE_READ)

    def test_h11_authorize_conformance(self, pg_session):
        """Test 17: the Python and PostgreSQL authorize renderings derive
        identical results from the same normalized grant facts."""
        checks = [
            (Capability.OBSERVATION_CREATE, "cA", [(Capability.OBSERVATION_CREATE, "cA")], "ALLOW"),
            (Capability.OBSERVATION_CREATE, "cA", [(Capability.OBSERVATION_CREATE, "cB")], "RESOURCE_SCOPE_MISMATCH"),
            (Capability.SEALED_CONTENT_READ, "cA", [(Capability.SEALED_METADATA_READ, "cA")], "CAPABILITY_NOT_GRANTED"),
            (Capability.CASE_READ, "cA", [], "CAPABILITY_NOT_GRANTED"),
            (Capability.SEALED_VERIFY, "cA", [(Capability.SEALED_VERIFY, "cA"), (Capability.CASE_READ, "cA")], "ALLOW"),
        ]
        divergences = []
        for required, case, grant_specs, expected in checks:
            grants = tuple(_g("p", c, cid) for c, cid in grant_specs)
            d = authorize(required, case, grants)
            py = "ALLOW" if d.allowed else d.reason
            pg = pg_session.execute(text(
                "SELECT argus_private.authorize(:req, :case, CAST(:caps AS text[]), CAST(:scopes AS text[]))"
            ), {"req": required.value, "case": case,
                "caps": "{" + ",".join(c.value for c, _ in grant_specs) + "}",
                "scopes": "{" + ",".join(cid for _, cid in grant_specs) + "}"}).scalar()
            if not (py == pg == expected):
                divergences.append(f"{required.value}@{case}: py={py} pg={pg} expected={expected}")
        assert not divergences, "H11 falsified:\n" + "\n".join(divergences)

    def test_h11_authority_changes_no_epistemic_state(
        self, pg_engine, pg_session, store, world, verifier_registry
    ):
        """Test 10: granting/denying authority changes no stored field or
        derived state on any record."""
        a, sealed = world["caseA"], world["sealed"]
        before = pg_session.get(EvidenceArtifact, sealed.id)
        snap = (before.hash_digest, before.size_bytes, before.status.value,
                before.acquisition_description)
        # Two different authority views of the same case.
        for grants in ({"x": (_g("x", Capability.CASE_READ, a.id),)},
                       {"x": (_g("x", Capability.CASE_READ, a.id),
                              _g("x", Capability.SEALED_METADATA_READ, a.id),
                              _g("x", Capability.SEALED_CONTENT_READ, a.id))}):
            provider = self._provider(grants)
            client = self._client(pg_engine, verifier_registry, provider, store)
            from argus.domain.actor_binding import AuthenticatedPrincipal, PrincipalClass
            verifier_registry._registry["tok-x"] = AuthenticatedPrincipal(
                "x", PrincipalClass.HUMAN, "dev-token")
            client.get(f"/cases/{a.id}", headers=self._h("tok-x"))
        pg_session.expire_all()
        after = pg_session.get(EvidenceArtifact, sealed.id)
        assert (after.hash_digest, after.size_bytes, after.status.value,
                after.acquisition_description) == snap
