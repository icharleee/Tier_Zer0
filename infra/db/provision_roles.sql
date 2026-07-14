-- ARGUS database role provisioning (ADR-0016, Amendment 5).
-- Run by infrastructure (a superuser or role-admin identity) BEFORE Alembic.
-- Alembic migrations verify these roles exist and fail clearly if not; they
-- never create roles themselves.
--
-- Passwords below are DEVELOPMENT/CI defaults. Production provisioning
-- replaces them via its secret mechanism (deployment ADR, deferred).
-- Idempotent: safe to re-run.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_owner') THEN
        CREATE ROLE argus_owner LOGIN PASSWORD 'argus_owner_dev';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_app') THEN
        CREATE ROLE argus_app LOGIN PASSWORD 'argus_app_dev';
    END IF;
    -- Privileged tampering role for the corruption-detection test ONLY.
    -- Exists in dev/CI databases; never provisioned in production.
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'argus_test_admin') THEN
        CREATE ROLE argus_test_admin LOGIN PASSWORD 'argus_test_admin_dev';
    END IF;
END
$$;
