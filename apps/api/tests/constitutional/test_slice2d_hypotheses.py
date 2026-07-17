"""Slice 2D — Hypotheses as provisional explanatory structures (ODE H7).

H7 (refined, AGC Session 012): independent implementations can admit
plural, provisional explanatory structures while preserving derivational
support, falsifiability, explicit alternative and boundary articulation,
uncertainty, and non-preference — without automatically revising,
promoting, refuting, or adjudicating any explanation.

Expectations transcribed from CONSTITUTIONAL_PREDICATES.md 0.6.0
(triangulation leg 3, ONT-PRN-015).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text

from argus.domain import admissibility as adm
from argus.domain import fingerprints
from argus.domain.actors import ActorClass
from argus.domain.chain import verify_case_chain
from argus.domain.exceptions import ConstitutionalViolation
from argus.domain.models import (
    ContradictionLink,
    Hypothesis,
    HypothesisAlternative,
    HypothesisGrounding,
    UnknownLink,
)
from argus.ingestion.contradictions import create_contradiction, dispose_contradiction, link_contradiction
from argus.ingestion.hypotheses import (
    contradiction_boundary_state,
    create_hypothesis,
    current_alternative_state,
    hypothesis_health,
    link_hypothesis_alternative,
    retract_hypothesis,
    unknown_boundary_state,
)
from argus.ingestion.interpretations import create_interpretation, retract_interpretation
from argus.ingestion.observations import create_observation, create_source_locator
from argus.ingestion.service import (
    create_artifact_record,
    create_case,
    stage_upload,
    verify_and_activate,
)
from argus.ingestion.unknowns import create_unknown, link_unknown, resolve_unknown

SYNTHETIC_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128 + b"ARGUS-SYNTHETIC-2D"

# Gold fixtures (CONSTITUTIONAL_PREDICATES.md 0.6.0).
STATEMENT_1 = "The sedan visible at 19:42 was already parked before the recording interval began."
STATEMENT_2 = "The sedan visible at 19:42 was completing a parking maneuver as the recording interval began."
H_REASONING = "Composed from the admitted motion-state interpretations over the cited frames."
TESTABILITY = "Additional footage covering 19:41:00-19:42:00 would bear on this explanation."
CHALLENGE = "Footage showing the parking spot empty at 19:41:30 would challenge this explanation."
UNC = "No material uncertainty has been identified from the cited observations, but the interpretation remains provisional."
ALT_ABSENCE = ("No alternative explanation is currently articulated: the alternative "
               "space considered (arrival or departure during the interval) is not "
               "yet supported by any grounded Interpretation.")
NO_UNK = ("No specific unresolved gap is presently articulated for this explanation; "
          "unknowns may exist that have not been recognized.")
NO_CON = ("No formal contradiction is currently linked; this does not assert the "
          "explanation is uncontradicted in reality.")
ALT_RELATION = "Both explanations account for the same admitted motion-state interpretations."

MEANING_A = "The visible vehicle is stationary throughout 19:42:00-19:42:10."
MEANING_B = "The visible vehicle changes position during 19:42:00-19:42:10."
SCOPE = "Same vehicle, same camera, same coordinate frame, same interval 19:42:00-19:42:10."
BASIS = ("A single vehicle cannot be both stationary throughout and changing "
         "position during the same interval in the same coordinate frame.")

G = adm.InterpretationGroundingState
VALID_G = (G(exists=True, grounded=True),)


def _kwargs(**overrides):
    base = dict(
        explanatory_statement=STATEMENT_1,
        reasoning_description=H_REASONING,
        uncertainty_status="ACKNOWLEDGED",
        uncertainty_explanation=UNC,
        testability_statement=TESTABILITY,
        challenge_condition=CHALLENGE,
        actor_class=ActorClass.HUMAN,
        groundings=VALID_G,
        alternative_link_count=0,
        alternative_absence_explanation=ALT_ABSENCE,
        unknown_link_count=0,
        no_current_unknowns_explanation=NO_UNK,
        contradiction_link_count=0,
        no_current_contradictions_explanation=NO_CON,
    )
    base.update(overrides)
    return base


# The canonical refusal matrix, transcribed (never imported from the
# implementation): name -> (validator kwargs, expected codes).
HYPOTHESIS_MATRIX = {
    "valid": (_kwargs(), ()),
    "statement-required": (_kwargs(explanatory_statement="  "), (adm.HYP_STATEMENT_REQUIRED,)),
    "reasoning-required": (_kwargs(reasoning_description=""), (adm.HYP_REASONING_REQUIRED,)),
    "uncertainty-status-required": (_kwargs(uncertainty_status="CERTAIN"),
                                    (adm.HYP_UNCERTAINTY_STATUS_REQUIRED,)),
    "uncertainty-explanation-required": (_kwargs(uncertainty_explanation=" "),
                                         (adm.HYP_UNCERTAINTY_EXPLANATION_REQUIRED,)),
    "testability-required": (_kwargs(testability_statement=""), (adm.HYP_TESTABILITY_REQUIRED,)),
    "challenge-condition-required": (_kwargs(challenge_condition="  "),
                                     (adm.HYP_CHALLENGE_CONDITION_REQUIRED,)),
    "ai-actor-not-authorized": (_kwargs(actor_class=ActorClass.AI), (adm.HYP_UNSUPPORTED_ACTOR,)),
    "system-actor": (_kwargs(actor_class=ActorClass.SYSTEM), (adm.HYP_UNSUPPORTED_ACTOR,)),
    "no-groundings": (_kwargs(groundings=()), (adm.HYP_DERIVATION_REQUIRED,)),
    "contextual-only-inadmissible": (
        _kwargs(groundings=(G(exists=True, grounded=True, role="CONTEXTUALIZED_BY"),)),
        (adm.HYP_DERIVATION_REQUIRED,)),
    "invalid-grounding-role": (
        _kwargs(groundings=(G(exists=True, grounded=True, role="SUPPORTING"),)),
        (adm.HYP_DERIVATION_REQUIRED, adm.HYP_INVALID_GROUNDING_ROLE)),
    "unknown-interpretation": (_kwargs(groundings=(G(exists=False),)),
                               (adm.HYP_UNKNOWN_INTERPRETATION,)),
    "interpretation-retracted": (_kwargs(groundings=(G(exists=True, retracted=True),)),
                                 (adm.HYP_INTERPRETATION_RETRACTED,)),
    "interpretation-degraded": (_kwargs(groundings=(G(exists=True, grounded=False),)),
                                (adm.HYP_INTERPRETATION_DEGRADED,)),
    "cross-case-grounding": (
        _kwargs(groundings=(G(exists=True, grounded=True, same_case=False),)),
        (adm.HYP_CROSS_CASE,)),
    "duplicate-grounding": (
        _kwargs(groundings=(G(exists=True, grounded=True), G(exists=True, grounded=True)),
                distinct_grounding_count=1),
        (adm.HYP_DUPLICATE_GROUNDING,)),
    "alternative-articulation-required": (
        _kwargs(alternative_absence_explanation=None), (adm.HYP_ALT_ARTICULATION_REQUIRED,)),
    "alternative-articulation-conflict": (
        _kwargs(alternative_link_count=1), (adm.HYP_ALT_ARTICULATION_CONFLICT,)),
    "unknown-boundary-articulation-required": (
        _kwargs(no_current_unknowns_explanation="  "), (adm.HYP_UNK_ARTICULATION_REQUIRED,)),
    "unknown-boundary-articulation-conflict": (
        _kwargs(unknown_link_count=1), (adm.HYP_UNK_ARTICULATION_CONFLICT,)),
    "contradiction-boundary-articulation-required": (
        _kwargs(no_current_contradictions_explanation=None),
        (adm.HYP_CON_ARTICULATION_REQUIRED,)),
    "contradiction-boundary-articulation-conflict": (
        _kwargs(contradiction_link_count=1), (adm.HYP_CON_ARTICULATION_CONFLICT,)),
    "comparative-language": (
        _kwargs(explanatory_statement=STATEMENT_1 + " This is the best explanation."),
        (adm.HYP_COMPARATIVE_LANGUAGE,)),
}


class TestPythonRendering:
    def test_hypothesis_admissibility_matrix(self):
        """ONT-HYP-001/ONT-PRN-023 → Articles III, IV, VII, IX: an
        explanation exists only when it can state what supports it, what
        limits it, what could challenge it, and what remains unknown."""
        for name, (kwargs, expected) in HYPOTHESIS_MATRIX.items():
            codes = adm.validate_hypothesis(**kwargs)
            assert sorted(codes) == sorted(expected), name

    def test_alternative_link_matrix(self):
        """Session 012 Amendment 4: the ten link requirements as refusals."""
        ok = dict(self_link=False, both_exist=True, same_case=True, duplicate=False,
                  relation_explanation=ALT_RELATION, actor_class=ActorClass.HUMAN)
        assert adm.validate_hypothesis_alternative(**ok) == ()
        assert adm.ALT_SELF_LINK in adm.validate_hypothesis_alternative(
            **{**ok, "self_link": True})
        assert adm.ALT_UNKNOWN_HYPOTHESIS in adm.validate_hypothesis_alternative(
            **{**ok, "both_exist": False})
        assert adm.ALT_CROSS_CASE in adm.validate_hypothesis_alternative(
            **{**ok, "same_case": False})
        assert adm.ALT_DUPLICATE in adm.validate_hypothesis_alternative(
            **{**ok, "duplicate": True})
        assert adm.ALT_EXPLANATION_REQUIRED in adm.validate_hypothesis_alternative(
            **{**ok, "relation_explanation": " "})
        assert adm.ALT_COMPARATIVE_LANGUAGE in adm.validate_hypothesis_alternative(
            **{**ok, "relation_explanation": "This one is stronger than the other."})
        assert adm.ACTOR_NOT_PERMITTED in adm.validate_hypothesis_alternative(
            **{**ok, "actor_class": ActorClass.AI})

    def test_contradiction_link_matrix(self):
        """A Contradiction challenges; it never kills. CHALLENGED_BY_CONTRADICTION
        is the only relationship that exists."""
        ok = dict(both_exist=True, same_case=True, duplicate=False,
                  relationship_type=adm.CHALLENGED_BY_CONTRADICTION,
                  explanation="The scoped incompatibility bears on this explanation.",
                  actor_class=ActorClass.HUMAN)
        assert adm.validate_contradiction_link(**ok) == ()
        assert adm.CONLINK_TARGET_NOT_FOUND in adm.validate_contradiction_link(
            **{**ok, "both_exist": False})
        assert adm.CONLINK_CROSS_CASE in adm.validate_contradiction_link(
            **{**ok, "same_case": False})
        assert adm.CONLINK_DUPLICATE in adm.validate_contradiction_link(
            **{**ok, "duplicate": True})
        for forbidden in ("REFUTED_BY", "DISPROVEN_BY", "DEFEATED_BY", "WEAKENED_BY",
                          "INVALIDATED_BY"):
            assert adm.CONLINK_INVALID_RELATIONSHIP in adm.validate_contradiction_link(
                **{**ok, "relationship_type": forbidden})
        assert adm.CONLINK_EXPLANATION_REQUIRED in adm.validate_contradiction_link(
            **{**ok, "explanation": ""})
        assert adm.ACTOR_NOT_PERMITTED in adm.validate_contradiction_link(
            **{**ok, "actor_class": ActorClass.SYSTEM})

    def test_hypothesis_health_three_states(self):
        """Amendment 5 → Article II: DERIVED_FROM only; even UNSUPPORTED
        never auto-retracts (surfaced for human review)."""
        cur = G(exists=True, grounded=True)
        bad = G(exists=True, retracted=True)
        ctx_bad = G(exists=True, retracted=True, role="CONTEXTUALIZED_BY")
        assert adm.hypothesis_health((cur, cur)) == "CURRENT"
        assert adm.hypothesis_health((cur, bad)) == "DEGRADED"
        assert adm.hypothesis_health((bad, bad)) == "UNSUPPORTED"
        assert adm.hypothesis_health(()) == "UNSUPPORTED"
        # Contextual groundings never enter the computation.
        assert adm.hypothesis_health((cur, ctx_bad)) == "CURRENT"

    def test_derived_states(self):
        """Amendment 2/3: current state derived, never stored; the
        historical articulation lives elsewhere and is never recomputed."""
        assert adm.current_alternative_state(()) == "NO_CURRENT_ALTERNATIVES"
        assert adm.current_alternative_state((True,)) == "ALTERNATIVES_CURRENT"
        assert adm.current_alternative_state((False,)) == "ALTERNATIVES_DEGRADED"
        assert adm.current_alternative_state((False, True)) == "ALTERNATIVES_CURRENT"
        assert adm.unknown_boundary_state(()) == "NONE_ARTICULATED"
        assert adm.unknown_boundary_state((True,)) == "LIMITS_CURRENT"
        assert adm.unknown_boundary_state((False,)) == "LIMITS_RESOLVED"
        assert adm.contradiction_boundary_state(()) == "NONE_ARTICULATED"
        assert adm.contradiction_boundary_state((True, False)) == "CHALLENGES_CURRENT"
        assert adm.contradiction_boundary_state((False,)) == "CHALLENGES_DISPOSED"


@pytest.mark.postgres
class TestExperimentH7:
    @pytest.fixture()
    def pg_case(self, pg_session, investigator):
        return create_case(
            pg_session, title="Slice 2D explanations",
            legal_authority_basis="Test warrant 2026-SYN-2D", responsible=investigator,
        )

    @pytest.fixture()
    def competing_interpretations(self, pg_session, store, pg_case, investigator, verifier):
        staged = stage_upload(store, SYNTHETIC_IMAGE)
        artifact = create_artifact_record(
            pg_session, staged, case=pg_case, actor=investigator,
            media_type="image/png", acquisition_description="Synthetic 2D video still.",
        )
        verify_and_activate(pg_session, store, artifact, verifier)
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
            meaning_statement=MEANING_A, reasoning_description="Position comparison across the cited frames.",
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator,
        )
        b = create_interpretation(
            pg_session, case=pg_case, groundings=[(obs.id, "SUPPORTING")],
            meaning_statement=MEANING_B, reasoning_description="Position comparison across the cited frames.",
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            actor=investigator,
        )
        return a, b

    def _snap(self, h: Hypothesis) -> tuple:
        return (h.citation, h.explanatory_statement, h.reasoning_description,
                h.uncertainty_status, h.uncertainty_explanation,
                h.testability_statement, h.challenge_condition,
                h.alternative_articulation_at_creation,
                h.alternative_absence_explanation,
                h.no_current_unknowns_explanation,
                h.no_current_contradictions_explanation, h.retracted_at)

    def _make(self, pg_session, pg_case, interps, investigator, statement=STATEMENT_1,
              **extra):
        a, b = interps
        articulation = dict(
            alternative_absence_explanation=ALT_ABSENCE,
            no_current_unknowns_explanation=NO_UNK,
            no_current_contradictions_explanation=NO_CON,
        )
        articulation.update(extra)
        return create_hypothesis(
            pg_session, case=pg_case,
            groundings=[(a.id, "DERIVED_FROM"), (b.id, "DERIVED_FROM")],
            explanatory_statement=statement, reasoning_description=H_REASONING,
            uncertainty_status="ACKNOWLEDGED", uncertainty_explanation=UNC,
            testability_statement=TESTABILITY, challenge_condition=CHALLENGE,
            actor=investigator, **articulation,
        )

    def _pg_state(self, pg_session, fn, hyp_id):
        return pg_session.execute(
            text(f"SELECT argus_private.{fn}(:id)"), {"id": hyp_id}
        ).scalar()

    def test_h7_acceptance_explanations_without_verdict(
        self, pg_session, pg_case, competing_interpretations, investigator
    ):
        """The Session 012 eight-step acceptance sequence: historical
        articulation vs. current derived state; boundary events and sibling
        retraction leave every explanation byte-identical.
        (ONT-HYP-001/ONT-PRN-023 → Articles II, III, IV, VII, IX.)"""
        a, b = competing_interpretations

        # 1. HYP-000001: no alternative currently articulated, with the
        #    considered-space explanation; explicit boundary articulation;
        #    testability and challenge conditions.
        h1 = self._make(pg_session, pg_case, (a, b), investigator)
        assert h1.citation == "HYP-000001"
        assert h1.alternative_articulation_at_creation.value == "NONE_CURRENTLY_ARTICULATED_AT_CREATION"
        assert h1.alternative_absence_explanation == ALT_ABSENCE
        groundings = pg_session.execute(select(HypothesisGrounding).where(
            HypothesisGrounding.hypothesis_id == h1.id)).scalars().all()
        assert len(groundings) == 2
        # Fingerprint v2 conformance: stored (PG-computed) == Python rendering.
        by_int = {g.interpretation_id: g for g in groundings}
        for interp in (a, b):
            expected = fingerprints.interpretation_fingerprint_v2(
                interp.meaning_statement, interp.reasoning_description,
                interp.uncertainty_status.value, interp.uncertainty_explanation)
            assert by_int[interp.id].interpretation_fingerprint == expected
        assert hypothesis_health(pg_session, h1) == "CURRENT"
        assert self._pg_state(pg_session, "hypothesis_health", h1.id) == "CURRENT"
        assert current_alternative_state(pg_session, h1) == "NO_CURRENT_ALTERNATIVES"
        assert self._pg_state(pg_session, "current_alternative_state", h1.id) == "NO_CURRENT_ALTERNATIVES"
        assert unknown_boundary_state(pg_session, h1) == "NONE_ARTICULATED"
        assert contradiction_boundary_state(pg_session, h1) == "NONE_ARTICULATED"
        before_h1 = self._snap(h1)

        # 2. HYP-000002, linked symmetrically to HYP-000001 at creation.
        h2 = self._make(
            pg_session, pg_case, (a, b), investigator, statement=STATEMENT_2,
            alternatives=[(h1.id, ALT_RELATION)],
            alternative_absence_explanation=None,
        )
        assert h2.citation == "HYP-000002"
        assert h2.alternative_articulation_at_creation.value == "ALTERNATIVE_LINKED_AT_CREATION"
        assert h2.alternative_absence_explanation is None

        # 3. HYP-000001's creation-time absence explanation remains intact;
        #    its CURRENT derived state changes; neither Hypothesis modified;
        #    no preference assigned.
        pg_session.expire_all()
        assert self._snap(h1) == before_h1  # historical truth preserved
        for h in (h1, h2):
            assert current_alternative_state(pg_session, h) == "ALTERNATIVES_CURRENT"
            assert self._pg_state(pg_session, "current_alternative_state", h.id) == "ALTERNATIVES_CURRENT"
        links = pg_session.execute(select(HypothesisAlternative)).scalars().all()
        assert len(links) == 1
        assert links[0].hypothesis_a_id < links[0].hypothesis_b_id  # normalized, unordered

        # 4. Link the same Unknown and Contradiction to both.
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
        before_h1, before_h2 = self._snap(h1), self._snap(h2)
        for h in (h1, h2):
            link_unknown(pg_session, unknown=unknown, target_type="Hypothesis",
                         target_id=h.id, nature="The driver's identity limits this explanation.",
                         actor=investigator)
            link_contradiction(pg_session, contradiction=contradiction,
                               hypothesis_id=h.id,
                               explanation="The scoped incompatibility bears on this explanation.",
                               actor=investigator)
        pg_session.expire_all()
        for h in (h1, h2):
            assert unknown_boundary_state(pg_session, h) == "LIMITS_CURRENT"
            assert self._pg_state(pg_session, "unknown_boundary_state", h.id) == "LIMITS_CURRENT"
            assert contradiction_boundary_state(pg_session, h) == "CHALLENGES_CURRENT"
            assert self._pg_state(pg_session, "contradiction_boundary_state", h.id) == "CHALLENGES_CURRENT"
        assert self._snap(h1) == before_h1 and self._snap(h2) == before_h2

        # Fingerprint v1 conformance on the boundary snapshot.
        clink = pg_session.execute(select(ContradictionLink).where(
            ContradictionLink.hypothesis_id == h1.id)).scalars().one()
        assert clink.relationship_type == "CHALLENGED_BY_CONTRADICTION"
        assert clink.hypothesis_fingerprint == fingerprints.hypothesis_fingerprint_v1(
            h1.explanatory_statement, h1.reasoning_description,
            h1.uncertainty_status.value, h1.uncertainty_explanation,
            h1.testability_statement, h1.challenge_condition)
        assert clink.hypothesis_fingerprint == pg_session.execute(
            text("SELECT argus_private.hypothesis_fingerprint_v1(:id)"), {"id": h1.id}
        ).scalar()

        # 5. Resolve the Unknown; dispose the Contradiction.
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

        # 6. Both Hypotheses byte-identical; links remain; boundary state
        #    changes only through derivation; nothing revised or promoted.
        pg_session.expire_all()
        assert self._snap(h1) == before_h1 and self._snap(h2) == before_h2
        assert pg_session.execute(select(UnknownLink).where(
            UnknownLink.target_type == "Hypothesis")).scalars().all()
        assert len(pg_session.execute(select(ContradictionLink)).scalars().all()) == 2
        for h in (h1, h2):
            assert unknown_boundary_state(pg_session, h) == "LIMITS_RESOLVED"
            assert self._pg_state(pg_session, "unknown_boundary_state", h.id) == "LIMITS_RESOLVED"
            assert contradiction_boundary_state(pg_session, h) == "CHALLENGES_DISPOSED"
            assert self._pg_state(pg_session, "contradiction_boundary_state", h.id) == "CHALLENGES_DISPOSED"

        # 7. Retract HYP-000002.
        retract_hypothesis(pg_session, h2, investigator,
                           reason="Author withdrew the maneuver account after frame re-review.")

        # 8. HYP-000001 not promoted; the historical link remains; current
        #    alternative health accurately derived; creation-time absence
        #    explanation remains historical truth.
        pg_session.expire_all()
        assert self._snap(h1) == before_h1
        assert h1.alternative_absence_explanation == ALT_ABSENCE
        assert len(pg_session.execute(select(HypothesisAlternative)).scalars().all()) == 1
        assert current_alternative_state(pg_session, h1) == "ALTERNATIVES_DEGRADED"
        assert self._pg_state(pg_session, "current_alternative_state", h1.id) == "ALTERNATIVES_DEGRADED"
        assert verify_case_chain(pg_session, pg_case.id).valid

    def test_h7_validator_conformance(
        self, pg_session, pg_case, competing_interpretations
    ):
        """H7: SQL and Python renderings agree on expressible matrix rows —
        both compared against the transcription, never each other alone."""
        a, b = competing_interpretations

        def sql_validate(statement, reasoning, unc_status, unc_expl, testability,
                         challenge, actor, int_ids, roles,
                         alt_count=0, alt_absence=ALT_ABSENCE,
                         unk_count=0, no_unk=NO_UNK, con_count=0, no_con=NO_CON):
            return sorted(pg_session.execute(text(
                "SELECT argus_private.validate_hypothesis(:c, CAST(:ints AS text[]),"
                " CAST(:roles AS text[]), :s, :r, :us, :ue, :t, :ch, :a,"
                " :altc, :alta, :unkc, :nounk, :conc, :nocon)"
            ), {"c": pg_case.id,
                "ints": "{" + ",".join(int_ids) + "}",
                "roles": "{" + ",".join(roles) + "}",
                "s": statement, "r": reasoning, "us": unc_status, "ue": unc_expl,
                "t": testability, "ch": challenge, "a": actor,
                "altc": alt_count, "alta": alt_absence,
                "unkc": unk_count, "nounk": no_unk,
                "conc": con_count, "nocon": no_con}).scalar())

        base = (STATEMENT_1, H_REASONING, "ACKNOWLEDGED", UNC, TESTABILITY, CHALLENGE)
        checks = [
            ("valid", base + ("HUMAN", [a.id, b.id], ["DERIVED_FROM", "DERIVED_FROM"]), {}, ()),
            ("statement", ("  ",) + base[1:] + ("HUMAN", [a.id], ["DERIVED_FROM"]), {},
             (adm.HYP_STATEMENT_REQUIRED,)),
            ("unc-status", base[:2] + ("CERTAIN",) + base[3:] + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {}, (adm.HYP_UNCERTAINTY_STATUS_REQUIRED,)),
            ("testability", base[:4] + (" ", CHALLENGE) + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {}, (adm.HYP_TESTABILITY_REQUIRED,)),
            ("challenge", base[:5] + ("",) + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {}, (adm.HYP_CHALLENGE_CONDITION_REQUIRED,)),
            ("ai-actor", base + ("AI", [a.id], ["DERIVED_FROM"]), {},
             (adm.HYP_UNSUPPORTED_ACTOR,)),
            ("contextual-only", base + ("HUMAN", [a.id, b.id],
                                        ["CONTEXTUALIZED_BY", "CONTEXTUALIZED_BY"]), {},
             (adm.HYP_DERIVATION_REQUIRED,)),
            ("bad-role", base + ("HUMAN", [a.id], ["SUPPORTING"]), {},
             (adm.HYP_DERIVATION_REQUIRED, adm.HYP_INVALID_GROUNDING_ROLE)),
            ("unknown-interp", base + ("HUMAN", [a.id, "deadbeef"],
                                       ["DERIVED_FROM", "DERIVED_FROM"]), {},
             (adm.HYP_UNKNOWN_INTERPRETATION,)),
            ("duplicate", base + ("HUMAN", [a.id, a.id], ["DERIVED_FROM", "DERIVED_FROM"]),
             {}, (adm.HYP_DUPLICATE_GROUNDING,)),
            ("alt-required", base + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {"alt_absence": None}, (adm.HYP_ALT_ARTICULATION_REQUIRED,)),
            ("alt-conflict", base + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {"alt_count": 1}, (adm.HYP_ALT_ARTICULATION_CONFLICT,)),
            ("unk-required", base + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {"no_unk": " "}, (adm.HYP_UNK_ARTICULATION_REQUIRED,)),
            ("unk-conflict", base + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {"unk_count": 1}, (adm.HYP_UNK_ARTICULATION_CONFLICT,)),
            ("con-required", base + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {"no_con": None}, (adm.HYP_CON_ARTICULATION_REQUIRED,)),
            ("con-conflict", base + ("HUMAN", [a.id], ["DERIVED_FROM"]),
             {"con_count": 1}, (adm.HYP_CON_ARTICULATION_CONFLICT,)),
            ("comparative", (STATEMENT_1 + " This is the best explanation.",) + base[1:]
             + ("HUMAN", [a.id], ["DERIVED_FROM"]), {},
             (adm.HYP_COMPARATIVE_LANGUAGE,)),
        ]
        divergences = [
            f"{name}: pg={sql_validate(*inputs, **extra)} expected={sorted(exp)}"
            for name, inputs, extra, exp in checks
            if sql_validate(*inputs, **extra) != sorted(exp)
        ]
        assert not divergences, "H7 falsified for:\n" + "\n".join(divergences)

    def test_h7_no_preference_surface(self, pg_session):
        """Resolution 018 → Article IV: no field or constraint carries a
        verdict, preference, probability, promotion, or refutation surface
        on any Slice 2D table (structured surfaces per the Session 012
        caution)."""
        forbidden = ("verdict", "probab", "confiden", "preferred", "primary",
                     "leading", "best", "winner", "accept", "theory", "rank",
                     "weight", "score", "refut", "disprov", "defeat", "weaken",
                     "invalidat", "promot")
        for table in (Hypothesis.__table__, HypothesisGrounding.__table__,
                      HypothesisAlternative.__table__, ContradictionLink.__table__):
            for col in table.columns:
                assert not any(f in col.name.lower() for f in forbidden), col.name
        constraints = [r for r in pg_session.execute(text(
            "SELECT conname FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
            "WHERE t.relname LIKE 'hypothes%' OR t.relname = 'contradiction_links'"
        )).scalars()]
        assert constraints  # the scan actually saw the slice's tables
        assert not any(any(f in c for f in forbidden) for c in constraints)

    def test_alternative_link_operation_at_db(
        self, pg_session, pg_case, competing_interpretations, investigator
    ):
        """Amendment 4: the dedicated operation exists for later
        articulation; self-links, duplicates, and empty or comparative
        explanations are refused; neither Hypothesis is modified."""
        from sqlalchemy.exc import DBAPIError

        h1 = self._make(pg_session, pg_case, competing_interpretations, investigator)
        h2 = self._make(pg_session, pg_case, competing_interpretations, investigator,
                        statement=STATEMENT_2)
        before = (self._snap(h1), self._snap(h2))

        link = link_hypothesis_alternative(
            pg_session, hypothesis_a=h1, hypothesis_b_id=h2.id,
            relation_explanation=ALT_RELATION, actor=investigator,
        )
        assert link.hypothesis_a_id < link.hypothesis_b_id
        pg_session.expire_all()
        assert (self._snap(h1), self._snap(h2)) == before

        with pytest.raises((ConstitutionalViolation, DBAPIError)):
            link_hypothesis_alternative(
                pg_session, hypothesis_a=h2, hypothesis_b_id=h1.id,
                relation_explanation=ALT_RELATION, actor=investigator,
            )  # duplicate, order-independent
        pg_session.rollback()
        with pytest.raises((ConstitutionalViolation, DBAPIError)):
            link_hypothesis_alternative(
                pg_session, hypothesis_a=h1, hypothesis_b_id=h1.id,
                relation_explanation=ALT_RELATION, actor=investigator,
            )
        pg_session.rollback()
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.link_hypothesis_alternative('l1', :a, :b,"
                " 'This account is clearly stronger.', 'HUMAN', 'det.reyes', NULL)"
            ), {"a": h1.id, "b": h2.id})
            pg_session.commit()
        pg_session.rollback()
        assert "alt-" in str(err.value)

    def test_human_only_and_db_enforcement(
        self, pg_session, pg_case, competing_interpretations, investigator
    ):
        """AI authorship NOT AUTHORIZED; the app role cannot write the
        tables directly; boundary links are human-only at the function."""
        from sqlalchemy.exc import DBAPIError

        a, b = competing_interpretations
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.create_hypothesis('h0', :c,"
                " CAST(:ints AS text[]), CAST('{DERIVED_FROM}' AS text[]),"
                " :s, :r, 'ACKNOWLEDGED', :u, :t, :ch,"
                " CAST('{}' AS text[]), CAST('{}' AS text[]), :alta,"
                " CAST('{}' AS text[]), CAST('{}' AS text[]), :nounk,"
                " CAST('{}' AS text[]), CAST('{}' AS text[]), :nocon,"
                " 'AI', 'model-x', 'v1')"
            ), {"c": pg_case.id, "ints": "{" + a.id + "}", "s": STATEMENT_1,
                "r": H_REASONING, "u": UNC, "t": TESTABILITY, "ch": CHALLENGE,
                "alta": ALT_ABSENCE, "nounk": NO_UNK, "nocon": NO_CON})
            pg_session.commit()
        pg_session.rollback()
        assert "unsupported-actor" in str(err.value)

        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "INSERT INTO public.hypotheses (id, case_id, citation,"
                " explanatory_statement, reasoning_description, uncertainty_status,"
                " uncertainty_explanation, testability_statement, challenge_condition,"
                " alternative_articulation_at_creation, alternative_absence_explanation,"
                " created_by_class, created_by_id, created_at)"
                " VALUES ('f00d2d', :c, 'HYP-000099', 's', 'r', 'ACKNOWLEDGED', 'u',"
                " 't', 'ch', 'NONE_CURRENTLY_ARTICULATED_AT_CREATION', 'x',"
                " 'HUMAN', 'x', now())"
            ), {"c": pg_case.id})
            pg_session.commit()
        pg_session.rollback()
        assert "permission denied" in str(err.value)

        h1 = self._make(pg_session, pg_case, (a, b), investigator)
        with pytest.raises(DBAPIError) as err:
            pg_session.execute(text(
                "SELECT argus_private.link_contradiction('l2', 'nonesuch', :h,"
                " 'x', 'SYSTEM', 'svc', NULL)"), {"h": h1.id})
            pg_session.commit()
        pg_session.rollback()
        assert "actor-not-permitted" in str(err.value)
