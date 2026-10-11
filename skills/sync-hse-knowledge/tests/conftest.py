"""Pytest fixtures for HSE knowledge testing."""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.db.models import Base
from service.core.registry import load_source_registry, SourceRegistry


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def registry() -> SourceRegistry:
    return load_source_registry()
