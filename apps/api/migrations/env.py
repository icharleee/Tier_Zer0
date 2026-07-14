"""Alembic environment. Migrations run as argus_owner against roles that
already exist (ADR-0016 Amendment 5); migration 001 verifies this."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import create_engine

config = context.config
url = os.environ.get("ARGUS_MIGRATION_URL") or config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
