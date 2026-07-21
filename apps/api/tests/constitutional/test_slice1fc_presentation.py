"""Slice 1F-C — the visible review surface (ODE Hypothesis H12).

H12 (refined, AGC Session 022): a human-facing presentation can render an
authorized constitutional Case projection while preserving completeness,
plurality, temporal truth, explicit boundaries, visibility constraints,
accessibility-relevant semantics, and peer non-preference — without
labels, ordering, prominence, color, grouping, or interaction defaults
introducing new epistemic meaning or a privileged narrative.

Expectations transcribed from CASE_PRESENTATION.md 0.1.0 (leg 3). Honest
bounds: the renderer is a declared single implementation downstream of
the authorized projection; static DOM inspection verifies
accessibility-semantic SOURCE parity, never full assistive-technology
conformance.
"""

from __future__ import annotations

import inspect

import pytest
from bs4 import BeautifulSoup

from argus.presentation import conformance, render
from argus.presentation.conformance import scan_presentation
from argus.presentation.render import render_case_review

from argus.domain.authority import AuthorityGrant, Capability
from argus.domain.transitions import seal_artifact
from argus.ingestion.contradictions import (
    create_contradiction, dispose_contradiction, link_contradiction,
)
from argus.ingestion.hypotheses import create_hypothesis, retract_hypothesis
from argus.ingestion.interpretations import create_interpretation
from argus.ingestion.observations import create_observation, create_source_locator
from argus.ingestion.service import (
    create_artifact_record, create_case, stage_upload, verify_and_activate,
)
from argus.ingestion.unknowns import create_unknown, link_unknown, resolve_unknown

SYNTHETIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 96 + b"ARGUS-1FC"
UNC = "No material uncertainty has been identified from the cited observations, but the interpretation remains provisional."
S1 = "The sedan visible at 19:42 was already parked before the recording interval began."
S2 = "The sedan visible at 19:42 was completing a parking maneuver as the recording interval began."
S3 = "The sedan visible at 19:42 was briefly stopped mid-street before continuing."
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


def _g(pid, cap, case_id):
    return AuthorityGrant(pid, cap, "CASE", case_id)


# ---------------------------------------------------------------------------
# Red-team fixtures (CASE_PRESENTATION.md §12): synthetic violating HTML —
# never dangerous variants in the production template — that MUST fail the
# conformance scanner (the O12 discipline applied to presentation).
# ---------------------------------------------------------------------------

_RT_PROJECTION = {
    "case": {"id": "c1", "title": "T", "status": "OPEN"},
    "hypotheses": [
        {"citation": "HYP-000001", "explanatory_statement": "Statement one.",
         "retraction": None},
        {"citation": "HYP-000002", "explanatory_statement": "Statement two.",
         "retraction": {"reason": "Withdrawn after re-review."}},
    ],
}

RED_TEAM_FIXTURES = {
    "featured-slot": (
        '<main><section class="featured-hypothesis">Hypothesis — HYP-000001 Statement one.</section>'
        '<p>Hypothesis — HYP-000002 Statement two. RETRACTED Withdrawn after re-review.</p></main>',
        "attribute-contamination",
    ),
    "primary-vocabulary": (
        '<main><p>Primary hypothesis: Hypothesis — HYP-000001 Statement one.</p>'
        '<p>Hypothesis — HYP-000002 Statement two. RETRACTED Withdrawn after re-review.</p></main>',
        "phrase-contamination",
    ),
    "health-based-ordering": (
        '<main><p>Hypothesis — HYP-000002 Statement two. RETRACTED Withdrawn after re-review.</p>'
        '<p>Hypothesis — HYP-000001 Statement one.</p></main>',
        "order-violation",
    ),
    "first-card-only-expanded": (
        '<main><details open><summary>Hypothesis — HYP-000001</summary>Statement one.</details>'
        '<details><summary>Hypothesis — HYP-000002</summary>Statement two. RETRACTED Withdrawn after re-review.</details></main>',
        "expansion-asymmetry",
    ),
    "hidden-retraction": (
        '<main><p>Hypothesis — HYP-000001 Statement one.</p></main>',
        "order-violation",  # the retracted card is missing entirely
    ),
    "truth-css-class": (
        '<main><p class="true-state">Hypothesis — HYP-000001 Statement one.</p>'
        '<p>Hypothesis — HYP-000002 Statement two. RETRACTED Withdrawn after re-review.</p></main>',
        "attribute-contamination",
    ),
    "synthesized-summary": (
        '<main><p>Hypothesis — HYP-000001 Statement one.</p>'
        '<p>Hypothesis — HYP-000002 Statement two. RETRACTED Withdrawn after re-review.</p>'
        '<p>Summary: this hypothesis is less reliable because it faces a contradiction.</p></main>',
        "phrase-contamination",
    ),
    "duplicated-statement": (
        '<main><header>Key finding: Statement one.</header>'
        '<p>Hypothesis — HYP-000001 Statement one.</p>'
        '<p>Hypothesis — HYP-000002 Statement two. RETRACTED Withdrawn after re-review.</p></main>',
        "duplication-violation",
    ),
}


