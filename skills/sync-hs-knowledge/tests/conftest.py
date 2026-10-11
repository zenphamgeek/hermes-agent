"""Pytest test configuration and in-memory test database fixtures."""

import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add skill root to sys.path
SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from service.db.models import Base
from service.core.registry import SourceRegistry


@pytest.fixture(scope="session")
def registry():
    catalog_path = SKILL_ROOT / "references" / "source-catalog.yaml"
    return SourceRegistry(str(catalog_path))


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
