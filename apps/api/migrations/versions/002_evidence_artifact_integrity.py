"""002 — EvidenceArtifact integrity enforcement.

Creates evidence_artifacts with the five ADR-0007 constitutional states
(STAGED deliberately absent — pre-constitutional) and enforces the
Invariant Matrix rows at the database layer:

- content-immutable field group: no UPDATE grant + BEFORE UPDATE guard trigger;
- no DELETE grant (the application role and ordinary operational roles cannot
  delete; privileged owners remain inside the declared trust boundary);
- status: excluded from the application role's UPDATE grants entirely —
  changed only by the SECURITY DEFINER transition functions (migration 003);
- storage_ref: the single controlled-transition column argus_app may update.

Revision ID: 002_artifact
Revises: 001_core
"""

from alembic import op
import sqlalchemy as sa

revision = "002_artifact"
down_revision = "001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_artifacts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("case_id", sa.String(32), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("hash_algorithm", sa.String(32), nullable=False),
        sa.Column("hash_digest", sa.String(128), nullable=False, index=True),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("media_type", sa.String(255), nullable=False),
        sa.Column("acquisition_description", sa.Text, nullable=False),
        sa.Column("ingested_by_class", sa.String(16), nullable=False),
        sa.Column("ingested_by_id", sa.String(200), nullable=False),
        sa.Column("human_authority", sa.String(200), nullable=False),
        sa.Column("storage_ref", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retraction_reason", sa.Text, nullable=True),
        sa.Column(
            "superseded_by",
            sa.String(32),
            sa.ForeignKey("evidence_artifacts.id"),
            nullable=True,
        ),
        # STAGED is not a value here: staging is pre-constitutional (ADR-0007 §2).
        sa.CheckConstraint(
            "status IN ('PENDING_VERIFICATION','ACTIVE','QUARANTINED','RETRACTED','SEALED')",
            name="ck_artifact_status",
        ),
        sa.CheckConstraint(
            "length(trim(acquisition_description)) > 0",
            name="ck_artifact_provenance",  # ONT-PRN-005 at the persistence boundary
        ),
    )

    # Second line of defense above grants: content-immutable columns can never
    # change via DML. (Owners can alter schema; that is the declared trust
    # boundary — detected by review and chain verification, not prevented.)
    op.execute(
        """
        CREATE FUNCTION argus_private.guard_artifact_immutable()
        RETURNS trigger
        LANGUAGE plpgsql
        SET search_path = argus_private, pg_catalog, pg_temp
        AS $$
        BEGIN
            IF NEW.id IS DISTINCT FROM OLD.id
               OR NEW.case_id IS DISTINCT FROM OLD.case_id
               OR NEW.hash_algorithm IS DISTINCT FROM OLD.hash_algorithm
               OR NEW.hash_digest IS DISTINCT FROM OLD.hash_digest
               OR NEW.size_bytes IS DISTINCT FROM OLD.size_bytes
               OR NEW.media_type IS DISTINCT FROM OLD.media_type
               OR NEW.acquisition_description IS DISTINCT FROM OLD.acquisition_description
               OR NEW.ingested_by_class IS DISTINCT FROM OLD.ingested_by_class
               OR NEW.ingested_by_id IS DISTINCT FROM OLD.ingested_by_id
               OR NEW.human_authority IS DISTINCT FROM OLD.human_authority
               OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                RAISE EXCEPTION
                    'ONT-EVA-001: content-immutable EvidenceArtifact fields cannot be modified';
            END IF;
            RETURN NEW;
        END $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_artifact_immutable
        BEFORE UPDATE ON public.evidence_artifacts
        FOR EACH ROW EXECUTE FUNCTION argus_private.guard_artifact_immutable();
        """
    )

    op.execute("GRANT SELECT, INSERT ON public.evidence_artifacts TO argus_app")
    op.execute("GRANT UPDATE (storage_ref) ON public.evidence_artifacts TO argus_app")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_artifact_immutable ON public.evidence_artifacts")
    op.execute("DROP FUNCTION IF EXISTS argus_private.guard_artifact_immutable()")
    op.drop_table("evidence_artifacts")