class TestConformanceScanner:
    def test_red_team_fixtures_fail_scanner(self):
        """Every violating fixture is caught with the expected violation
        class — the constraints function as discovery instruments (O12)."""
        for name, (html, expected_kind) in RED_TEAM_FIXTURES.items():
            violations = scan_presentation(html, _RT_PROJECTION)
            assert violations, f"{name}: scanner found nothing"
            assert any(expected_kind in v for v in violations), (
                f"{name}: expected {expected_kind}, got {violations}"
            )

    def test_clean_fixture_passes(self):
        html = ('<main><p>Hypothesis — HYP-000001 Statement one.</p>'
                '<p>Hypothesis — HYP-000002 Statement two. RETRACTED '
                'Withdrawn after re-review.</p></main>')
        assert scan_presentation(html, _RT_PROJECTION) == []


class TestRendererIsDownstreamOfAuthority:
    def test_projection_only_authority(self):
        """Session 022 test 19 (structural): the renderer takes only the
        projection — it holds no grants, imports no authority module, and
        calls no authorize()."""
        params = list(inspect.signature(render_case_review).parameters)
        assert params == ["projection"]
        # No authority machinery is importable or callable from the
        # renderer or scanner: scan import lines and call sites, and the
        # module namespaces (docstrings may mention the prohibition).
        for module in (render, conformance):
            source = inspect.getsource(module)
            import_lines = [l for l in source.splitlines()
                            if l.strip().startswith(("import ", "from "))]
            assert not any("authority" in l for l in import_lines), import_lines
            assert "authorize(" not in source.replace("no authorize(", "")
            assert not any("authoriz" in name.lower() for name in vars(module))


