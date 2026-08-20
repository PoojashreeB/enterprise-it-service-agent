import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.core.db import Base, get_db


@pytest.fixture()
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(test_engine, monkeypatch):
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    # The lifespan handler calls Base.metadata.create_all(bind=engine) using
    # the module-level `engine`, which points at the real database. Point it
    # at the in-memory test engine instead so tests never touch real data.
    monkeypatch.setattr(main_module, "engine", test_engine)
    main_module.app.dependency_overrides[get_db] = override_get_db

    with TestClient(main_module.app) as test_client:
        yield test_client

    main_module.app.dependency_overrides.clear()


@pytest.fixture()
def signup(client):
    def _signup(email="user@example.com", password="password123"):
        response = client.post(
            "/auth/signup",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        return response.json()

    return _signup


@pytest.fixture()
def auth_headers(signup):
    token = signup()["access_token"]
    return {"Authorization": f"Bearer {token}"}
