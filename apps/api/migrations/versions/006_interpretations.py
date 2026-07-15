"""006 — Interpretation: competing meanings without preference (Slice 2A).

Rung two of the ladder. The application role has SELECT only; creation and
retraction exist solely as controlled functions. validate_interpretation is
the independent PostgreSQL rendering of the canonical refusal matrix
(CONSTITUTIONAL_PREDICATES.md 0.3.0) — ODE H4's database leg. No
epistemic-ranking column, constraint, or default ordering exists anywhere in
this migration; citation order is technical and non-evidentiary.

Revision ID: 006_interpretations
Revises: 005_observations
"""

from alembic import op
import sqlalchemy as sa

revision = "006_interpretations"
down_revision = "005_observations"
branch_labels = None
depends_on = None

DEFINER = "LANGUAGE plpgsql SECURITY DEFINER SET search_path = argus_private, pg_catalog, pg_temp"
INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.create_table(
        "interpretations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("citation", sa.String(16), nullable=False),
        sa.Column("meaning_statement", sa.Text, nullable=False),
        sa.Column("reasoning_description", sa.Text, nullable=False),
        sa.Column("uncertainty_status", sa.String(16), nullable=False),
        sa.Column("uncertainty_explanation", sa.Text, nullable=False),
        sa.Column("created_by_class", sa.String(16), nullable=False),
        sa.Column("created_by_id", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.UniqueConstraint("case_id", "citation", name="uq_int_citation"),
        # The structured uncertainty envelope, backed at the persistence
        # boundary (Amendment 2; deliberately no 'certain' status).
        sa.CheckConstraint(
            "uncertainty_status IN ('ACKNOWLEDGED','MATERIAL','LIMITING','UNRESOLVED')",
            name="ck_int_uncertainty_status",
        ),
        sa.CheckConstraint("length(trim(meaning_statement)) > 0", name="ck_int_meaning"),
        sa.CheckConstraint("length(trim(reasoning_description)) > 0", name="ck_int_reasoning"),
        sa.CheckConstraint(
            "length(trim(uncertainty_explanation)) > 0", name="ck_int_uncertainty_expl"
        ),
    )
    op.create_table(
        "interpretation_groundings",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("interpretation_id", sa.String(32), sa.ForeignKey("interpretations.id"), nullable=False),
        sa.Column("observation_id", sa.String(32), sa.ForeignKey("observations.id"), nullable=False),
        sa.Column("statement_fingerprint", sa.String(64), nullable=False),
        sa.Column("grounding_role", sa.String(16), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("interpretation_id", "observation_id", name="uq_int_grounding"),
        sa.CheckConstraint(
            "grounding_role IN ('SUPPORTING','LIMITING','CONTEXTUAL')",
            name="ck_grounding_role",
        ),
    )
    op.execute("GRANT SELECT ON public.interpretations TO argus_app")
    op.execute("GRANT SELECT ON public.interpretation_groundings TO argus_app")

    op.execute(
        """
        CREATE FUNCTION argus_private.validate_interpretation(
            p_case_id text, p_observation_ids text[], p_meaning text,
            p_reasoning text, p_unc_status text, p_unc_expl text,
            p_actor_class text, p_roles text[]
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_codes text[] := ARRAY[]::text[];
            v_prose text;
            v_term text;
            i integer;
            v_oid text;
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

            -- Conservative lexical guard (Amendment 1): heuristic tripwire.
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
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE
            v_codes text[]; v_citation text; v_n integer; i integer;
        BEGIN
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = p_case_id FOR UPDATE;
            v_codes := argus_private.validate_interpretation(
                p_case_id, p_observation_ids, p_meaning, p_reasoning,
                p_unc_status, p_unc_expl, p_actor_class, p_roles);
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
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), p_case_id,
                p_actor_class, p_actor_id, p_ai_ver, 'claim-created',
                'Interpretation', p_id, 'SUCCEEDED',
                jsonb_build_object('citation', v_citation,
                                   'observations', to_jsonb(p_observation_ids),
                                   'uncertainty_status', p_unc_status));
            RETURN p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.retract_interpretation(
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
              FROM public.interpretations WHERE id = p_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-PRN-006: unknown record %', p_id;
            END IF;
            IF v_retracted IS NOT NULL THEN
                RAISE EXCEPTION 'ONT-PRN-006: already retracted (retraction is terminal)';
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            UPDATE public.interpretations
               SET retracted_at = clock_timestamp(), retraction_reason = p_reason
             WHERE id = p_id;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver, 'claim-retracted',
                'Interpretation', p_id, 'SUCCEEDED',
                jsonb_build_object('reason', p_reason));
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.interpretation_grounding_health(p_int_id text)
        RETURNS text
        """ + INVOKER + """
        AS $$
        BEGIN
            RETURN CASE WHEN EXISTS (
                SELECT 1
                  FROM public.interpretation_groundings g
                  JOIN public.observations o ON o.id = g.observation_id
                 WHERE g.interpretation_id = p_int_id
                   AND o.retracted_at IS NULL
                   AND argus_private.is_observation_grounded(o.id))
            THEN 'GROUNDED' ELSE 'DEGRADED' END;
        END $$;
        """
    )

    fns = [
        ("validate_interpretation", "text, text[], text, text, text, text, text, text[]"),
        ("create_interpretation", "text, text, text[], text[], text, text, text, text, text, text, text"),
        ("retract_interpretation", "text, text, text, text, text"),
        ("interpretation_grounding_health", "text"),
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
                    ON public.interpretations, public.interpretation_groundings
                    TO argus_test_admin;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for stmt in [
        "DROP FUNCTION IF EXISTS argus_private.interpretation_grounding_health(text)",
        "DROP FUNCTION IF EXISTS argus_private.retract_interpretation(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.create_interpretation(text, text, text[], text[], text, text, text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.validate_interpretation(text, text[], text, text, text, text, text, text[])",
    ]:
        op.execute(stmt)
    op.drop_table("interpretation_groundings")
    op.drop_table("interpretations")
