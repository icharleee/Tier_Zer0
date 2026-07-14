"""004 — Constitutional predicate: can_support_observation (ADR-0018).

The PostgreSQL rendering of the canonical eligibility matrix
(docs/domain/CONSTITUTIONAL_PREDICATES.md), derived independently of the
Python rendering — this pair is ODE Hypothesis H2's Experiment One.

Derived, never stored: this is a STABLE read-only function; no eligibility
flag exists in any table. SECURITY INVOKER — it reads only tables the
application role can already read. Reason codes are the canonical registry's;
wording lives in documentation, codes live here.

Revision ID: 004_predicates
Revises: 003_audit_chain
"""

from alembic import op

revision = "004_predicates"
down_revision = "003_audit_chain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION argus_private.can_support_observation(p_artifact_id text)
        RETURNS TABLE (
            structurally_eligible boolean,
            contextually_eligible boolean,
            reasons text[]
        )
        LANGUAGE plpgsql STABLE
        SET search_path = argus_private, pg_catalog, pg_temp
        AS $$
        DECLARE
            v_artifact_status text;
            v_case_status text;
            v_reasons text[] := ARRAY[]::text[];
            v_structural boolean := true;
        BEGIN
            SELECT a.status, c.status
              INTO v_artifact_status, v_case_status
              FROM public.evidence_artifacts a
              JOIN public.cases c ON c.id = a.case_id
             WHERE a.id = p_artifact_id;

            IF NOT FOUND THEN
                RETURN QUERY SELECT false, false,
                    ARRAY['ONT-EVA-001:unknown-artifact'];
                RETURN;
            END IF;

            -- Structural layer: could this artifact possibly support an
            -- Observation (objective).
            IF v_artifact_status = 'PENDING_VERIFICATION' THEN
                v_structural := false;
                v_reasons := v_reasons || 'ONT-EVA-001:not-yet-verified'::text;
            ELSIF v_artifact_status = 'QUARANTINED' THEN
                v_structural := false;
                v_reasons := v_reasons || 'ONT-EVA-001:integrity-unresolved'::text;
            ELSIF v_artifact_status = 'RETRACTED' THEN
                v_structural := false;
                v_reasons := v_reasons || 'ONT-PRN-006:retracted'::text;
            END IF;

            -- Contextual layer: may it, in this investigation. SEALED is
            -- structurally sound but access-restricted until an authority
            -- model exists (Slice 1F; Article IX — never guess at authority).
            IF v_artifact_status = 'SEALED' THEN
                v_reasons := v_reasons || 'ONT-EVA-001:sealed-access-restricted'::text;
            END IF;
            IF v_case_status = 'CLOSED' THEN
                v_reasons := v_reasons || 'ONT-CAS-001:case-closed'::text;
            ELSIF v_case_status = 'SUSPENDED' THEN
                v_reasons := v_reasons || 'ONT-CAS-001:case-suspended'::text;
            END IF;

            RETURN QUERY SELECT
                v_structural,
                (cardinality(v_reasons) = 0),
                v_reasons;
        END $$;
        """
    )
    op.execute(
        "REVOKE ALL ON FUNCTION argus_private.can_support_observation(text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION argus_private.can_support_observation(text) TO argus_app"
    )


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS argus_private.can_support_observation(text)"
    )
