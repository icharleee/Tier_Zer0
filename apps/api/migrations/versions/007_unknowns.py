"""007 — Unknowns and evidentiary limits (Slice 2B, ADR-0024/0025).

Negative knowledge as deliberate epistemic objects. Operational state
(OPEN/UNDER_REVIEW) is a CT column moved only by named functions; epistemic
disposition is DERIVED from unknown_resolutions (no column exists to flip).
Resolving alters no linked record — knowledge changes, the system does not.

Also replaces validate_interpretation/create_interpretation with the
accumulated ONT-PRN-019 obligation: UNRESOLVED uncertainty must name a valid
same-case Unknown. Nothing inherited is weakened; one obligation is added.

Revision ID: 007_unknowns
Revises: 006_interpretations
"""

from alembic import op
import sqlalchemy as sa

revision = "007_unknowns"
down_revision = "006_interpretations"
branch_labels = None
depends_on = None

DEFINER = "LANGUAGE plpgsql SECURITY DEFINER SET search_path = argus_private, pg_catalog, pg_temp"
INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.create_table(
        "unknowns",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("citation", sa.String(16), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("impact_statement", sa.Text, nullable=True),
        sa.Column("operational_state", sa.String(16), nullable=False),
        sa.Column("created_by_class", sa.String(16), nullable=False),
        sa.Column("created_by_id", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "citation", name="uq_unk_citation"),
        sa.CheckConstraint(
            "operational_state IN ('OPEN','UNDER_REVIEW')", name="ck_unk_op_state"
        ),
        sa.CheckConstraint("length(trim(question)) > 0", name="ck_unk_question"),
    )
    op.create_table(
        "unknown_links",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("unknown_id", sa.String(32), sa.ForeignKey("unknowns.id"), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(32), nullable=False),
        sa.Column("nature", sa.Text, nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.CheckConstraint(
            "target_type IN ('Observation','Interpretation','EvidenceArtifact')",
            name="ck_unk_link_target",
        ),
    )
    op.create_table(
        "unknown_resolutions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("unknown_id", sa.String(32), sa.ForeignKey("unknowns.id"), nullable=False),
        sa.Column("resolution_type", sa.String(24), nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("answering_claims", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("resolved_by", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("unknown_id", name="uq_unk_resolution"),
        sa.CheckConstraint(
            "resolution_type IN ('ANSWERED','PARTIALLY_ANSWERED','UNRESOLVABLE','WITHDRAWN')",
            name="ck_unk_res_type",
        ),
        sa.CheckConstraint("length(trim(rationale)) > 0", name="ck_unk_rationale"),
    )
    for t in ("unknowns", "unknown_links", "unknown_resolutions"):
        op.execute(f"GRANT SELECT ON public.{t} TO argus_app")

    op.execute(
        """
        CREATE FUNCTION argus_private.validate_unknown(
            p_question text, p_actor_class text
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_codes text[] := ARRAY[]::text[];
            v_q text := trim(coalesce(p_question, ''));
            v_low text := lower(trim(coalesce(p_question, '')));
        BEGIN
            IF v_q = '' THEN
                v_codes := v_codes || 'ONT-UNK-001:question-required'::text;
            ELSE
                IF right(v_q, 1) <> '?' THEN
                    v_codes := v_codes || 'ONT-UNK-001:not-a-question'::text;
                END IF;
                IF v_low LIKE '%todo%' OR v_low LIKE '%follow up%'
                   OR v_low LIKE '%assign%' OR v_low LIKE '%remind%'
                   OR v_low LIKE '%need to%'
                   OR v_low LIKE 'interview %' OR v_low LIKE 'collect %'
                   OR v_low LIKE 'obtain %' OR v_low LIKE 'request %' THEN
                    v_codes := v_codes || 'ONT-UNK-001:task-shaped-not-question'::text;
                END IF;
            END IF;
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                v_codes := v_codes || 'ONT-UNK-001:unsupported-actor'::text;
            END IF;
            RETURN ARRAY(SELECT DISTINCT c FROM unnest(v_codes) AS c ORDER BY c);
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.unknown_status(p_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v_res text; v_op text;
        BEGIN
            SELECT resolution_type INTO v_res
              FROM public.unknown_resolutions WHERE unknown_id = p_id;
            IF FOUND THEN RETURN v_res; END IF;
            SELECT operational_state INTO v_op FROM public.unknowns WHERE id = p_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'ONT-UNK-001: unknown record %', p_id; END IF;
            RETURN v_op;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.create_unknown(
            p_id text, p_case_id text, p_question text, p_impact text,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_codes text[]; v_n integer; v_citation text;
        BEGIN
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = p_case_id FOR UPDATE;
            v_codes := argus_private.validate_unknown(p_question, p_actor_class);
            IF cardinality(v_codes) > 0 THEN
                RAISE EXCEPTION 'ONT-UNK-001: inadmissible: %', array_to_string(v_codes, ', ');
            END IF;
            SELECT count(*) + 1 INTO v_n FROM public.unknowns WHERE case_id = p_case_id;
            v_citation := 'UNK-' || lpad(v_n::text, 6, '0');
            INSERT INTO public.unknowns
                (id, case_id, citation, question, impact_statement,
                 operational_state, created_by_class, created_by_id, created_at)
            VALUES (p_id, p_case_id, v_citation, p_question, p_impact, 'OPEN',
                    p_actor_class, p_actor_id, clock_timestamp());
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), p_case_id,
                p_actor_class, p_actor_id, p_ai_ver, 'unknown-created',
                'Unknown', p_id, 'SUCCEEDED',
                jsonb_build_object('citation', v_citation));
            RETURN p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.link_unknown(
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
        CREATE FUNCTION argus_private.set_unknown_review(
            p_id text, p_under_review boolean,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS void
        """ + DEFINER + """
        AS $$
        DECLARE v_case text; v_state text;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-PRN-007: review marking is human-only';
            END IF;
            SELECT case_id, operational_state INTO v_case, v_state
              FROM public.unknowns WHERE id = p_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'ONT-UNK-001: unknown record %', p_id; END IF;
            IF EXISTS (SELECT 1 FROM public.unknown_resolutions WHERE unknown_id = p_id) THEN
                RAISE EXCEPTION 'ONT-PRN-012: disposition is terminal; no operational transitions after resolution';
            END IF;
            IF (p_under_review AND v_state = 'UNDER_REVIEW')
               OR (NOT p_under_review AND v_state = 'OPEN') THEN
                RAISE EXCEPTION 'ONT-PRN-012: no such transition (already %)', v_state;
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            UPDATE public.unknowns
               SET operational_state = CASE WHEN p_under_review THEN 'UNDER_REVIEW' ELSE 'OPEN' END
             WHERE id = p_id;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver,
                CASE WHEN p_under_review THEN 'unknown-review-started'
                     ELSE 'unknown-review-paused' END,
                'Unknown', p_id, 'SUCCEEDED', NULL);
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.resolve_unknown(
            p_res_id text, p_unknown_id text, p_type text, p_rationale text,
            p_claims text[], p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_case text; v_cid text; v_found boolean;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-UNR-001: inadmissible: ONT-PRN-007:actor-not-permitted';
            END IF;
            IF p_rationale IS NULL OR length(trim(p_rationale)) = 0 THEN
                RAISE EXCEPTION 'ONT-UNR-001: inadmissible: ONT-UNR-001:rationale-required';
            END IF;
            IF p_type NOT IN ('ANSWERED','PARTIALLY_ANSWERED','UNRESOLVABLE','WITHDRAWN') THEN
                RAISE EXCEPTION 'ONT-UNR-001: invalid resolution type %', p_type;
            END IF;
            SELECT case_id INTO v_case FROM public.unknowns WHERE id = p_unknown_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'ONT-UNK-001: unknown record %', p_unknown_id; END IF;
            IF EXISTS (SELECT 1 FROM public.unknown_resolutions WHERE unknown_id = p_unknown_id) THEN
                RAISE EXCEPTION 'ONT-PRN-012: disposition is terminal; already resolved';
            END IF;
            IF p_type IN ('ANSWERED','PARTIALLY_ANSWERED') THEN
                IF p_claims IS NULL OR cardinality(p_claims) = 0 THEN
                    RAISE EXCEPTION 'ONT-UNR-001: inadmissible: ONT-UNR-001:answer-requires-evidence';
                END IF;
                FOREACH v_cid IN ARRAY p_claims LOOP
                    SELECT true INTO v_found FROM public.observations
                     WHERE id = v_cid AND case_id = v_case;
                    IF NOT FOUND THEN
                        SELECT true INTO v_found FROM public.interpretations
                         WHERE id = v_cid AND case_id = v_case;
                    END IF;
                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'ONT-UNR-001: inadmissible: ONT-UNR-001:answer-requires-evidence';
                    END IF;
                END LOOP;
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            INSERT INTO public.unknown_resolutions
                (id, unknown_id, resolution_type, rationale, answering_claims,
                 resolved_by, created_at)
            VALUES (p_res_id, p_unknown_id, p_type, p_rationale,
                    CASE WHEN p_claims IS NULL THEN NULL ELSE to_jsonb(p_claims) END,
                    p_actor_id, clock_timestamp());
            -- Deliberately: NO update to any other record. Knowledge changes;
            -- the system does not (ONT-PRN-020 / H5).
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver,
                CASE p_type WHEN 'ANSWERED' THEN 'unknown-resolved'
                            WHEN 'PARTIALLY_ANSWERED' THEN 'unknown-partially-resolved'
                            WHEN 'WITHDRAWN' THEN 'unknown-withdrawn'
                            ELSE 'unknown-marked-unresolvable' END,
                'UnknownResolution', p_res_id, 'SUCCEEDED',
                jsonb_build_object('unknown_id', p_unknown_id, 'type', p_type));
            RETURN p_res_id;
        END $$;
        """
    )

    # ---- Accumulated obligation (ONT-PRN-019): replace the Interpretation
    # validator/creator with the UNRESOLVED-names-its-Unknown rule ----
    op.execute("DROP FUNCTION argus_private.create_interpretation(text, text, text[], text[], text, text, text, text, text, text, text)")
    op.execute("DROP FUNCTION argus_private.validate_interpretation(text, text[], text, text, text, text, text, text[])")
    op.execute(
        """
        CREATE FUNCTION argus_private.validate_interpretation(
            p_case_id text, p_observation_ids text[], p_meaning text,
            p_reasoning text, p_unc_status text, p_unc_expl text,
            p_actor_class text, p_roles text[], p_unresolved_unknown_id text
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_codes text[] := ARRAY[]::text[];
            v_prose text; v_term text; i integer; v_oid text;
            v_retracted timestamptz; v_ocase text;
        BEGIN
            IF p_meaning IS NULL OR length(trim(p_meaning)) = 0 THEN
                v_codes := v_codes || 'ONT-INT-001:meaning-required'::text;
            END IF;
            IF p_reasoning IS NULL OR length(trim(p_reasoning)) = 0 THEN
                v_codes := v_codes || 'ONT-INT-001:reasoning-required'::text;
            END IF;
            IF p_unc_status IS NULL OR p_unc_status NOT IN
               ('ACKNOWLEDGED','MATERIAL','LIMITING','UNRESOLVED') THEN
                v_codes := v_codes || 'ONT-INT-001:uncertainty-status-required'::text;
            END IF;
            IF p_unc_expl IS NULL OR length(trim(p_unc_expl)) = 0 THEN
                v_codes := v_codes || 'ONT-INT-001:uncertainty-explanation-required'::text;
            END IF;
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                v_codes := v_codes || 'ONT-INT-001:unsupported-actor'::text;
            END IF;
            v_prose := lower(coalesce(p_meaning, '') || ' ' || coalesce(p_reasoning, ''));
            FOREACH v_term IN ARRAY ARRAY[
                'more likely','most likely','more probable','most probable',
                'stronger','strongest','weaker','preferred',
                'primary explanation','best explanation']
            LOOP
                IF position(v_term IN v_prose) > 0 THEN
                    v_codes := v_codes || 'ONT-INT-001:comparative-ranking-not-yet-modeled'::text;
                    EXIT;
                END IF;
            END LOOP;
            -- Accumulated (ONT-PRN-019): UNRESOLVED names its Unknown.
            IF p_unc_status = 'UNRESOLVED' AND (
                p_unresolved_unknown_id IS NULL OR NOT EXISTS (
                    SELECT 1 FROM public.unknowns
                     WHERE id = p_unresolved_unknown_id AND case_id = p_case_id)
            ) THEN
                v_codes := v_codes || 'ONT-INT-001:unresolved-requires-named-unknown'::text;
            END IF;
            IF p_observation_ids IS NULL OR cardinality(p_observation_ids) = 0 THEN
                v_codes := v_codes || 'ONT-INT-001:no-grounded-observations'::text;
            ELSE
                FOR i IN 1 .. cardinality(p_observation_ids) LOOP
                    v_oid := p_observation_ids[i];
                    IF p_roles IS NULL OR cardinality(p_roles) < i OR
                       p_roles[i] NOT IN ('SUPPORTING','LIMITING','CONTEXTUAL') THEN
                        v_codes := v_codes || 'ONT-INT-001:invalid-grounding-role'::text;
                    END IF;
                    SELECT o.retracted_at, o.case_id INTO v_retracted, v_ocase
                      FROM public.observations o WHERE o.id = v_oid;
                    IF NOT FOUND THEN
                        v_codes := v_codes || 'ONT-INT-001:unknown-observation'::text;
                        CONTINUE;
                    END IF;
                    IF v_retracted IS NOT NULL THEN
                        v_codes := v_codes || 'ONT-INT-001:observation-retracted'::text;
                        CONTINUE;
                    END IF;
                    IF v_ocase IS DISTINCT FROM p_case_id THEN
                        v_codes := v_codes || 'ONT-INT-001:cross-case-grounding'::text;
                        CONTINUE;
                    END IF;
                    IF NOT argus_private.is_observation_grounded(v_oid) THEN
                        v_codes := v_codes || 'ONT-INT-001:observation-ungrounded'::text;
                    END IF;
                END LOOP;
            END IF;
            RETURN ARRAY(SELECT DISTINCT c FROM unnest(v_codes) AS c ORDER BY c);
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.create_interpretation(
            p_id text, p_case_id text, p_observation_ids text[], p_roles text[],
            p_meaning text, p_reasoning text, p_unc_status text, p_unc_expl text,
            p_actor_class text, p_actor_id text, p_ai_ver text,
            p_unresolved_unknown_id text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE
            v_codes text[]; v_citation text; v_n integer; i integer;
        BEGIN
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = p_case_id FOR UPDATE;
            v_codes := argus_private.validate_interpretation(
                p_case_id, p_observation_ids, p_meaning, p_reasoning,
                p_unc_status, p_unc_expl, p_actor_class, p_roles,
                p_unresolved_unknown_id);
            IF cardinality(v_codes) > 0 THEN
                RAISE EXCEPTION 'ONT-INT-001: inadmissible: %', array_to_string(v_codes, ', ');
            END IF;
            SELECT count(*) + 1 INTO v_n FROM public.interpretations WHERE case_id = p_case_id;
            v_citation := 'INT-' || lpad(v_n::text, 6, '0');
            INSERT INTO public.interpretations
                (id, case_id, citation, meaning_statement, reasoning_description,
                 uncertainty_status, uncertainty_explanation, created_by_class,
                 created_by_id, created_at)
            VALUES (p_id, p_case_id, v_citation, p_meaning, p_reasoning,
                    p_unc_status, p_unc_expl, p_actor_class, p_actor_id,
                    clock_timestamp());
            FOR i IN 1 .. cardinality(p_observation_ids) LOOP
                INSERT INTO public.interpretation_groundings
                    (id, interpretation_id, observation_id, statement_fingerprint,
                     grounding_role, linked_at)
                SELECT replace(gen_random_uuid()::text, '-', ''), p_id, o.id,
                       encode(sha256(convert_to(o.statement, 'UTF8')), 'hex'),
                       p_roles[i], clock_timestamp()
                  FROM public.observations o WHERE o.id = p_observation_ids[i];
            END LOOP;
            -- UNRESOLVED names its boundary: the link is a validity
            -- relationship (ONT-PRN-021), created with the interpretation.
            IF p_unresolved_unknown_id IS NOT NULL THEN
                INSERT INTO public.unknown_links
                    (id, unknown_id, target_type, target_id, nature, linked_at)
                VALUES (replace(gen_random_uuid()::text, '-', ''),
                        p_unresolved_unknown_id, 'Interpretation', p_id,
                        'Named evidentiary limit for UNRESOLVED uncertainty (Article IX)',
                        clock_timestamp());
            END IF;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), p_case_id,
                p_actor_class, p_actor_id, p_ai_ver, 'claim-created',
                'Interpretation', p_id, 'SUCCEEDED',
                jsonb_build_object('citation', v_citation,
                                   'observations', to_jsonb(p_observation_ids),
                                   'uncertainty_status', p_unc_status,
                                   'unresolved_unknown', p_unresolved_unknown_id));
            RETURN p_id;
        END $$;
        """
    )

    fns = [
        ("validate_unknown", "text, text"),
        ("unknown_status", "text"),
        ("create_unknown", "text, text, text, text, text, text, text"),
        ("link_unknown", "text, text, text, text, text, text, text, text"),
        ("set_unknown_review", "text, boolean, text, text, text"),
        ("resolve_unknown", "text, text, text, text, text[], text, text, text"),
        ("validate_interpretation", "text, text[], text, text, text, text, text, text[], text"),
        ("create_interpretation", "text, text, text[], text[], text, text, text, text, text, text, text, text"),
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
                    ON public.unknowns, public.unknown_links, public.unknown_resolutions
                    TO argus_test_admin;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    raise NotImplementedError(
        "007 replaces interpretation function signatures; downgrade requires "
        "restoring 006's definitions — perform via explicit migration review."
    )
