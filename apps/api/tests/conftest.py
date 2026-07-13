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
