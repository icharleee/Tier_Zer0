"""012 — Database principal guard (Slice 1F-A, ADR-0033 / ONT-PRN-028).

Identity is authenticated, never asserted. This migration adds the
persistence-boundary half of the three-layer identity invariant (transport
proves the principal, the domain derives the actor, the database verifies
they agree at execution time — O13):

- assert_transaction_principal: the PRIMARY guard, called at the beginning
  of the constitutional mutation path by the authenticated application
  transaction. Fails closed — a bound principal is required; a bound
  principal inconsistent with the actor is refused.
- guard_audit_actor_principal: DEFENSE-IN-DEPTH only, a BEFORE INSERT
  trigger on audit_entries that re-checks consistency WHEN a principal is
  bound. Trusted internal transactions (fixtures, bootstrap, migrations)
  bind no principal and are unaffected — this is not a fallback reachable
  from the transport boundary, which always binds a principal.

Honest bound (Slice 1B-style): the trusted service sets both the bound
principal and the actor arguments, so this detects INCONSISTENCY, not a
fully-compromised service. It makes the binding invariant checkable at the
persistence boundary — the class the storage_ref defect belonged to.

Principal context is transaction-scoped (set_config(..., is_local => true)
== SET LOCAL); a persistent pooled-connection GUC would leak the principal
across requests.

Revision ID: 012_actor_principal_guard
Revises: 011_storage_reconciliation
"""

from alembic import op

revision = "012_actor_principal_guard"
down_revision = "011_storage_reconciliation"
branch_labels = None
depends_on = None

INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"
TRIGGER_FN = "LANGUAGE plpgsql SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION argus_private.assert_transaction_principal(
            p_actor_class text, p_actor_id text, p_human_attribution text
        ) RETURNS void
        """ + INVOKER + """
        AS $$
        DECLARE v_pid text; v_pclass text; v_hattr text;
        BEGIN
            v_pid := current_setting('argus.actor_principal', true);
            -- Fail closed: this function runs only on the authenticated
            -- application transaction path; no bound principal is a refusal,
            -- never a fallback to caller-supplied identity.
            IF v_pid IS NULL OR v_pid = '' THEN
                RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:unauthenticated';
            END IF;
            v_pclass := current_setting('argus.actor_principal_class', true);
            v_hattr := coalesce(current_setting('argus.human_attribution', true), '');
            IF p_actor_class = 'HUMAN' THEN
                IF v_pclass IS DISTINCT FROM 'HUMAN'
                   OR p_actor_id IS DISTINCT FROM v_pid THEN
                    RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:actor-principal-mismatch';
                END IF;
            ELSIF p_actor_class = 'SYSTEM' THEN
                IF v_pclass IS DISTINCT FROM 'SERVICE'
                   OR p_actor_id IS DISTINCT FROM v_pid
                   OR coalesce(p_human_attribution, '') IS DISTINCT FROM v_hattr THEN
                    RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:actor-principal-mismatch';
                END IF;
            ELSE
                -- No AI principal path exists in 1F-A.
                RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:actor-principal-mismatch';
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.guard_audit_actor_principal() RETURNS trigger
        """ + TRIGGER_FN + """
        AS $$
        DECLARE v_pid text; v_pclass text;
        BEGIN
            v_pid := current_setting('argus.actor_principal', true);
            -- Defense-in-depth only: trusted internal transactions bind no
            -- principal, so no check applies to them.
            IF v_pid IS NULL OR v_pid = '' THEN
                RETURN NEW;
            END IF;
            v_pclass := current_setting('argus.actor_principal_class', true);
            IF NEW.actor_class = 'HUMAN' THEN
                IF v_pclass IS DISTINCT FROM 'HUMAN'
                   OR NEW.actor_id IS DISTINCT FROM v_pid THEN
                    RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:actor-principal-mismatch';
                END IF;
            ELSIF NEW.actor_class = 'SYSTEM' THEN
                IF v_pclass IS DISTINCT FROM 'SERVICE'
                   OR NEW.actor_id IS DISTINCT FROM v_pid THEN
                    RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:actor-principal-mismatch';
                END IF;
            ELSE
                RAISE EXCEPTION 'ONT-PRN-028: inadmissible: ONT-PRN-007:actor-principal-mismatch';
            END IF;
            RETURN NEW;
        END $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_actor_principal
        BEFORE INSERT ON public.audit_entries
        FOR EACH ROW EXECUTE FUNCTION argus_private.guard_audit_actor_principal();
        """
    )

    op.execute(
        "REVOKE ALL ON FUNCTION argus_private.assert_transaction_principal(text, text, text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION argus_private.assert_transaction_principal(text, text, text) TO argus_app"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_actor_principal ON public.audit_entries")
    op.execute("DROP FUNCTION IF EXISTS argus_private.guard_audit_actor_principal()")
    op.execute("DROP FUNCTION IF EXISTS argus_private.assert_transaction_principal(text, text, text)")
