"""001 — Core case, authority, and audit-head foundation.

Verifies provisioned roles exist (never creates them — ADR-0016 Amendment 5),
creates the argus_private schema, and lays the Case foundation: cases,
append-only case_authorities, and the per-case audit-chain root
case_audit_heads (ADR-0016).

Grants (argus_app): SELECT+INSERT only on all three tables. The head row is
advanced only inside argus_private.append_audit_event (migration 003).

Revision ID: 001_core
Revises: None
"""

from alembic import op
import sqlalchemy as sa

revision = "001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Roles must pre-exist (infra/db/provision.sh). Fail clearly if not.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_app') THEN
                RAISE EXCEPTION 'Role argus_app missing: run infra/db/provision.sh before Alembic (ADR-0016 Amendment 5)';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_owner') THEN
                RAISE EXCEPTION 'Role argus_owner missing: run infra/db/provision.sh before Alembic (ADR-0016 Amendment 5)';
            END IF;
        END $$;
        """
    )

    # Trusted, non-user-writable schema for SECURITY DEFINER functions
    # (ADR-0016 Amendment 3). argus_app gets USAGE only, never CREATE.
    op.execute("CREATE SCHEMA IF NOT EXISTS argus_private")
    op.execute("REVOKE ALL ON SCHEMA argus_private FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA argus_private TO argus_app")

    op.create_table(
        "cases",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("responsible_actor", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('OPEN','SUSPENDED','CLOSED')", name="ck_case_status"
        ),
    )
    op.create_table(
        "case_authorities",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("basis", sa.Text, nullable=False),
        sa.Column("recorded_by", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "case_audit_heads",
        sa.Column(
            "case_id", sa.String(32), sa.ForeignKey("cases.id"), primary_key=True
        ),
        sa.Column("last_sequence", sa.Integer, nullable=False),
        sa.Column("last_event_hash", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Least privilege (Invariant Matrix, Case rows): append-only postures.
    op.execute("GRANT SELECT, INSERT ON public.cases TO argus_app")
    op.execute("GRANT SELECT, INSERT ON public.case_authorities TO argus_app")
    op.execute("GRANT SELECT, INSERT ON public.case_audit_heads TO argus_app")


def downgrade() -> None:
    op.drop_table("case_audit_heads")
    op.drop_table("case_authorities")
    op.drop_table("cases")
    op.execute("DROP SCHEMA IF EXISTS argus_private CASCADE")
