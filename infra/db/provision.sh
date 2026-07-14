#!/usr/bin/env sh
# ARGUS dev/CI database provisioning (ADR-0016, Amendment 5).
# Creates roles and the database, then hands off to Alembic (run separately,
# as argus_owner). Requires a superuser connection (default: local postgres).
#
# Usage: PGSUPER_URL=postgresql://postgres@localhost/postgres ./provision.sh
set -eu

PGSUPER_URL="${PGSUPER_URL:-postgresql://postgres@localhost/postgres}"
DBNAME="${ARGUS_DB:-argus}"

psql "$PGSUPER_URL" -v ON_ERROR_STOP=1 -f "$(dirname "$0")/provision_roles.sql"

if ! psql "$PGSUPER_URL" -tAc "SELECT 1 FROM pg_database WHERE datname='${DBNAME}'" | grep -q 1; then
    psql "$PGSUPER_URL" -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DBNAME} OWNER argus_owner"
fi

# The application role must not be able to create objects in any schema on the
# definer functions' search_path (ADR-0016, Amendment 3).
psql "${PGSUPER_URL%/*}/${DBNAME}" -v ON_ERROR_STOP=1 <<'SQL'
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO argus_app, argus_test_admin;
GRANT ALL ON SCHEMA public TO argus_owner;
-- argus_test_admin tampers across the trust boundary in tests; table-level
-- privileges for it are granted by migration 003 in dev/CI only.
SQL

echo "Provisioned roles and database '${DBNAME}'. Next: run Alembic as argus_owner."
