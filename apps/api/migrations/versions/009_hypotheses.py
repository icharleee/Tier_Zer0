"""009 — Hypotheses as provisional explanatory structures (Slice 2D, ADR-0028).

ONT-PRN-023: an explanation is constitutionally admissible only when the
system can state what supports it, what limits it, what could challenge it,
and what remains unknown. The decisive rule, enforced here: ARGUS may
preserve explanations for examination; it may never convert explanation
into verdict. No probability, confidence, preference, promotion, or
refutation surface exists; creation is human-only; every derived state
(health, alternative state, boundary states) is computed, never stored.

Revision ID: 009_hypotheses
Revises: 008_contradictions
"""

from alembic import op
import sqlalchemy as sa

revision = "009_hypotheses"
down_revision = "008_contradictions"
branch_labels = None
depends_on = None

DEFINER = "LANGUAGE plpgsql SECURITY DEFINER SET search_path = argus_private, pg_catalog, pg_temp"
INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"

# Transcribed from CONSTITUTIONAL_PREDICATES.md 0.6.0 (same list as Slice 2A).
GUARD_TERMS = (
    "'more likely','most likely','more probable','most probable',"
    "'stronger','strongest','weaker','preferred',"
    "'primary explanation','best explanation'"
)


def upgrade() -> None:
    op.create_table(
        "hypotheses",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("citation", sa.String(16), nullable=False),
        sa.Column("explanatory_statement", sa.Text, nullable=False),
        sa.Column("reasoning_description", sa.Text, nullable=False),
        sa.Column("uncertainty_status", sa.String(16), nullable=False),
        sa.Column("uncertainty_explanation", sa.Text, nullable=False),
        sa.Column("testability_statement", sa.Text, nullable=False),
        sa.Column("challenge_condition", sa.Text, nullable=False),
        sa.Column("alternative_articulation_at_creation", sa.String(48), nullable=False),
        sa.Column("alternative_absence_explanation", sa.Text, nullable=True),
        sa.Column("no_current_unknowns_explanation", sa.Text, nullable=True),
        sa.Column("no_current_contradictions_explanation", sa.Text, nullable=True),
        sa.Column("created_by_class", sa.String(16), nullable=False),
        sa.Column("created_by_id", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.UniqueConstraint("case_id", "citation", name="uq_hyp_citation"),
        sa.CheckConstraint(
            "uncertainty_status IN ('ACKNOWLEDGED','MATERIAL','LIMITING','UNRESOLVED')",
            name="ck_hyp_unc_status",
        ),
        sa.CheckConstraint(
            "alternative_articulation_at_creation IN "
            "('ALTERNATIVE_LINKED_AT_CREATION','NONE_CURRENTLY_ARTICULATED_AT_CREATION')",
            name="ck_hyp_articulation",
        ),
        # The creation-time articulation pairs with its explanation exactly
        # (Session 012, Amendment 2): historical truth, immutable.
        sa.CheckConstraint(
            "(alternative_articulation_at_creation = 'NONE_CURRENTLY_ARTICULATED_AT_CREATION')"
            " = (alternative_absence_explanation IS NOT NULL)",
            name="ck_hyp_articulation_pairing",
        ),
        sa.CheckConstraint("length(trim(explanatory_statement)) > 0", name="ck_hyp_statement"),
        sa.CheckConstraint("length(trim(reasoning_description)) > 0", name="ck_hyp_reasoning"),
        sa.CheckConstraint("length(trim(uncertainty_explanation)) > 0", name="ck_hyp_unc_expl"),
        sa.CheckConstraint("length(trim(testability_statement)) > 0", name="ck_hyp_testability"),
        sa.CheckConstraint("length(trim(challenge_condition)) > 0", name="ck_hyp_challenge"),
        sa.CheckConstraint(
            "alternative_absence_explanation IS NULL OR length(trim(alternative_absence_explanation)) > 0",
            name="ck_hyp_alt_absence_expl",
        ),
        sa.CheckConstraint(
            "no_current_unknowns_explanation IS NULL OR length(trim(no_current_unknowns_explanation)) > 0",
            name="ck_hyp_no_unk_expl",
        ),
        sa.CheckConstraint(
            "no_current_contradictions_explanation IS NULL OR length(trim(no_current_contradictions_explanation)) > 0",
            name="ck_hyp_no_con_expl",
        ),
    )
    op.create_table(
        "hypothesis_groundings",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("hypothesis_id", sa.String(32), sa.ForeignKey("hypotheses.id"), nullable=False),
        sa.Column("interpretation_id", sa.String(32), sa.ForeignKey("interpretations.id"), nullable=False),
        sa.Column("interpretation_fingerprint", sa.String(64), nullable=False),
        sa.Column("grounding_role", sa.String(24), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("hypothesis_id", "interpretation_id", name="uq_hyp_grounding"),
        sa.CheckConstraint(
            "grounding_role IN ('DERIVED_FROM','CONTEXTUALIZED_BY')",
            name="ck_hyp_grounding_role",
        ),
    )
    op.create_table(
        "hypothesis_alternatives",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("hypothesis_a_id", sa.String(32), sa.ForeignKey("hypotheses.id"), nullable=False),
        sa.Column("hypothesis_b_id", sa.String(32), sa.ForeignKey("hypotheses.id"), nullable=False),
        sa.Column("relation_explanation", sa.Text, nullable=False),
        sa.Column("linked_by_class", sa.String(16), nullable=False),
        sa.Column("linked_by_id", sa.String(200), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("hypothesis_a_id", "hypothesis_b_id", name="uq_hyp_alternative"),
        # Unordered symmetric pair, normalized by identifier (Amendment 2).
        sa.CheckConstraint("hypothesis_a_id < hypothesis_b_id", name="ck_hyp_alt_order"),
        sa.CheckConstraint("length(trim(relation_explanation)) > 0", name="ck_hyp_alt_explanation"),
    )
    op.create_table(
        "contradiction_links",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("contradiction_id", sa.String(32), sa.ForeignKey("contradictions.id"), nullable=False),
        sa.Column("hypothesis_id", sa.String(32), sa.ForeignKey("hypotheses.id"), nullable=False),
        sa.Column("hypothesis_fingerprint", sa.String(64), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("linked_by_class", sa.String(16), nullable=False),
        sa.Column("linked_by_id", sa.String(200), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.UniqueConstraint("contradiction_id", "hypothesis_id", name="uq_con_link"),
        # A Contradiction challenges; it never kills. No refutation value
        # exists or may ever be added (Session 012).
        sa.CheckConstraint(
            "relationship_type = 'CHALLENGED_BY_CONTRADICTION'",
            name="ck_con_link_relationship",
        ),
        sa.CheckConstraint("length(trim(explanation)) > 0", name="ck_con_link_explanation"),
    )
    for t in ("hypotheses", "hypothesis_groundings", "hypothesis_alternatives",
              "contradiction_links"):
        op.execute(f"GRANT SELECT ON public.{t} TO argus_app")

    # Unknown bounds Hypothesis too (LIMITED_BY_UNKNOWN).
    op.drop_constraint("ck_unk_link_target", "unknown_links", type_="check")
    op.create_check_constraint(
        "ck_unk_link_target",
        "unknown_links",
        "target_type IN ('Observation','Interpretation','EvidenceArtifact','Hypothesis')",
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION argus_private.link_unknown(
            p_link_id text, p_unknown_id text, p_target_type text,
            p_target_id text, p_nature text,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_case text; v_target_case text;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-UNK-001: inadmissible: ONT-UNK-001:unsupported-actor';
            END IF;
            SELECT case_id INTO v_case FROM public.unknowns WHERE id = p_unknown_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-UNK-001: unknown record %', p_unknown_id;
            END IF;
            IF p_target_type = 'Observation' THEN
                SELECT case_id INTO v_target_case FROM public.observations WHERE id = p_target_id;
            ELSIF p_target_type = 'Interpretation' THEN
                SELECT case_id INTO v_target_case FROM public.interpretations WHERE id = p_target_id;
            ELSIF p_target_type = 'EvidenceArtifact' THEN
                SELECT case_id INTO v_target_case FROM public.evidence_artifacts WHERE id = p_target_id;
            ELSIF p_target_type = 'Hypothesis' THEN
                SELECT case_id INTO v_target_case FROM public.hypotheses WHERE id = p_target_id;
            END IF;
            IF v_target_case IS NULL THEN
                RAISE EXCEPTION 'ONT-UNK-001: inadmissible: ONT-UNK-001:unknown-target';
            END IF;
            IF v_target_case IS DISTINCT FROM v_case THEN
                RAISE EXCEPTION 'ONT-UNK-001: inadmissible: ONT-UNK-001:cross-case-link';
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            INSERT INTO public.unknown_links
                (id, unknown_id, target_type, target_id, nature, linked_at)
            VALUES (p_link_id, p_unknown_id, p_target_type, p_target_id,
                    p_nature, clock_timestamp());
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver, 'unknown-linked',
                'UnknownLink', p_link_id, 'SUCCEEDED',
                jsonb_build_object('unknown_id', p_unknown_id,
                                   'target_type', p_target_type,
                                   'target_id', p_target_id));
            RETURN p_link_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.interpretation_state_v2(
            p_id text,
            OUT o_case text, OUT o_retracted timestamptz,
            OUT o_grounded boolean, OUT o_fingerprint text
        )
        """ + INVOKER + """
        AS $$
        BEGIN
            SELECT case_id, retracted_at,
                   argus_private.interpretation_grounding_health(id) = 'GROUNDED',
                   encode(sha256(convert_to(
                       meaning_statement || chr(31) || reasoning_description
                       || chr(31) || uncertainty_status || chr(31)
                       || uncertainty_explanation, 'UTF8')), 'hex')
              INTO o_case, o_retracted, o_grounded, o_fingerprint
              FROM public.interpretations WHERE id = p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.hypothesis_fingerprint_v1(p_id text)
        RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v text;
        BEGIN
            SELECT encode(sha256(convert_to(
                       explanatory_statement || chr(31) || reasoning_description
                       || chr(31) || uncertainty_status || chr(31)
                       || uncertainty_explanation || chr(31)
                       || testability_statement || chr(31)
                       || challenge_condition, 'UTF8')), 'hex')
              INTO v FROM public.hypotheses WHERE id = p_id;
            RETURN v;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.validate_hypothesis(
            p_case_id text, p_int_ids text[], p_roles text[],
            p_statement text, p_reasoning text, p_unc_status text,
            p_unc_expl text, p_testability text, p_challenge text,
            p_actor_class text,
            p_alt_count integer, p_alt_absence text,
            p_unk_count integer, p_no_unk text,
            p_con_count integer, p_no_con text
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_codes text[] := ARRAY[]::text[];
            v_prose text; v_term text; i integer;
            v_s record; v_distinct integer; v_derived boolean := false;
        BEGIN
            IF p_statement IS NULL OR length(trim(p_statement)) = 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:statement-required'::text;
            END IF;
            IF p_reasoning IS NULL OR length(trim(p_reasoning)) = 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:reasoning-required'::text;
            END IF;
            IF p_unc_status IS NULL OR p_unc_status NOT IN
               ('ACKNOWLEDGED','MATERIAL','LIMITING','UNRESOLVED') THEN
                v_codes := v_codes || 'ONT-HYP-001:uncertainty-status-required'::text;
            END IF;
            IF p_unc_expl IS NULL OR length(trim(p_unc_expl)) = 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:uncertainty-explanation-required'::text;
            END IF;
            IF p_testability IS NULL OR length(trim(p_testability)) = 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:testability-required'::text;
            END IF;
            IF p_challenge IS NULL OR length(trim(p_challenge)) = 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:challenge-condition-required'::text;
            END IF;
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                v_codes := v_codes || 'ONT-HYP-001:unsupported-actor'::text;
            END IF;
            v_prose := lower(coalesce(p_statement, '') || ' ' || coalesce(p_reasoning, ''));
            FOREACH v_term IN ARRAY ARRAY[""" + GUARD_TERMS + """]
            LOOP
                IF position(v_term IN v_prose) > 0 THEN
                    v_codes := v_codes || 'ONT-HYP-001:comparative-language'::text;
                    EXIT;
                END IF;
            END LOOP;

            FOR i IN 1 .. coalesce(cardinality(p_int_ids), 0) LOOP
                IF p_roles[i] = 'DERIVED_FROM' THEN v_derived := true; END IF;
            END LOOP;
            IF NOT v_derived THEN
                v_codes := v_codes || 'ONT-HYP-001:derivation-required'::text;
            END IF;
            SELECT count(DISTINCT p_int_ids[j]) INTO v_distinct
              FROM generate_subscripts(coalesce(p_int_ids, ARRAY[]::text[]), 1) AS j;
            IF v_distinct < coalesce(cardinality(p_int_ids), 0) THEN
                v_codes := v_codes || 'ONT-HYP-001:duplicate-grounding'::text;
            END IF;
            FOR i IN 1 .. coalesce(cardinality(p_int_ids), 0) LOOP
                IF p_roles IS NULL OR cardinality(p_roles) < i
                   OR p_roles[i] NOT IN ('DERIVED_FROM','CONTEXTUALIZED_BY') THEN
                    v_codes := v_codes || 'ONT-HYP-001:invalid-grounding-role'::text;
                END IF;
                SELECT * INTO v_s FROM argus_private.interpretation_state_v2(p_int_ids[i]);
                IF v_s.o_case IS NULL THEN
                    v_codes := v_codes || 'ONT-HYP-001:unknown-interpretation'::text;
                    CONTINUE;
                END IF;
                IF v_s.o_retracted IS NOT NULL THEN
                    v_codes := v_codes || 'ONT-HYP-001:interpretation-retracted'::text;
                    CONTINUE;
                END IF;
                IF v_s.o_case IS DISTINCT FROM p_case_id THEN
                    v_codes := v_codes || 'ONT-HYP-001:cross-case-grounding'::text;
                    CONTINUE;
                END IF;
                IF NOT v_s.o_grounded THEN
                    v_codes := v_codes || 'ONT-HYP-001:interpretation-degraded'::text;
                END IF;
            END LOOP;

            -- Resolution 018 articulation: link XOR explicit absence.
            IF coalesce(p_alt_count, 0) <= 0
               AND (p_alt_absence IS NULL OR length(trim(p_alt_absence)) = 0) THEN
                v_codes := v_codes || 'ONT-HYP-001:alternative-articulation-required'::text;
            END IF;
            IF coalesce(p_alt_count, 0) > 0
               AND p_alt_absence IS NOT NULL AND length(trim(p_alt_absence)) > 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:alternative-articulation-conflict'::text;
            END IF;
            IF coalesce(p_unk_count, 0) <= 0
               AND (p_no_unk IS NULL OR length(trim(p_no_unk)) = 0) THEN
                v_codes := v_codes || 'ONT-HYP-001:unknown-boundary-articulation-required'::text;
            END IF;
            IF coalesce(p_unk_count, 0) > 0
               AND p_no_unk IS NOT NULL AND length(trim(p_no_unk)) > 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:unknown-boundary-articulation-conflict'::text;
            END IF;
            IF coalesce(p_con_count, 0) <= 0
               AND (p_no_con IS NULL OR length(trim(p_no_con)) = 0) THEN
                v_codes := v_codes || 'ONT-HYP-001:contradiction-boundary-articulation-required'::text;
            END IF;
            IF coalesce(p_con_count, 0) > 0
               AND p_no_con IS NOT NULL AND length(trim(p_no_con)) > 0 THEN
                v_codes := v_codes || 'ONT-HYP-001:contradiction-boundary-articulation-conflict'::text;
            END IF;
            RETURN ARRAY(SELECT DISTINCT c FROM unnest(v_codes) AS c ORDER BY c);
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.link_hypothesis_alternative(
            p_id text, p_a text, p_b text, p_explanation text,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_case_a text; v_case_b text; v_lo text; v_hi text;
                v_prose text; v_term text;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-PRN-007:actor-not-permitted';
            END IF;
            IF p_a = p_b THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-HYP-001:alt-self-link';
            END IF;
            SELECT case_id INTO v_case_a FROM public.hypotheses WHERE id = p_a;
            SELECT case_id INTO v_case_b FROM public.hypotheses WHERE id = p_b;
            IF v_case_a IS NULL OR v_case_b IS NULL THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-HYP-001:alt-unknown-hypothesis';
            END IF;
            IF v_case_a IS DISTINCT FROM v_case_b THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-HYP-001:alt-cross-case';
            END IF;
            v_lo := least(p_a, p_b); v_hi := greatest(p_a, p_b);
            IF EXISTS (SELECT 1 FROM public.hypothesis_alternatives
                        WHERE hypothesis_a_id = v_lo AND hypothesis_b_id = v_hi) THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-HYP-001:alt-duplicate';
            END IF;
            IF p_explanation IS NULL OR length(trim(p_explanation)) = 0 THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-HYP-001:alt-explanation-required';
            END IF;
            v_prose := lower(p_explanation);
            FOREACH v_term IN ARRAY ARRAY[""" + GUARD_TERMS + """]
            LOOP
                IF position(v_term IN v_prose) > 0 THEN
                    RAISE EXCEPTION 'ONT-HYP-001: inadmissible: ONT-HYP-001:alt-comparative-language';
                END IF;
            END LOOP;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case_a FOR UPDATE;
            -- Deliberately: neither hypothesis is modified. Naming an
            -- alternative confers no status on either side (Article IV).
            INSERT INTO public.hypothesis_alternatives
                (id, hypothesis_a_id, hypothesis_b_id, relation_explanation,
                 linked_by_class, linked_by_id, linked_at)
            VALUES (p_id, v_lo, v_hi, p_explanation,
                    p_actor_class, p_actor_id, clock_timestamp());
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case_a,
                p_actor_class, p_actor_id, p_ai_ver, 'hypothesis-alternative-linked',
                'HypothesisAlternative', p_id, 'SUCCEEDED',
                jsonb_build_object('hypothesis_a_id', v_lo, 'hypothesis_b_id', v_hi));
            RETURN p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.link_contradiction(
            p_id text, p_con_id text, p_hyp_id text, p_explanation text,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_case_con text; v_case_hyp text;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-CON-001: inadmissible: ONT-PRN-007:actor-not-permitted';
            END IF;
            SELECT case_id INTO v_case_con FROM public.contradictions WHERE id = p_con_id;
            SELECT case_id INTO v_case_hyp FROM public.hypotheses WHERE id = p_hyp_id;
            IF v_case_con IS NULL OR v_case_hyp IS NULL THEN
                RAISE EXCEPTION 'ONT-CON-001: inadmissible: ONT-CON-001:link-target-not-found';
            END IF;
            IF v_case_con IS DISTINCT FROM v_case_hyp THEN
                RAISE EXCEPTION 'ONT-CON-001: inadmissible: ONT-CON-001:link-cross-case';
            END IF;
            IF EXISTS (SELECT 1 FROM public.contradiction_links
                        WHERE contradiction_id = p_con_id AND hypothesis_id = p_hyp_id) THEN
                RAISE EXCEPTION 'ONT-CON-001: inadmissible: ONT-CON-001:link-duplicate';
            END IF;
            IF p_explanation IS NULL OR length(trim(p_explanation)) = 0 THEN
                RAISE EXCEPTION 'ONT-CON-001: inadmissible: ONT-CON-001:link-explanation-required';
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case_con FOR UPDATE;
            -- CHALLENGED_BY_CONTRADICTION is the only relationship that
            -- exists; a Contradiction challenges without killing. Neither
            -- endpoint is altered; disposed Contradictions stay linked.
            INSERT INTO public.contradiction_links
                (id, contradiction_id, hypothesis_id, hypothesis_fingerprint,
                 relationship_type, explanation, linked_by_class, linked_by_id,
                 linked_at)
            VALUES (p_id, p_con_id, p_hyp_id,
                    argus_private.hypothesis_fingerprint_v1(p_hyp_id),
                    'CHALLENGED_BY_CONTRADICTION', p_explanation,
                    p_actor_class, p_actor_id, clock_timestamp());
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case_con,
                p_actor_class, p_actor_id, p_ai_ver, 'contradiction-linked',
                'ContradictionLink', p_id, 'SUCCEEDED',
                jsonb_build_object('contradiction_id', p_con_id,
                                   'hypothesis_id', p_hyp_id,
                                   'relationship_type', 'CHALLENGED_BY_CONTRADICTION'));
            RETURN p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.create_hypothesis(
            p_id text, p_case_id text, p_int_ids text[], p_roles text[],
            p_statement text, p_reasoning text, p_unc_status text,
            p_unc_expl text, p_testability text, p_challenge text,
            p_alt_ids text[], p_alt_expls text[], p_alt_absence text,
            p_unk_ids text[], p_unk_natures text[], p_no_unk text,
            p_con_ids text[], p_con_expls text[], p_no_con text,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE
            v_codes text[]; v_n integer; v_citation text; i integer;
            v_s record; v_articulation text;
        BEGIN
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = p_case_id FOR UPDATE;
            v_codes := argus_private.validate_hypothesis(
                p_case_id, p_int_ids, p_roles, p_statement, p_reasoning,
                p_unc_status, p_unc_expl, p_testability, p_challenge,
                p_actor_class,
                coalesce(cardinality(p_alt_ids), 0), p_alt_absence,
                coalesce(cardinality(p_unk_ids), 0), p_no_unk,
                coalesce(cardinality(p_con_ids), 0), p_no_con);
            IF cardinality(v_codes) > 0 THEN
                RAISE EXCEPTION 'ONT-HYP-001: inadmissible: %', array_to_string(v_codes, ', ');
            END IF;
            SELECT count(*) + 1 INTO v_n FROM public.hypotheses WHERE case_id = p_case_id;
            v_citation := 'HYP-' || lpad(v_n::text, 6, '0');
            v_articulation := CASE WHEN coalesce(cardinality(p_alt_ids), 0) > 0
                                   THEN 'ALTERNATIVE_LINKED_AT_CREATION'
                                   ELSE 'NONE_CURRENTLY_ARTICULATED_AT_CREATION' END;
            INSERT INTO public.hypotheses
                (id, case_id, citation, explanatory_statement, reasoning_description,
                 uncertainty_status, uncertainty_explanation, testability_statement,
                 challenge_condition, alternative_articulation_at_creation,
                 alternative_absence_explanation, no_current_unknowns_explanation,
                 no_current_contradictions_explanation, created_by_class,
                 created_by_id, created_at)
            VALUES (p_id, p_case_id, v_citation, p_statement, p_reasoning,
                    p_unc_status, p_unc_expl, p_testability, p_challenge,
                    v_articulation, p_alt_absence, p_no_unk, p_no_con,
                    p_actor_class, p_actor_id, clock_timestamp());
            FOR i IN 1 .. coalesce(cardinality(p_int_ids), 0) LOOP
                SELECT * INTO v_s FROM argus_private.interpretation_state_v2(p_int_ids[i]);
                INSERT INTO public.hypothesis_groundings
                    (id, hypothesis_id, interpretation_id,
                     interpretation_fingerprint, grounding_role, linked_at)
                VALUES (replace(gen_random_uuid()::text, '-', ''), p_id,
                        p_int_ids[i], v_s.o_fingerprint, p_roles[i],
                        clock_timestamp());
            END LOOP;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), p_case_id,
                p_actor_class, p_actor_id, p_ai_ver, 'claim-created',
                'Hypothesis', p_id, 'SUCCEEDED',
                jsonb_build_object('citation', v_citation,
                                   'interpretations', to_jsonb(p_int_ids),
                                   'uncertainty_status', p_unc_status,
                                   'alternative_articulation', v_articulation));
            -- Articulation links reuse the dedicated operations so their
            -- validation and audit semantics exist exactly once.
            FOR i IN 1 .. coalesce(cardinality(p_alt_ids), 0) LOOP
                PERFORM argus_private.link_hypothesis_alternative(
                    replace(gen_random_uuid()::text, '-', ''), p_id,
                    p_alt_ids[i], p_alt_expls[i],
                    p_actor_class, p_actor_id, p_ai_ver);
            END LOOP;
            FOR i IN 1 .. coalesce(cardinality(p_unk_ids), 0) LOOP
                PERFORM argus_private.link_unknown(
                    replace(gen_random_uuid()::text, '-', ''), p_unk_ids[i],
                    'Hypothesis', p_id, p_unk_natures[i],
                    p_actor_class, p_actor_id, p_ai_ver);
            END LOOP;
            FOR i IN 1 .. coalesce(cardinality(p_con_ids), 0) LOOP
                PERFORM argus_private.link_contradiction(
                    replace(gen_random_uuid()::text, '-', ''), p_con_ids[i],
                    p_id, p_con_expls[i],
                    p_actor_class, p_actor_id, p_ai_ver);
            END LOOP;
            RETURN p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.retract_hypothesis(
            p_id text, p_actor_class text, p_actor_id text,
            p_ai_ver text, p_reason text
        ) RETURNS void
        """ + DEFINER + """
        AS $$
        DECLARE v_case text; v_retracted timestamptz;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-PRN-007: retraction is human-only';
            END IF;
            IF p_reason IS NULL OR length(trim(p_reason)) = 0 THEN
                RAISE EXCEPTION 'ONT-PRN-006: retraction requires a non-empty reason';
            END IF;
            SELECT case_id, retracted_at INTO v_case, v_retracted
              FROM public.hypotheses WHERE id = p_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-PRN-006: unknown record %', p_id;
            END IF;
            IF v_retracted IS NOT NULL THEN
                RAISE EXCEPTION 'ONT-PRN-006: already retracted (retraction is terminal)';
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            -- Retraction retracts one explanation. It promotes no sibling,
            -- removes no alternative link, and alters no boundary record.
            UPDATE public.hypotheses
               SET retracted_at = clock_timestamp(), retraction_reason = p_reason
             WHERE id = p_id;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver, 'claim-retracted',
                'Hypothesis', p_id, 'SUCCEEDED',
                jsonb_build_object('reason', p_reason));
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.hypothesis_health(p_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v_total integer; v_current integer;
        BEGIN
            SELECT count(*) INTO v_total
              FROM public.hypothesis_groundings g
             WHERE g.hypothesis_id = p_id AND g.grounding_role = 'DERIVED_FROM';
            SELECT count(*) INTO v_current
              FROM public.hypothesis_groundings g
              JOIN public.interpretations i ON i.id = g.interpretation_id
             WHERE g.hypothesis_id = p_id AND g.grounding_role = 'DERIVED_FROM'
               AND i.retracted_at IS NULL
               AND argus_private.interpretation_grounding_health(i.id) = 'GROUNDED';
            RETURN CASE WHEN v_total > 0 AND v_current = v_total THEN 'CURRENT'
                        WHEN v_current > 0 THEN 'DEGRADED'
                        ELSE 'UNSUPPORTED' END;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.current_alternative_state(p_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v_total integer; v_active integer;
        BEGIN
            SELECT count(*) INTO v_total FROM public.hypothesis_alternatives
             WHERE hypothesis_a_id = p_id OR hypothesis_b_id = p_id;
            IF v_total = 0 THEN RETURN 'NO_CURRENT_ALTERNATIVES'; END IF;
            SELECT count(*) INTO v_active
              FROM public.hypothesis_alternatives a
              JOIN public.hypotheses h
                ON h.id = CASE WHEN a.hypothesis_a_id = p_id
                               THEN a.hypothesis_b_id ELSE a.hypothesis_a_id END
             WHERE (a.hypothesis_a_id = p_id OR a.hypothesis_b_id = p_id)
               AND h.retracted_at IS NULL;
            RETURN CASE WHEN v_active > 0 THEN 'ALTERNATIVES_CURRENT'
                        ELSE 'ALTERNATIVES_DEGRADED' END;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.unknown_boundary_state(p_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v_total integer; v_open integer;
        BEGIN
            SELECT count(*) INTO v_total FROM public.unknown_links l
             WHERE l.target_type = 'Hypothesis' AND l.target_id = p_id
               AND l.retracted_at IS NULL;
            IF v_total = 0 THEN RETURN 'NONE_ARTICULATED'; END IF;
            SELECT count(*) INTO v_open
              FROM public.unknown_links l
             WHERE l.target_type = 'Hypothesis' AND l.target_id = p_id
               AND l.retracted_at IS NULL
               AND NOT EXISTS (SELECT 1 FROM public.unknown_resolutions r
                                WHERE r.unknown_id = l.unknown_id);
            RETURN CASE WHEN v_open > 0 THEN 'LIMITS_CURRENT'
                        ELSE 'LIMITS_RESOLVED' END;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.contradiction_boundary_state(p_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v_total integer; v_open integer;
        BEGIN
            SELECT count(*) INTO v_total FROM public.contradiction_links l
             WHERE l.hypothesis_id = p_id AND l.retracted_at IS NULL;
            IF v_total = 0 THEN RETURN 'NONE_ARTICULATED'; END IF;
            SELECT count(*) INTO v_open
              FROM public.contradiction_links l
             WHERE l.hypothesis_id = p_id AND l.retracted_at IS NULL
               AND NOT EXISTS (SELECT 1 FROM public.contradiction_dispositions d
                                WHERE d.contradiction_id = l.contradiction_id);
            RETURN CASE WHEN v_open > 0 THEN 'CHALLENGES_CURRENT'
                        ELSE 'CHALLENGES_DISPOSED' END;
        END $$;
        """
    )

    fns = [
        ("interpretation_state_v2", "text"),
        ("hypothesis_fingerprint_v1", "text"),
        ("validate_hypothesis",
         "text, text[], text[], text, text, text, text, text, text, text, "
         "integer, text, integer, text, integer, text"),
        ("create_hypothesis",
         "text, text, text[], text[], text, text, text, text, text, text, "
         "text[], text[], text, text[], text[], text, text[], text[], text, "
         "text, text, text"),
        ("link_hypothesis_alternative", "text, text, text, text, text, text, text"),
        ("link_contradiction", "text, text, text, text, text, text, text"),
        ("retract_hypothesis", "text, text, text, text, text"),
        ("hypothesis_health", "text"),
        ("current_alternative_state", "text"),
        ("unknown_boundary_state", "text"),
        ("contradiction_boundary_state", "text"),
    ]
    for fn, args in fns:
        op.execute(f"REVOKE ALL ON FUNCTION argus_private.{fn}({args}) FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION argus_private.{fn}({args}) TO argus_app")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_test_admin') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE
                    ON public.hypotheses, public.hypothesis_groundings,
                       public.hypothesis_alternatives, public.contradiction_links
                    TO argus_test_admin;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for stmt in [
        "DROP FUNCTION IF EXISTS argus_private.contradiction_boundary_state(text)",
        "DROP FUNCTION IF EXISTS argus_private.unknown_boundary_state(text)",
        "DROP FUNCTION IF EXISTS argus_private.current_alternative_state(text)",
        "DROP FUNCTION IF EXISTS argus_private.hypothesis_health(text)",
        "DROP FUNCTION IF EXISTS argus_private.retract_hypothesis(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.create_hypothesis(text, text, text[], text[], text, text, text, text, text, text, text[], text[], text, text[], text[], text, text[], text[], text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.link_contradiction(text, text, text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.link_hypothesis_alternative(text, text, text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.validate_hypothesis(text, text[], text[], text, text, text, text, text, text, text, integer, text, integer, text, integer, text)",
        "DROP FUNCTION IF EXISTS argus_private.hypothesis_fingerprint_v1(text)",
        "DROP FUNCTION IF EXISTS argus_private.interpretation_state_v2(text)",
    ]:
        op.execute(stmt)
    op.drop_table("contradiction_links")
    op.drop_table("hypothesis_alternatives")
    op.drop_table("hypothesis_groundings")
    op.drop_table("hypotheses")
    op.drop_constraint("ck_unk_link_target", "unknown_links", type_="check")
    op.create_check_constraint(
        "ck_unk_link_target",
        "unknown_links",
        "target_type IN ('Observation','Interpretation','EvidenceArtifact')",
    )
