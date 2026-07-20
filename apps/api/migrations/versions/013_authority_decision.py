"""013 — Authority decision function (Slice 1F-B, ADR-0034 / ONT-PRN-029).

The PostgreSQL rendering of the pure authority decision
(AUTHORITY.md §4). It reads no tables and mutates nothing — authority is a
pure classification over normalized, resource-scoped capability grants; the
Python sibling is argus.domain.authority.authorize, and the H11 conformance
sweep compares the two over the same grant facts.

Authority governs actions and visibility, never epistemic standing: this
function returns ALLOW or a DENY reason, and no truth/credibility surface
exists. Capabilities are Case-scoped with no inheritance (only the named
capability satisfies the check) and there is no global scope in 1F-B.

Revision ID: 013_authority_decision
Revises: 012_actor_principal_guard
"""

from alembic import op

revision = "013_authority_decision"
down_revision = "012_actor_principal_guard"
branch_labels = None
depends_on = None

IMMUTABLE = "LANGUAGE plpgsql IMMUTABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION argus_private.authorize(
            p_required_capability text, p_resource_case_id text,
            p_caps text[], p_scope_ids text[]
        ) RETURNS text
        """ + IMMUTABLE + """
        AS $$
        DECLARE i integer; v_held boolean := false;
        BEGIN
            FOR i IN 1 .. coalesce(cardinality(p_caps), 0) LOOP
                IF p_caps[i] = p_required_capability THEN
                    v_held := true;
                    -- All grants are CASE-scoped in 1F-B.
                    IF p_scope_ids[i] = p_resource_case_id THEN
                        RETURN 'ALLOW';
                    END IF;
                END IF;
            END LOOP;
            IF v_held THEN
                RETURN 'RESOURCE_SCOPE_MISMATCH';
            ELSE
                RETURN 'CAPABILITY_NOT_GRANTED';
            END IF;
        END $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION argus_private.authorize(text, text, text[], text[]) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION argus_private.authorize(text, text, text[], text[]) TO argus_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS argus_private.authorize(text, text, text[], text[])")