@pytest.mark.postgres
class TestExperimentH12:
    @pytest.fixture()
    def world(self, pg_session, store, investigator, verifier):
        """The Session 021 fixture: two competing Interpretations, one
        resolved Unknown, one disposed Contradiction, two alternative
        Hypotheses, one retracted Hypothesis, one SEALED artifact, health
        differences, historical/current pairs."""
        case = create_case(pg_session, title="review case",
                           legal_authority_basis="w", responsible=investigator)
        staged = stage_upload(store, SYNTHETIC + b"-full")
        full = create_artifact_record(pg_session, staged, case=case, actor=investigator,
                                      media_type="image/png", acquisition_description="full artifact")
        verify_and_activate(pg_session, store, full, verifier)
        staged2 = stage_upload(store, SYNTHETIC + b"-sealed")
        sealed = create_artifact_record(pg_session, staged2, case=case, actor=investigator,
                                        media_type="image/png", acquisition_description="sealed artifact")
        verify_and_activate(pg_session, store, sealed, verifier)
        seal_artifact(pg_session, sealed, investigator, legal_basis="protective order")
        loc = create_source_locator(pg_session, artifact=full, scheme="byte-range",
                                    payload={"start": 0, "end": 8}, actor=investigator)
        obs = create_observation(pg_session, case=case, locator_ids=[loc.id],
                                 statement="Blue sedan visible.",
                                 method_description="Direct visual review.",
                                 actor=investigator)
        ia = create_interpretation(
            pg_session, case=case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement="The visible vehicle is stationary throughout 19:42:00-19:42:10.",
            reasoning_description="Position comparison across the cited frames.",
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator)
        ib = create_interpretation(
            pg_session, case=case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement="The visible vehicle changes position during 19:42:00-19:42:10.",
            reasoning_description="Position comparison across the cited frames.",
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator)
        unk = create_unknown(pg_session, case=case,
                             question="Who was driving the sedan between 19:41 and 19:43?",
                             actor=investigator)
        con = create_contradiction(
            pg_session, case=case,
            members=[("Interpretation", ia.id), ("Interpretation", ib.id)],
            description="Interpretations assert mutually exclusive motion states under identical scope.",
            contradiction_type="DESCRIPTIVE",
            scope_definition="Same vehicle, camera, frame, interval.",
            incompatibility_basis="A vehicle cannot be both stationary and moving in the same interval.",
            actor=investigator)
        h1 = create_hypothesis(
            pg_session, case=case,
            groundings=[(ia.id, "DERIVED_FROM"), (ib.id, "DERIVED_FROM")],
            explanatory_statement=S1, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator, alternative_absence_explanation=ALT_ABSENCE,
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON)
        h2 = create_hypothesis(
            pg_session, case=case,
            groundings=[(ia.id, "DERIVED_FROM"), (ib.id, "DERIVED_FROM")],
            explanatory_statement=S2, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator,
            alternatives=[(h1.id, "Both explanations account for the same admitted motion-state interpretations.")],
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON)
        h3 = create_hypothesis(
            pg_session, case=case, groundings=[(ia.id, "DERIVED_FROM")],
            explanatory_statement=S3, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator, alternative_absence_explanation=ALT_ABSENCE,
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON)
        for h in (h1, h2):
            link_unknown(pg_session, unknown=unk, target_type="Hypothesis",
                         target_id=h.id, nature="The driver's identity limits this explanation.",
                         actor=investigator)
            link_contradiction(pg_session, contradiction=con, hypothesis_id=h.id,
                               explanation="The scoped incompatibility bears on this explanation.",
                               actor=investigator)
        resolve_unknown(pg_session, unknown=unk, resolution_type="UNRESOLVABLE",
                        rationale="No admissible source identifies the driver.",
                        answering_claims=None, actor=investigator)
        dispose_contradiction(pg_session, contradiction=con, outcome="EXPLAINED",
                              rationale="The intervals differ by one frame; scopes were not identical.",
                              informing_refs=None, actor=investigator)
        retract_hypothesis(pg_session, h3, investigator,
                           reason="Author withdrew the mid-street account after frame re-review.")
        pg_session.commit()  # release audit-head locks before TestClient use
        return {"case": case, "sealed": sealed, "h1": h1, "h2": h2, "h3": h3}

    def _registry(self):
        from argus.domain.actor_binding import AuthenticatedPrincipal, PrincipalClass
        from argus.api.authentication import DevTokenVerifier
        return DevTokenVerifier({
            f"tok-{n}": AuthenticatedPrincipal(n, PrincipalClass.HUMAN, "dev-token")
            for n in ("alice", "bob", "carol")
        })

    def _client(self, pg_engine, store, grants: dict):
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import Session, sessionmaker
        from argus.api.app import create_app
        from argus.api.authority_provider import DevAuthorityProvider
        factory = sessionmaker(bind=pg_engine, class_=Session)
        app = create_app(session_factory=factory, verifier=self._registry(),
                         authority_provider=DevAuthorityProvider(grants),
                         content_store=store)
        return TestClient(app, raise_server_exceptions=True)

    def _page(self, pg_engine, store, world, *, extra=()):
        case = world["case"]
        grants = {"alice": (_g("alice", Capability.CASE_READ, case.id),)
                  + tuple(_g("alice", c, case.id) for c in extra)}
        client = self._client(pg_engine, store, grants)
        r = client.get(f"/cases/{case.id}/review",
                       headers={"Authorization": "Bearer tok-alice"})
        assert r.status_code == 200, r.text
        rj = client.get(f"/cases/{case.id}",
                        headers={"Authorization": "Bearer tok-alice"})
        return r.text, rj.json()

    def test_h12_conformance_scan_and_parity(self, pg_engine, store, world):
        """The scanner passes the real page against its real projection:
        contamination-free, citation order, complete, no duplication,
        retraction visible, uniform expansion."""
        html, projection = self._page(pg_engine, store, world)
        assert scan_presentation(html, projection) == []
        # Content parity, projection-derived values (both directions is the
        # scanner's occurrence rule; here the presence sweep):
        soup = BeautifulSoup(html, "html.parser")
        visible = soup.get_text(" ")
        for h in projection["hypotheses"]:
            for value in (h["citation"], h["explanatory_statement"],
                          h["testability_statement"], h["challenge_condition"],
                          h["alternative_articulation_at_creation"],
                          h["derived"]["hypothesis_health"],
                          h["derived"]["current_alternative_state"]):
                assert value in visible, value
        for i in projection["interpretations"]:
            assert i["meaning_statement"] in visible
        for u in projection["unknowns"]:
            assert u["question"] in visible and u["derived"]["status"] in visible
        for c in projection["contradictions"]:
            assert c["incompatibility_basis"] in visible
            assert c["disposition"]["rationale"] in visible

    def test_h12_peer_rule_equality(self, pg_engine, store, world):
        """Session 022 test 20: normalized structural comparison of the two
        live Hypothesis cards — identical hierarchy, label sequence,
        classes, heading level, state, and (absence of) interactions."""
        html, projection = self._page(pg_engine, store, world)
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("article.hypothesis-record")
        live = [c for c in cards if "RETRACTED" not in c.get_text()]
        assert len(live) == 2

        def shape(card):
            return {
                "classes": tuple(card.get("class")),
                "heading": card.find("h3").name,
                "labels": tuple(dt.get_text(strip=True) for dt in card.find_all("dt")),
                "tags": tuple(el.name for el in card.find_all(["h3", "div", "ul"])),
                "focusables": tuple(el.name for el in card.find_all(
                    ["a", "button", "input", "select", "textarea", "details"])),
            }
        s1, s2 = shape(live[0]), shape(live[1])
        assert s1 == s2
        assert s1["focusables"] == ()  # no interactions exist to privilege

    def test_h12_boundaries_history_and_health_semantics(self, pg_engine, store, world):
        """Boundaries as relationships; historical beside current; health as
        text with neutral definitions; no truth iconography or coloring."""
        html, projection = self._page(pg_engine, store, world)
        soup = BeautifulSoup(html, "html.parser")
        visible = soup.get_text(" ")
        assert "Limited by Unknown" in visible
        assert "Challenged by Contradiction" in visible
        assert "At creation" in visible and "Currently" in visible
        assert ALT_ABSENCE in visible  # historical truth still on the page
        assert "One or more derivational foundations are no longer current." in visible
        for icon in ("✓", "✗", "⚠"):
            assert icon not in html
        style = soup.find("style").get_text()
        for banned in ("green", "red", "#0f0", "#f00"):
            assert banned not in style.lower()

    def test_h12_retraction_visible_and_counted(self, pg_engine, store, world):
        html, projection = self._page(pg_engine, store, world)
        soup = BeautifulSoup(html, "html.parser")
        visible = soup.get_text(" ")
        assert "1 retracted records present" in visible
        h3 = world["h3"]
        card = next(c for c in soup.select("article.hypothesis-record")
                    if h3.citation in c.get_text())
        assert "RETRACTED" in card.get_text()
        assert "Author withdrew the mid-street account after frame re-review." in card.get_text()

    def test_h12_accessibility_semantic_source_parity(self, pg_engine, store, world):
        """Static DOM inspection only (Amendment 3): landmark, heading
        hierarchy, source order = citation order, peer depth, no autofocus,
        no unauthorized controls. NOT full AT conformance."""
        html, projection = self._page(pg_engine, store, world)
        soup = BeautifulSoup(html, "html.parser")
        assert soup.find("main") is not None
        assert soup.find("h1").get_text(strip=True) == "Case Review"
        sections = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]
        assert sections == ["Case", "Evidence Artifacts", "Observations",
                            "Interpretations", "Unknowns", "Contradictions",
                            "Hypotheses", "Hypothesis Alternatives", "Definitions"]
        # Source order of hypothesis headings equals citation order.
        headings = [h.get_text(strip=True) for h in soup.find_all("h3")
                    if h.get_text(strip=True).startswith("Hypothesis —")]
        expected = [f"Hypothesis — {h['citation']}" for h in projection["hypotheses"]]
        assert headings == expected
        # Peer depth: all hypothesis cards are siblings of one parent.
        cards = soup.select("article.hypothesis-record")
        assert len({id(c.parent) for c in cards}) == 1
        # No autofocus; no focusable controls anywhere (read-only surface).
        assert "autofocus" not in html
        assert soup.find_all(["button", "input", "select", "textarea", "a"]) == []
        # No ordinal identity labels.
        for banned in ("First Hypothesis", "Main Hypothesis", "Hypothesis #"):
            assert banned not in html

    def test_h12_no_review_workflow_controls(self, pg_engine, store, world):
        """No interaction labeled accept/confirm/approve exists; no form,
        no mutation affordance of any kind."""
        html, projection = self._page(pg_engine, store, world)
        soup = BeautifulSoup(html, "html.parser")
        assert soup.find("form") is None
        low = html.lower()
        for banned in ("accept", "approve", "confirm", "validate"):
            assert banned not in low

    def test_h12_visibility_constraints_on_page(self, pg_engine, store, world):
        """Explicit SEALED withholding when existence is authorized; the
        withheld metadata is genuinely absent from the markup."""
        html, projection = self._page(pg_engine, store, world)
        assert "Metadata withheld — Authority required" in html
        assert "Content withheld — Authority required" in html
        assert "sealed artifact" not in html  # the withheld acquisition text
        # With SEALED_METADATA_READ the metadata appears and the withholding
        # label narrows to content only.
        html2, _ = self._page(pg_engine, store, world,
                              extra=(Capability.SEALED_METADATA_READ,))
        assert "sealed artifact" in html2
        assert "Metadata withheld — Authority required" not in html2
        assert "Content withheld — Authority required" in html2

    def test_h12_shared_epistemic_content_across_projections(self, pg_engine, store, world):
        """Session 021 test 12: authority changes the artifact envelope,
        never the epistemic sections — identical hypothesis/interpretation
        markup across differently-authorized principals."""
        html1, p1 = self._page(pg_engine, store, world)
        html2, p2 = self._page(pg_engine, store, world,
                               extra=(Capability.SEALED_METADATA_READ,))
        for section in ("observations", "interpretations", "unknowns",
                        "contradictions", "hypotheses", "hypothesis_alternatives"):
            assert p1[section] == p2[section]
        s1 = BeautifulSoup(html1, "html.parser")
        s2 = BeautifulSoup(html2, "html.parser")
        for sec_id in ("h-hypotheses", "h-interpretations"):
            sec1 = s1.find("h2", id=sec_id).parent
            sec2 = s2.find("h2", id=sec_id).parent
            assert str(sec1) == str(sec2)

    def test_h12_no_existence_leak_review(self, pg_engine, store, world):
        """The review route applies the 1F-B generic denial before rendering
        begins — no CASE_READ means the identical 404 for real and
        nonexistent cases."""
        case = world["case"]
        client = self._client(pg_engine, store, {"bob": ()})
        r_real = client.get(f"/cases/{case.id}/review",
                            headers={"Authorization": "Bearer tok-bob"})
        r_fake = client.get("/cases/does-not-exist/review",
                            headers={"Authorization": "Bearer tok-bob"})
        assert r_real.status_code == 404 and r_fake.status_code == 404
        assert r_real.json() == r_fake.json()
        r_unauth = client.get(f"/cases/{case.id}/review")
        assert r_unauth.status_code == 401
