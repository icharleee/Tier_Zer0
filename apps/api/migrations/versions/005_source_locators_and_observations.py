"""005 — SourceLocator and Observation (Slice 1D, ADR-0020).

The first epistemic object. Validation is distinct from persistence
(Amendment 2): validate_* functions return canonical admissibility codes
(the independent PostgreSQL rendering of the refusal matrix in
docs/domain/CONSTITUTIONAL_PREDICATES.md — ODE H3); create_* functions are
nearly mechanical and refuse on any code. The application role has SELECT
only on all three tables — creation and retraction exist solely as
controlled functions.

Revision ID: 005_observations
Revises: 004_predicates
"""

from alembic import op
import sqlalchemy as sa

revision = "005_observations"
down_revision = "004_predicates"
branch_labels = None
depends_on = None

DEFINER = "LANGUAGE plpgsql SECURITY DEFINER SET search_path = argus_private, pg_catalog, pg_temp"
INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.create_table(
        "source_locators",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("artifact_id", sa.String(32), sa.ForeignKey("evidence_artifacts.id"), nullable=False),
        sa.Column("scheme", sa.String(32), nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column("created_by_class", sa.String(16), nullable=False),
        sa.Column("created_by_id", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.CheckConstraint(
            "scheme IN ('byte-range','time-range','page-region')", name="ck_locator_scheme"
        ),
    )
    op.create_table(
        "observations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("citation", sa.String(16), nullable=False),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("method_description", sa.Text, nullable=False),
        sa.Column("event_time_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_time_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_class", sa.String(16), nullable=False),
        sa.Column("created_by_id", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.UniqueConstraint("case_id", "citation", name="uq_obs_citation"),
        # Perception only, at the persistence boundary (ONT-PRN-005).
        sa.CheckConstraint("length(trim(statement)) > 0", name="ck_obs_statement"),
        sa.CheckConstraint("length(trim(method_description)) > 0", name="ck_obs_method"),
    )
    op.create_table(
        "observation_groundings",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("observation_id", sa.String(32), sa.ForeignKey("observations.id"), nullable=False),
        sa.Column("locator_id", sa.String(32), sa.ForeignKey("source_locators.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("observation_id", "locator_id", name="uq_grounding"),
    )
    for table in ("source_locators", "observations", "observation_groundings"):
        op.execute(f"GRANT SELECT ON public.{table} TO argus_app")

    # ---- validators (INVOKER: pure reads; the H3 experimental surface) ----
    op.execute(
        """
        CREATE FUNCTION argus_private.validate_source_locator(
            p_artifact_id text, p_scheme text, p_payload jsonb
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_status text; v_size integer;
            v_codes text[] := ARRAY[]::text[];
            v_start jsonb; v_end jsonb;
        BEGIN
            SELECT status, size_bytes INTO v_status, v_size
              FROM public.evidence_artifacts WHERE id = p_artifact_id;
            IF NOT FOUND OR v_status <> 'ACTIVE' THEN
                v_codes := v_codes || 'ONT-SRC-001:artifact-not-active'::text;
            END IF;
            IF p_scheme NOT IN ('byte-range','time-range','page-region') THEN
                v_codes := v_codes || 'ONT-SRC-001:unknown-scheme'::text;
            ELSIF p_scheme = 'byte-range' THEN
                v_start := p_payload -> 'start';
                v_end := p_payload -> 'end';
                IF v_start IS NULL OR v_end IS NULL
                   OR jsonb_typeof(v_start) <> 'number' OR jsonb_typeof(v_end) <> 'number'
                   OR v_start::text ~ '[.eE]' OR v_end::text ~ '[.eE]'
                   OR NOT (0 <= (v_start::text)::bigint
                           AND (v_start::text)::bigint < (v_end::text)::bigint
                           AND (v_end::text)::bigint <= coalesce(v_size, -1)) THEN
                    v_codes := v_codes || 'ONT-SRC-001:out-of-bounds'::text;
                END IF;
            END IF;
            RETURN ARRAY(SELECT DISTINCT c FROM unnest(v_codes) AS c ORDER BY c);
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.validate_observation(
            p_case_id text, p_locator_ids text[], p_statement text,
            p_method text, p_actor_class text
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE
            v_codes text[] := ARRAY[]::text[];
            v_lid text;
            v_retracted timestamptz; v_lcase text; v_artifact text;
            v_found boolean;
            v_elig record;
        BEGIN
            IF p_statement IS NULL OR length(trim(p_statement)) = 0 THEN
                v_codes := v_codes || 'ONT-PRN-005:missing-statement'::text;
            END IF;
            IF p_method IS NULL OR length(trim(p_method)) = 0 THEN
                v_codes := v_codes || 'ONT-PRN-005:missing-method'::text;
            END IF;
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                v_codes := v_codes || 'ONT-PRN-007:actor-not-permitted'::text;
            END IF;
            IF p_locator_ids IS NULL OR cardinality(p_locator_ids) = 0 THEN
                v_codes := v_codes || 'ONT-PRN-004:no-grounding'::text;
            ELSE
                FOREACH v_lid IN ARRAY p_locator_ids LOOP
                    SELECT l.retracted_at, l.case_id, l.artifact_id, true
                      INTO v_retracted, v_lcase, v_artifact, v_found
                      FROM public.source_locators l WHERE l.id = v_lid;
                    IF NOT FOUND THEN
                        v_codes := v_codes || 'ONT-SRC-001:unknown-locator'::text;
                        CONTINUE;
                    END IF;
                    IF v_retracted IS NOT NULL THEN
                        v_codes := v_codes || 'ONT-PRN-006:locator-retracted'::text;
                    END IF;
                    IF v_lcase IS DISTINCT FROM p_case_id THEN
                        v_codes := v_codes || 'ONT-PRN-004:cross-case-grounding'::text;
                        CONTINUE;  -- eligibility inherited for same-case only
                    END IF;
                    SELECT * INTO v_elig
                      FROM argus_private.can_support_observation(v_artifact);
                    v_codes := v_codes || v_elig.reasons;
                END LOOP;
            END IF;
            RETURN ARRAY(SELECT DISTINCT c FROM unnest(v_codes) AS c ORDER BY c);
        END $$;
        """
    )

    # ---- creation (DEFINER: the only insert paths; nearly mechanical) ----
    op.execute(
        """
        CREATE FUNCTION argus_private.create_source_locator(
            p_id text, p_artifact_id text, p_scheme text, p_payload jsonb,
            p_actor_class text, p_actor_id text, p_ai_ver text
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE
            v_case text; v_codes text[];
        BEGIN
            IF p_actor_class IS DISTINCT FROM 'HUMAN' THEN
                RAISE EXCEPTION 'ONT-PRN-007: SourceLocator creation is human-only in Slice 1D';
            END IF;
            SELECT case_id INTO v_case FROM public.evidence_artifacts WHERE id = p_artifact_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-SRC-001: unknown artifact %', p_artifact_id;
            END IF;
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
            PERFORM 1 FROM public.evidence_artifacts WHERE id = p_artifact_id FOR UPDATE;
            v_codes := argus_private.validate_source_locator(p_artifact_id, p_scheme, p_payload);
            IF cardinality(v_codes) > 0 THEN
                RAISE EXCEPTION 'ONT-SRC-001: inadmissible: %', array_to_string(v_codes, ', ');
            END IF;
            INSERT INTO public.source_locators
                (id, case_id, artifact_id, scheme, payload, created_by_class,
                 created_by_id, created_at)
            VALUES (p_id, v_case, p_artifact_id, p_scheme, p_payload,
                    p_actor_class, p_actor_id, clock_timestamp());
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case, p_actor_class,
                p_actor_id, p_ai_ver, 'locator-created', 'SourceLocator', p_id,
                'SUCCEEDED', jsonb_build_object('artifact_id', p_artifact_id, 'scheme', p_scheme));
            RETURN p_id;
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.create_observation(
            p_id text, p_case_id text, p_locator_ids text[], p_statement text,
            p_method text, p_actor_class text, p_actor_id text, p_ai_ver text,
            p_event_start timestamptz, p_event_end timestamptz
        ) RETURNS text
        """ + DEFINER + """
        AS $$
        DECLARE
            v_codes text[]; v_citation text; v_n integer; v_lid text;
        BEGIN
            PERFORM 1 FROM public.case_audit_heads WHERE case_id = p_case_id FOR UPDATE;
            v_codes := argus_private.validate_observation(
                p_case_id, p_locator_ids, p_statement, p_method, p_actor_class);
            IF cardinality(v_codes) > 0 THEN
                RAISE EXCEPTION 'ONT-OBS-001: inadmissible: %', array_to_string(v_codes, ', ');
            END IF;
            SELECT count(*) + 1 INTO v_n FROM public.observations WHERE case_id = p_case_id;
            v_citation := 'OBS-' || lpad(v_n::text, 6, '0');
            INSERT INTO public.observations
                (id, case_id, citation, statement, method_description,
                 event_time_start, event_time_end, created_by_class,
                 created_by_id, created_at)
            VALUES (p_id, p_case_id, v_citation, p_statement, p_method,
                    p_event_start, p_event_end, p_actor_class, p_actor_id,
                    clock_timestamp());
            FOREACH v_lid IN ARRAY p_locator_ids LOOP
                INSERT INTO public.observation_groundings
                    (id, observation_id, locator_id, created_at)
                VALUES (replace(gen_random_uuid()::text, '-', ''), p_id, v_lid,
                        clock_timestamp());
            END LOOP;
            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), p_case_id,
                p_actor_class, p_actor_id, p_ai_ver, 'claim-created',
                'Observation', p_id, 'SUCCEEDED',
                jsonb_build_object('citation', v_citation,
                                   'locators', to_jsonb(p_locator_ids)));
            RETURN p_id;
        END $$;
        """
    )

    # ---- retraction (DEFINER, human-only, reason required) ----
    for table, fn, action, target in (
        ("source_locators", "retract_source_locator", "locator-retracted", "SourceLocator"),
        ("observations", "retract_observation", "claim-retracted", "Observation"),
    ):
        op.execute(
            f"""
            CREATE FUNCTION argus_private.{fn}(
                p_id text, p_actor_class text, p_actor_id text,
                p_ai_ver text, p_reason text
            ) RETURNS void
            """ + DEFINER + f"""
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
                  FROM public.{table} WHERE id = p_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'ONT-PRN-006: unknown record %', p_id;
                END IF;
                IF v_retracted IS NOT NULL THEN
                    RAISE EXCEPTION 'ONT-PRN-006: already retracted (retraction is terminal)';
                END IF;
                PERFORM 1 FROM public.case_audit_heads WHERE case_id = v_case FOR UPDATE;
                UPDATE public.{table}
                   SET retracted_at = clock_timestamp(), retraction_reason = p_reason
                 WHERE id = p_id;
                PERFORM argus_private.append_audit_event(
                    replace(gen_random_uuid()::text, '-', ''), v_case,
                    p_actor_class, p_actor_id, p_ai_ver, '{action}',
                    '{target}', p_id, 'SUCCEEDED',
                    jsonb_build_object('reason', p_reason));
            END $$;
            """
        )

    # ---- groundedness: derived, never stored (ADR-0020 §6) ----
    op.execute(
        """
        CREATE FUNCTION argus_private.is_observation_grounded(p_obs_id text)
        RETURNS boolean
        """ + INVOKER + """
        AS $$
        BEGIN
            RETURN EXISTS (
                SELECT 1
                  FROM public.observation_groundings g
                  JOIN public.source_locators l ON l.id = g.locator_id
                  JOIN public.evidence_artifacts a ON a.id = l.artifact_id
                 WHERE g.observation_id = p_obs_id
                   AND l.retracted_at IS NULL
                   AND a.status = 'ACTIVE');
        END $$;
        """
    )

    # ---- grants: same transaction (Amendment 3 discipline from ADR-0016) ----
    fns = [
        ("validate_source_locator", "text, text, jsonb"),
        ("validate_observation", "text, text[], text, text, text"),
        ("create_source_locator", "text, text, text, jsonb, text, text, text"),
        ("create_observation", "text, text, text[], text, text, text, text, text, timestamptz, timestamptz"),
        ("retract_source_locator", "text, text, text, text, text"),
        ("retract_observation", "text, text, text, text, text"),
        ("is_observation_grounded", "text"),
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
                    ON public.source_locators, public.observations,
                       public.observation_groundings
                    TO argus_test_admin;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for stmt in [
        "DROP FUNCTION IF EXISTS argus_private.is_observation_grounded(text)",
        "DROP FUNCTION IF EXISTS argus_private.retract_observation(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.retract_source_locator(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.create_observation(text, text, text[], text, text, text, text, text, timestamptz, timestamptz)",
        "DROP FUNCTION IF EXISTS argus_private.create_source_locator(text, text, text, jsonb, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.validate_observation(text, text[], text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.validate_source_locator(text, text, jsonb)",
    ]:
        op.execute(stmt)
    op.drop_table("observation_groundings")
    op.drop_table("observations")
    op.drop_table("source_locators")
