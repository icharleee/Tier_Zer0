"""Constitutional test fixtures.

Application-layer constitutional semantics run here against SQLite for speed.
Database-layer enforcement rows of the Invariant Matrix (INSERT-only grants,
controlled functions, audit immutability for all roles) are verified against
real PostgreSQL in CI — those tests carry @pytest.mark.postgres and land with
the Alembic migrations; testing them against SQLite would test nothing
constitutional (ADR-0006).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from argus.domain import actors
from argus.domain.models import Base
from argus.ingestion.service import create_case
from argus.ingestion.store import LocalContentStore


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


# ---- PostgreSQL fixtures (Slice 1B adversarial suite) ----
# DATABASE_URL: the argus_app (least-privilege) connection.
# ARGUS_TEST_ADMIN_URL: the tampering role, dev/CI only, used to cross the
# declared trust boundary in the corruption-detection test and to clean up
# between tests (the app role deliberately cannot delete anything).

import os

from sqlalchemy import text as _text

_PG_TABLES_FK_ORDER = (
    "audit_entries",
    "case_audit_heads",
    "observation_groundings",
    "observations",
    "source_locators",
    "evidence_artifacts",
    "case_authorities",
    "cases",
)


def _pg_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def _pg_admin_url() -> str | None:
    return os.environ.get("ARGUS_TEST_ADMIN_URL")


@pytest.fixture(scope="session")
def pg_engine():
    url = _pg_url()
    if not url:
        pytest.skip("DATABASE_URL not set: PostgreSQL enforcement suite skipped")
    return create_engine(url, pool_pre_ping=True)


@pytest.fixture(scope="session")
def pg_admin_engine():
    url = _pg_admin_url()
    if not url:
        pytest.skip("ARGUS_TEST_ADMIN_URL not set")
    return create_engine(url, pool_pre_ping=True)


@pytest.fixture()
def pg_session(pg_engine, pg_admin_engine):
    with pg_admin_engine.begin() as conn:  # clean slate; app role cannot delete
        for table in _PG_TABLES_FK_ORDER:
            conn.execute(_text(f"DELETE FROM public.{table}"))
    with Session(pg_engine) as s:
        yield s
        s.rollback()


@pytest.fixture()
def store(tmp_path):
    return LocalContentStore(tmp_path / "content")


@pytest.fixture()
def investigator():
    return actors.human("det.reyes")


@pytest.fixture()
def verifier():
    return actors.system("ingest-verifier-01", human_authority="det.reyes")


@pytest.fixture()
def case(session, investigator):
    return create_case(
        session,
        title="Synthetic case for constitutional verification",
        legal_authority_basis="Test warrant 2026-SYN-001",
        responsible=investigator,
    )
