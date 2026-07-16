"""008 — Contradictions as boundary objects (Slice 2C, ADR-0027).

Joint incompatibility becomes representable: these admissible claims cannot
all fit the same reality under the stated scope. The decisive rule, enforced
here: a Contradiction may state that claims cannot all be true; it may never
decide which claim reality favors. No survivor surface exists; disposition
(ONT-CDP-001) is human-only, terminal, non-adjudicating, and alters no member.

Revision ID: 008_contradictions
Revises: 007_unknowns
"""

from alembic import op
import sqlalchemy as sa

revision = "008_contradictions"
down_revision = "007_unknowns"
branch_labels = None
depends_on = None

DEFINER = "LANGUAGE plpgsql SECURITY DEFINER SET search_path = argus_private, pg_catalog, pg_temp"
INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.create_table(
        "contradictions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("citation", sa.String(16), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("contradiction_type", sa.String(16), nullable=False),
        sa.Column("scope_definition", sa.Text, nullable=False),
        sa.Column("incompatibility_basis", sa.Text, nullable=False),
        sa.Column("operational_state", sa.String(16), nullable=False),
        sa.Column("created_by_class", sa.String(16), nullable=False),
        sa.Column("created_by_id", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "citation", name="uq_con_citation"),
        sa.CheckConstraint(
            "contradiction_type IN ('TEMPORAL','SPATIAL','IDENTITY','CAUSAL','DESCRIPTIVE','NUMERIC','PROCEDURAL','PROVENANCE','CUSTODY','LOGICAL')",
            name="ck_con_type",
        ),
        sa.CheckConstraint("operational_state IN ('OPEN','UNDER_REVIEW')", name="ck_con_op_state"),
        sa.CheckConstraint("length(trim(scope_definition)) > 0", name="ck_con_scope"),
        sa.CheckConstraint("length(trim(incompatibility_basis)) > 0", name="ck_con_basis"),
    )
    op.create_table(
        "contradiction_members",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("contradiction_id", sa.String(32), sa.ForeignKey("contradictions.id"), nullable=False),
        sa.Column("member_type", sa.String(32), nullable=False),
        sa.Column("member_id", sa.String(32), nullable=False),
        sa.Column("member_fingerprint", sa.String(64), nullable=False),
        sa.Column("member_role", sa.String(24), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("contradiction_id", "member_id", name="uq_con_member"),
        sa.CheckConstraint("member_role = 'INCOMPATIBLE_CLAIM'", name="ck_member_role"),
        sa.CheckConstraint("member_type IN ('Observation','Interpretation')", name="ck_member_type"),
    )
    op.create_table(
        "contradiction_dispositions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("contradiction_id", sa.String(32), sa.ForeignKey("contradictions.id"), nullable=False),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("informing_refs", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("disposed_by", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("contradiction_id", name="uq_con_disposition"),
        sa.CheckConstraint(
            "outcome IN ('EXPLAINED','NO_LONGER_APPLICABLE','WITHDRAWN','UNRESOLVED','SUPERSEDED')",
            name="ck_disposition_outcome",
        ),
        sa.CheckConstraint("length(trim(rationale)) > 0", name="ck_disposition_rationale"),
    )
    for t in ("contradictions", "contradiction_members", "contradiction_dispositions"):
        op.execute(f"GRANT SELECT ON public.{t} TO argus_app")

    op.execute(
        """
        CREATE FUNCTION argus_private.member_case_and_state(
            p_type text, p_id text,
            OUT o_case text, OUT o_retracted timestamptz, OUT o_fingerprint text
        )
        """ + INVOKER + """
        AS $$
        BEGIN
            IF p_type = 'Observation' THEN
                SELECT case_id, retracted_at,
                       encode(sha256(convert_to(statement, 'UTF8')), 'hex')
                  INTO o_case, o_retracted, o_fingerprint
                  FROM public.observations WHERE id = p_id;
            ELSIF p_type = 'Interpretation' THEN
                SELECT case_id, retracted_at,
                       encode(sha256(convert_to(meaning_statement, 'UTF8')), 'hex')
                  INTO o_case, o_retracted, o_fingerprint
                  FROM public.interpretations WHERE id = p_id;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.validate_contradiction(
            p_case_id text, p_member_types text[], p_member_ids text[],
            p_description text, p_type text, p_scope text, p_basis text,
            p_actor_class text, p_roles text[]
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_codes text[] := ARRAY[]::text[];
            v_prose text; v_term text; i integer;
            v_m record; v_distinct integer;
        BEGIN
            IF p_description IS NULL OR length(trim(p_description)) = 0 THEN
                v_codes := v_codes || 'ONT-CON-001:description-required'::text;
            END IF;
            IF p_type IS NULL OR p_type NOT IN
               ('TEMPORAL','SPATIAL','IDENTITY','CAUSAL','DESCRIPTIVE',
                'NUMERIC','PROCEDURAL','PROVENANCE','CUSTODY','LOGICAL') THEN
                v_codes := v_codes || 'ONT-CON-001:type-required'::text;
            END IF;
            IF p_scope IS NULL OR length(trim(p_scope)) = 0 THEN
                v_codes := v_codes || 'ONT-CON-001:scope-required'::text;
            END IF;
            IF p_basis IS NULL OR length(trim(p_basis)) = 0 THEN
                v_codes := v_codes || 'ONT-CON-001:basis-required'::text;
            END IF;
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                v_codes := v_codes || 'ONT-CON-001:unsupported-actor'::text;
            END IF;
            v_prose := lower(coalesce(p_description, '') || ' ' || coalesce(p_basis, ''));
            FOREACH v_term IN ARRAY ARRAY[
                'is wrong','is false','refuted','prevails','is correct',
                'should be preferred','winner']
            LOOP
                IF position(v_term IN v_prose) > 0 THEN
                    v_codes := v_codes || 'ONT-CON-001:adjudicative-language'::text;
                    EXIT;
                END IF;
            END LOOP;
            SELECT count(DISTINCT p_member_types[j] || ':' || p_member_ids[j])
              INTO v_distinct
              FROM generate_subscripts(coalesce(p_member_ids, ARRAY[]::text[]), 1) AS j;
            IF v_distinct < 2 THEN
                v_codes := v_codes || 'ONT-CON-001:insufficient-members'::text;
            END IF;
            IF v_distinct < coalesce(cardinality(p_member_ids), 0) THEN
                v_codes := v_codes || 'ONT-CON-001:duplicate-members'::text;
            END IF;
            FOR i IN 1 .. coalesce(cardinality(p_member_ids), 0) LOOP
                IF p_roles IS NULL OR cardinality(p_roles) < i
                   OR p_roles[i] IS DISTINCT FROM 'INCOMPATIBLE_CLAIM' THEN
                    v_codes := v_codes || 'ONT-CNM-001:invalid-member-role'::text;
                END IF;
                SELECT * INTO v_m FROM argus_private.member_case_and_state(
                    p_member_types[i], p_member_ids[i]);
                IF v_m.o_case IS NULL THEN
                    v_codes := v_codes || 'ONT-CNM-001:unknown-member'::text;
                    CONTINUE;
                END IF;
                IF v_m.o_retracted IS NOT NULL THEN
                    v_codes := v_codes || 'ONT-CNM-001:member-retracted'::text;
                END IF;
                IF v_m.o_case IS DISTINCT FROM p_case_id THEN
                    v_codes := v_codes || 'ONT-CNM-001:cross-case-member'::text;
                END IF;
            END LOOP;
            RETURN ARRAY(SELECT DISTINCT c FROM unnest(v_codes) AS c ORDER BY c);
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.create_contradiction(
            p_id text, p_case_id text, p_member_types text[], p_member_ids text[],
            p_roles text[], p_description text, p_type text, p_scope text,
            p_basis text, p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_codes text[]; v_n integer; v_citation text; i integer; v_m record;
        BEGIN
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = p_case_id FOR UPDATE;
            v_codes := argus_private.validate_contradiction(
                p_case_id, p_member_types, p_member_ids, p_description,
                p_type, p_scope, p_basis, p_actor_class, p_roles);
            IF cardinality(v_codes) > 0 THEN
                RAISE EXCEPTION 'ONT-CON-001: inadmissible: %', array_to_string(v_codes, ', ');
            END IF;
            SELECT count(*) + 1 INTO v_n FROM public.contradictions WHERE case_id = p_case_id;
            v_citation := 'CON-' || lpad(v_n::text, 6, '0');
            INSERT INTO public.contradictions
                (id, case_id, citation, description, contradiction_type,
                 scope_definition, incompatibility_basis, operational_state,
                 created_by_class, created_by_id, created_at)
            VALUES (p_id, p_case_id, v_citation, p_description, p_type, p_scope,
                    p_basis, 'OPEN', p_actor_class, p_actor_id, clock_timestamp());
            FOR i IN 1 .. cardinality(p_member_ids) LOOP
                SELECT * INTO v_m FROM argus_private.member_case_and_state(
                    p_member_types[i], p_member_ids[i]);
                INSERT INTO public.contradiction_members
                    (id, contradiction_id, member_type, member_id,
                     member_fingerprint, member_role, linked_at)
                VALUES (replace(gen_random_uuid()::text, '-', ''), p_id,
                        p_member_types[i], p_member_ids[i], v_m.o_fingerprint,
                        'INCOMPATIBLE_CLAIM', clock_timestamp());
            END LOOP;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), p_case_id,
                p_actor_class, p_actor_id, p_ai_ver, 'contradiction-created',
                'Contradiction', p_id, 'SUCCEEDED',
                jsonb_build_object('citation', v_citation, 'type', p_type,
                                   'members', to_jsonb(p_member_ids)));
            RETURN p_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.set_contradiction_review(
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
              FROM public.contradictions WHERE id = p_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'ONT-CON-001: unknown record %', p_id; END IF;
            IF EXISTS (SELECT 1 FROM public.contradiction_dispositions WHERE contradiction_id = p_id) THEN
                RAISE EXCEPTION 'ONT-PRN-012: disposition is terminal; no operational transitions after disposition';
            END IF;
            IF (p_under_review AND v_state = 'UNDER_REVIEW')
               OR (NOT p_under_review AND v_state = 'OPEN') THEN
                RAISE EXCEPTION 'ONT-PRN-012: no such transition (already %)', v_state;
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            UPDATE public.contradictions
               SET operational_state = CASE WHEN p_under_review THEN 'UNDER_REVIEW' ELSE 'OPEN' END
             WHERE id = p_id;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver,
                CASE WHEN p_under_review THEN 'contradiction-review-started'
                     ELSE 'contradiction-review-paused' END,
                'Contradiction', p_id, 'SUCCEEDED', NULL);
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.dispose_contradiction(
            p_disp_id text, p_con_id text, p_outcome text, p_rationale text,
            p_informing text[], p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE v_case text;
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-CDP-001: inadmissible: ONT-PRN-007:actor-not-permitted';
            END IF;
            IF p_outcome NOT IN ('EXPLAINED','NO_LONGER_APPLICABLE','WITHDRAWN','UNRESOLVED','SUPERSEDED') THEN
                RAISE EXCEPTION 'ONT-CDP-001: inadmissible: ONT-CDP-001:outcome-required';
            END IF;
            IF p_rationale IS NULL OR length(trim(p_rationale)) = 0 THEN
                RAISE EXCEPTION 'ONT-CDP-001: inadmissible: ONT-CDP-001:rationale-required';
            END IF;
            SELECT case_id INTO v_case FROM public.contradictions WHERE id = p_con_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'ONT-CON-001: unknown record %', p_con_id; END IF;
            IF EXISTS (SELECT 1 FROM public.contradiction_dispositions WHERE contradiction_id = p_con_id) THEN
                RAISE EXCEPTION 'ONT-PRN-012: disposition is terminal; already disposed';
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            INSERT INTO public.contradiction_dispositions
                (id, contradiction_id, outcome, rationale, informing_refs,
                 disposed_by, created_at)
            VALUES (p_disp_id, p_con_id, p_outcome, p_rationale,
                    CASE WHEN p_informing IS NULL THEN NULL ELSE to_jsonb(p_informing) END,
                    p_actor_id, clock_timestamp());
            -- Deliberately: no member, contradiction, or claim is altered.
            -- A disposition explains how humans disposed of the conflict —
            -- never which claim reality favors (ADR-0027).
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case,
                p_actor_class, p_actor_id, p_ai_ver, 'contradiction-disposed',
                'ContradictionDisposition', p_disp_id, 'SUCCEEDED',
                jsonb_build_object('contradiction_id', p_con_id, 'outcome', p_outcome));
            RETURN p_disp_id;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.contradiction_health(p_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE v_bad integer;
        BEGIN
            SELECT count(*) INTO v_bad
              FROM public.contradiction_members m
              LEFT JOIN public.observations o
                     ON m.member_type = 'Observation' AND o.id = m.member_id
              LEFT JOIN public.interpretations i
                     ON m.member_type = 'Interpretation' AND i.id = m.member_id
             WHERE m.contradiction_id = p_id
               AND (COALESCE(o.id, i.id) IS NULL
                    OR o.retracted_at IS NOT NULL
                    OR i.retracted_at IS NOT NULL);
            RETURN CASE WHEN v_bad = 0 THEN 'CURRENT' ELSE 'DEGRADED' END;
        END $$;
        """
    )

    fns = [
        ("member_case_and_state", "text, text"),
        ("validate_contradiction", "text, text[], text[], text, text, text, text, text, text[]"),
        ("create_contradiction", "text, text, text[], text[], text[], text, text, text, text, text, text, text"),
        ("set_contradiction_review", "text, boolean, text, text, text"),
        ("dispose_contradiction", "text, text, text, text, text[], text, text, text"),
        ("contradiction_health", "text"),
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
                    ON public.contradictions, public.contradiction_members,
                       public.contradiction_dispositions
                    TO argus_test_admin;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for stmt in [
        "DROP FUNCTION IF EXISTS argus_private.contradiction_health(text)",
        "DROP FUNCTION IF EXISTS argus_private.dispose_contradiction(text, text, text, text, text[], text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.set_contradiction_review(text, boolean, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.create_contradiction(text, text, text[], text[], text[], text, text, text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.validate_contradiction(text, text[], text[], text, text, text, text, text, text[])",
        "DROP FUNCTION IF EXISTS argus_private.member_case_and_state(text, text)",
    ]:
        op.execute(stmt)
    op.drop_table("contradiction_dispositions")
    op.drop_table("contradiction_members")
    op.drop_table("contradictions")
