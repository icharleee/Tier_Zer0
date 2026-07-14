"""003 — Append-only audit chain and controlled transition functions (ADR-0016).

Creates audit_entries (hash-chained, chain_version=1) and the argus_private
SECURITY DEFINER functions. The application role's postures:

- audit_entries: SELECT only — the ONLY insert path is append_audit_event;
  no UPDATE/DELETE grants for any ordinary role;
- transitions: EXECUTE on the six named wrappers, which hold the global lock
  order (case_audit_heads FOR UPDATE, then artifact row FOR UPDATE), validate
  predecessor/actor/action against the Entity Lifecycles §2 registry, mutate,
  and append the event — one function body, atomic, both or neither.

All functions: trusted schema, schema-qualified references,
search_path = argus_private, pg_catalog, pg_temp, REVOKE FROM PUBLIC,
created and permissioned in this one migration transaction (Amendment 3).

Revision ID: 003_audit_chain
Revises: 002_artifact
"""

from alembic import op
import sqlalchemy as sa

revision = "003_audit_chain"
down_revision = "002_artifact"
branch_labels = None
depends_on = None

DEFINER_OPTS = "LANGUAGE plpgsql SECURITY DEFINER SET search_path = argus_private, pg_catalog, pg_temp"
INVOKER_OPTS = "LANGUAGE plpgsql SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.create_table(
        "audit_entries",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("actor_class", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(200), nullable=False),
        sa.Column("ai_model_version", sa.String(200), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("target_id", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("detail", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("chain_version", sa.Integer, nullable=False),
        sa.Column("canonical_payload", sa.Text, nullable=True),
        sa.Column("previous_event_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("case_id", "seq", name="uq_audit_case_seq"),
    )

    # ---- canonical format helpers (chain_version = 1, ADR-0016) ----
    op.execute(
        r"""
        CREATE FUNCTION argus_private.chain_escape(v text) RETURNS text
        LANGUAGE sql IMMUTABLE
        SET search_path = argus_private, pg_catalog, pg_temp
        AS $$ SELECT replace(replace(v, '\', '\\'), E'\n', '\n') $$;
        """
    )
    op.execute(
        r"""
        CREATE FUNCTION argus_private.chain_field(name text, v text) RETURNS text
        LANGUAGE sql IMMUTABLE
        SET search_path = argus_private, pg_catalog, pg_temp
        AS $$
            SELECT name || '=' ||
                   CASE WHEN v IS NULL THEN '\N'
                        ELSE argus_private.chain_escape(v) END
        $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.canonical_jsonb(j jsonb) RETURNS text
        """ + INVOKER_OPTS + """ IMMUTABLE
        AS $$
        DECLARE
            t text;
            result text;
        BEGIN
            IF j IS NULL THEN RETURN NULL; END IF;
            t := jsonb_typeof(j);
            IF t = 'object' THEN
                SELECT string_agg(
                           to_jsonb(key)::text || ':' ||
                           argus_private.canonical_jsonb(j -> key),
                           ',' ORDER BY key COLLATE "C")
                  INTO result
                  FROM jsonb_object_keys(j) AS key;
                RETURN '{' || coalesce(result, '') || '}';
            ELSIF t = 'array' THEN
                SELECT string_agg(argus_private.canonical_jsonb(elem), ',' ORDER BY ord)
                  INTO result
                  FROM jsonb_array_elements(j) WITH ORDINALITY AS x(elem, ord);
                RETURN '[' || coalesce(result, '') || ']';
            ELSIF t = 'number' THEN
                IF j::text ~ '[.eE]' THEN
                    RAISE EXCEPTION 'chain_version=1 payloads may not contain non-integer numbers';
                END IF;
                RETURN j::text;
            ELSE
                RETURN j::text;  -- string (JSON-escaped), boolean, null
            END IF;
        END $$;
        """
    )

    # ---- the append routine: the ONLY audit insert path ----
    op.execute(
        """
        CREATE FUNCTION argus_private.append_audit_event(
            p_entry_id text, p_case_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_action text, p_target_type text,
            p_target_id text, p_outcome text, p_detail jsonb
        ) RETURNS text
        """ + DEFINER_OPTS + """
        AS $$
        DECLARE
            v_head public.case_audit_heads%ROWTYPE;
            v_seq integer;
            v_ts timestamptz;
            v_canonical_payload text;
            v_text text;
            v_hash text;
        BEGIN
            -- Global lock order step 1 (ADR-0016): the per-case head row.
            SELECT * INTO v_head FROM public.case_audit_heads
             WHERE case_id = p_case_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-AUD-001: no audit head for case %', p_case_id;
            END IF;
            v_seq := v_head.last_sequence + 1;
            v_ts := clock_timestamp();
            v_canonical_payload := argus_private.canonical_jsonb(p_detail);
            v_text :=
                argus_private.chain_field('chain_version', '1') || E'\n' ||
                argus_private.chain_field('case_id', p_case_id) || E'\n' ||
                argus_private.chain_field('seq', v_seq::text) || E'\n' ||
                argus_private.chain_field('target_type', p_target_type) || E'\n' ||
                argus_private.chain_field('target_id', p_target_id) || E'\n' ||
                argus_private.chain_field('action', p_action) || E'\n' ||
                argus_private.chain_field('actor_class', p_actor_class) || E'\n' ||
                argus_private.chain_field('actor_id', p_actor_id) || E'\n' ||
                argus_private.chain_field('ai_model_version', p_ai_model_version) || E'\n' ||
                argus_private.chain_field('occurred_at',
                    to_char(v_ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')) || E'\n' ||
                argus_private.chain_field('outcome', p_outcome) || E'\n' ||
                argus_private.chain_field('canonical_payload', v_canonical_payload) || E'\n' ||
                argus_private.chain_field('previous_event_hash', v_head.last_event_hash);
            v_hash := encode(sha256(convert_to(v_text, 'UTF8')), 'hex');

            INSERT INTO public.audit_entries
                (id, case_id, seq, actor_class, actor_id, ai_model_version,
                 action, target_type, target_id, outcome, detail, occurred_at,
                 chain_version, canonical_payload, previous_event_hash, event_hash)
            VALUES
                (p_entry_id, p_case_id, v_seq, p_actor_class, p_actor_id,
                 p_ai_model_version, p_action, p_target_type, p_target_id,
                 p_outcome, p_detail, v_ts,
                 1, v_canonical_payload, v_head.last_event_hash, v_hash);

            UPDATE public.case_audit_heads
               SET last_sequence = v_seq, last_event_hash = v_hash, updated_at = v_ts
             WHERE case_id = p_case_id;

            RETURN p_entry_id;
        END $$;
        """
    )

    # ---- the transition core: Entity Lifecycles §2, rendered in SQL ----
    op.execute(
        """
        CREATE FUNCTION argus_private.transition_artifact(
            p_artifact_id text, p_to_status text, p_actor_class text,
            p_actor_id text, p_ai_model_version text, p_action text, p_detail jsonb
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        DECLARE
            v_case_id text;
            v_art public.evidence_artifacts%ROWTYPE;
        BEGIN
            SELECT case_id INTO v_case_id FROM public.evidence_artifacts
             WHERE id = p_artifact_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-EVA-001: unknown artifact %', p_artifact_id;
            END IF;
            -- Global lock order (ADR-0016): head first, then the artifact row.
            PERFORM 1 FROM public.case_audit_heads
             WHERE case_id = v_case_id FOR UPDATE;
            SELECT * INTO v_art FROM public.evidence_artifacts
             WHERE id = p_artifact_id FOR UPDATE;

            -- Allowed-predecessor registry (Entity Lifecycles 2.0.0 §2;
            -- ONT-PRN-012 / ONT-PRN-007).
            IF NOT (
                (v_art.status = 'PENDING_VERIFICATION' AND p_to_status = 'ACTIVE'      AND p_actor_class = 'SYSTEM' AND p_action = 'artifact-activated') OR
                (v_art.status = 'PENDING_VERIFICATION' AND p_to_status = 'QUARANTINED' AND p_actor_class = 'SYSTEM' AND p_action = 'artifact-quarantined') OR
                (v_art.status = 'ACTIVE'      AND p_to_status = 'QUARANTINED' AND p_actor_class = 'SYSTEM' AND p_action = 'artifact-quarantined') OR
                (v_art.status = 'QUARANTINED' AND p_to_status = 'RETRACTED'   AND p_actor_class = 'HUMAN'  AND p_action = 'artifact-retracted') OR
                (v_art.status = 'QUARANTINED' AND p_to_status = 'ACTIVE'      AND p_actor_class = 'HUMAN'  AND p_action = 'artifact-reactivated') OR
                (v_art.status = 'ACTIVE'      AND p_to_status = 'RETRACTED'   AND p_actor_class = 'HUMAN'  AND p_action = 'artifact-retracted') OR
                (v_art.status = 'ACTIVE'      AND p_to_status = 'SEALED'      AND p_actor_class = 'HUMAN'  AND p_action = 'artifact-sealed') OR
                (v_art.status = 'SEALED'      AND p_to_status = 'ACTIVE'      AND p_actor_class = 'HUMAN'  AND p_action = 'artifact-unsealed')
            ) THEN
                RAISE EXCEPTION
                    'ONT-PRN-012/ONT-PRN-007: transition % -> % by % via % is not in the allowed-predecessor registry',
                    v_art.status, p_to_status, p_actor_class, p_action;
            END IF;

            UPDATE public.evidence_artifacts SET status = p_to_status
             WHERE id = p_artifact_id;

            PERFORM argus_private.append_audit_event(
                replace(gen_random_uuid()::text, '-', ''), v_case_id,
                p_actor_class, p_actor_id, p_ai_model_version, p_action,
                'EvidenceArtifact', p_artifact_id, 'SUCCEEDED', p_detail);
        END $$;
        """
    )

    # ---- the six named wrappers (argument order matches the Python adapter) ----
    op.execute(
        """
        CREATE FUNCTION argus_private.activate_evidence_artifact(
            p_artifact_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_verified_digest text
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.evidence_artifacts
                            WHERE id = p_artifact_id
                              AND hash_digest = p_verified_digest) THEN
                RAISE EXCEPTION 'ONT-EVA-001: activation requires the verifier''s recomputed digest to match the recorded original hash';
            END IF;
            PERFORM argus_private.transition_artifact(
                p_artifact_id, 'ACTIVE', p_actor_class, p_actor_id,
                p_ai_model_version, 'artifact-activated', NULL);
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.quarantine_evidence_artifact(
            p_artifact_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_reason text
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        BEGIN
            IF p_reason IS NULL OR length(trim(p_reason)) = 0 THEN
                RAISE EXCEPTION 'ONT-EVA-001: quarantine requires a reason';
            END IF;
            PERFORM argus_private.transition_artifact(
                p_artifact_id, 'QUARANTINED', p_actor_class, p_actor_id,
                p_ai_model_version, 'artifact-quarantined',
                jsonb_build_object('reason', p_reason));
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.reactivate_evidence_artifact(
            p_artifact_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_reverified_digest text, p_rationale text
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.evidence_artifacts
                            WHERE id = p_artifact_id
                              AND hash_digest = p_reverified_digest) THEN
                RAISE EXCEPTION 'ONT-EVA-001: reactivation requires re-verification against the original hash';
            END IF;
            IF p_rationale IS NULL OR length(trim(p_rationale)) = 0 THEN
                RAISE EXCEPTION 'ONT-PRN-007: quarantine disposition requires a rationale';
            END IF;
            PERFORM argus_private.transition_artifact(
                p_artifact_id, 'ACTIVE', p_actor_class, p_actor_id,
                p_ai_model_version, 'artifact-reactivated',
                jsonb_build_object('rationale', p_rationale));
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.retract_evidence_artifact(
            p_artifact_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_reason text, p_superseded_by text
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        BEGIN
            IF p_reason IS NULL OR length(trim(p_reason)) = 0 THEN
                RAISE EXCEPTION 'ONT-PRN-006: retraction requires a non-empty reason';
            END IF;
            PERFORM argus_private.transition_artifact(
                p_artifact_id, 'RETRACTED', p_actor_class, p_actor_id,
                p_ai_model_version, 'artifact-retracted',
                jsonb_build_object('reason', p_reason, 'superseded_by', p_superseded_by));
            UPDATE public.evidence_artifacts
               SET retracted_at = clock_timestamp(),
                   retraction_reason = p_reason,
                   superseded_by = p_superseded_by
             WHERE id = p_artifact_id;
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.seal_evidence_artifact(
            p_artifact_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_legal_basis text
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        BEGIN
            IF p_legal_basis IS NULL OR length(trim(p_legal_basis)) = 0 THEN
                RAISE EXCEPTION 'ONT-CAS-001: sealing requires a legal basis (Article VI)';
            END IF;
            PERFORM argus_private.transition_artifact(
                p_artifact_id, 'SEALED', p_actor_class, p_actor_id,
                p_ai_model_version, 'artifact-sealed',
                jsonb_build_object('legal_basis', p_legal_basis));
        END $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION argus_private.unseal_evidence_artifact(
            p_artifact_id text, p_actor_class text, p_actor_id text,
            p_ai_model_version text, p_legal_basis text
        ) RETURNS void
        """ + DEFINER_OPTS + """
        AS $$
        BEGIN
            IF p_legal_basis IS NULL OR length(trim(p_legal_basis)) = 0 THEN
                RAISE EXCEPTION 'ONT-CAS-001: unsealing requires a legal basis (Article VI)';
            END IF;
            PERFORM argus_private.transition_artifact(
                p_artifact_id, 'ACTIVE', p_actor_class, p_actor_id,
                p_ai_model_version, 'artifact-unsealed',
                jsonb_build_object('legal_basis', p_legal_basis));
        END $$;
        """
    )

    # ---- grants: created and permissioned in this same transaction ----
    op.execute("GRANT SELECT ON public.audit_entries TO argus_app")
    for fn, args in [
        ("chain_escape", "text"),
        ("chain_field", "text, text"),
        ("canonical_jsonb", "jsonb"),
        ("append_audit_event", "text, text, text, text, text, text, text, text, text, jsonb"),
        ("transition_artifact", "text, text, text, text, text, text, jsonb"),
        ("activate_evidence_artifact", "text, text, text, text, text"),
        ("quarantine_evidence_artifact", "text, text, text, text, text"),
        ("reactivate_evidence_artifact", "text, text, text, text, text, text"),
        ("retract_evidence_artifact", "text, text, text, text, text, text"),
        ("seal_evidence_artifact", "text, text, text, text, text"),
        ("unseal_evidence_artifact", "text, text, text, text, text"),
    ]:
        op.execute(f"REVOKE ALL ON FUNCTION argus_private.{fn}({args}) FROM PUBLIC")
    # argus_app may execute the append routine, the named wrappers, and the
    # canonical helper (parity test) — but NOT the transition core directly.
    for fn, args in [
        ("chain_escape", "text"),
        ("chain_field", "text, text"),
        ("canonical_jsonb", "jsonb"),
        ("append_audit_event", "text, text, text, text, text, text, text, text, text, jsonb"),
        ("activate_evidence_artifact", "text, text, text, text, text"),
        ("quarantine_evidence_artifact", "text, text, text, text, text"),
        ("reactivate_evidence_artifact", "text, text, text, text, text, text"),
        ("retract_evidence_artifact", "text, text, text, text, text, text"),
        ("seal_evidence_artifact", "text, text, text, text, text"),
        ("unseal_evidence_artifact", "text, text, text, text, text"),
    ]:
        op.execute(f"GRANT EXECUTE ON FUNCTION argus_private.{fn}({args}) TO argus_app")

    # Dev/CI only: the tampering role for the corruption-detection test.
    # Production provisioning never creates this role, so the grant is skipped.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_test_admin') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE
                    ON public.audit_entries, public.evidence_artifacts,
                       public.cases, public.case_authorities, public.case_audit_heads
                    TO argus_test_admin;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for stmt in [
        "DROP FUNCTION IF EXISTS argus_private.unseal_evidence_artifact(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.seal_evidence_artifact(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.retract_evidence_artifact(text, text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.reactivate_evidence_artifact(text, text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.quarantine_evidence_artifact(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.activate_evidence_artifact(text, text, text, text, text)",
        "DROP FUNCTION IF EXISTS argus_private.transition_artifact(text, text, text, text, text, text, jsonb)",
        "DROP FUNCTION IF EXISTS argus_private.append_audit_event(text, text, text, text, text, text, text, text, text, jsonb)",
        "DROP FUNCTION IF EXISTS argus_private.canonical_jsonb(jsonb)",
        "DROP FUNCTION IF EXISTS argus_private.chain_field(text, text)",
        "DROP FUNCTION IF EXISTS argus_private.chain_escape(text)",
    ]:
        op.execute(stmt)
    op.drop_table("audit_entries")
