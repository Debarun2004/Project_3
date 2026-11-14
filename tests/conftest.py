"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.models import Base
from app.repositories.store import FleetStore


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """Run app lifespan against demo data for each API test."""
    monkeypatch.setenv("DATA_SOURCE", "demo")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mysql_client(monkeypatch: pytest.MonkeyPatch):
    """Run write API tests against an isolated SQL database."""
    monkeypatch.setenv("DATA_SOURCE", "demo")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with TestClient(app) as test_client:
            test_client.app.state.fleet_store = FleetStore(sessions)
            yield test_client
    finally:
        engine.dispose()
