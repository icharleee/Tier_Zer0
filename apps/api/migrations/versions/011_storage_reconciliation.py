"""011 — Storage reconciliation classifiers (Slice 1E, AGC Session 016).

No tables are created or altered, and no write path exists: reconciliation
is detection only (ONT-PRN-027 — repair sits behind a later gate). These
STABLE functions are the PostgreSQL rendering of the canonical
classification precedence in STORAGE_RECONCILIATION.md 0.1.0 §4–5; the
Python classifier is the independent sibling, and H9 compares them over
the same observed storage facts — probing itself is a declared
single-implementation surface.

Integrity conditions, never truth conditions (ONT-PRN-026): agreement is
never authenticity; divergence is never falsity.

Revision ID: 011_storage_reconciliation
Revises: 010_case_reconstruction
"""

from alembic import op

revision = "011_storage_reconciliation"
down_revision = "010_case_reconstruction"
branch_labels = None
depends_on = None

INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION argus_private.classify_storage_integrity(
            p_verification_performed boolean, p_present boolean,
            p_readable boolean, p_digest_match boolean,
            p_size_match boolean, p_location_match boolean
        ) RETURNS text
        """ + INVOKER + """
        AS $$
        BEGIN
            -- Canonical precedence (normative, STORAGE_RECONCILIATION.md §5):
            -- intentionally-unverified resolves first (SEALED default scan,
            -- unsupported algorithm, quarantine suspension).
            IF NOT coalesce(p_verification_performed, false) THEN
                RETURN 'UNVERIFIED';
            ELSIF NOT coalesce(p_present, false) THEN
                RETURN 'MISSING';
            ELSIF NOT coalesce(p_readable, false) THEN
                RETURN 'UNREADABLE';
            ELSIF NOT (coalesce(p_digest_match, false)
                       AND coalesce(p_size_match, false)
                       AND coalesce(p_location_match, false)) THEN
                RETURN 'DIVERGENT';
            ELSE
                RETURN 'MATCHED';
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.storage_divergence_reasons(
            p_digest_match boolean, p_size_match boolean, p_location_match boolean
        ) RETURNS text[]
        """ + INVOKER + """
        AS $$
        DECLARE v text[] := ARRAY[]::text[];
        BEGIN
            -- Diagnostic subconditions, sorted; not new top-level states.
            IF NOT coalesce(p_digest_match, false) THEN
                v := v || 'DIGEST_MISMATCH'::text;
            END IF;
            IF NOT coalesce(p_size_match, false) THEN
                v := v || 'SIZE_MISMATCH'::text;
            END IF;
            IF NOT coalesce(p_location_match, false) THEN
                v := v || 'STORAGE_LOCATION_MISMATCH'::text;
            END IF;
            RETURN v;
        END $$;
        """
    )

    fns = [
        ("classify_storage_integrity", "boolean, boolean, boolean, boolean, boolean, boolean"),
        ("storage_divergence_reasons", "boolean, boolean, boolean"),
    ]
    for fn, args in fns:
        op.execute(f"REVOKE ALL ON FUNCTION argus_private.{fn}({args}) FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION argus_private.{fn}({args}) TO argus_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS argus_private.storage_divergence_reasons(boolean, boolean, boolean)")
    op.execute("DROP FUNCTION IF EXISTS argus_private.classify_storage_integrity(boolean, boolean, boolean, boolean, boolean, boolean)")
