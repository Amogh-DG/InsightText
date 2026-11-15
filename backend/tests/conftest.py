import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db import SessionLocal
from app.models.all_models import User
from app.core.security import create_access_token

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def auth_headers(db_session):
    def _get_headers(role: str):
        user = db_session.query(User).filter(User.role == role).first()
        if not user:
            user = db_session.query(User).filter(User.email.contains(role)).first()
        token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})
        return {"Authorization": f"Bearer {token}"}
    return _get_headers

@pytest.fixture(scope="session")
def admin_headers(auth_headers):
    return auth_headers("admin")

@pytest.fixture(scope="session")
def analyst_headers(auth_headers):
    return auth_headers("analyst")

@pytest.fixture(scope="session")
def scientist_headers(auth_headers):
    return auth_headers("data_scientist")

@pytest.fixture(scope="session")
def manager_headers(auth_headers):
    return auth_headers("manager")

@pytest.fixture(scope="session")
def reviewer_headers(auth_headers):
    return auth_headers("reviewer")

@pytest.fixture(scope="session")
def api_key_headers():
    return {"X-API-Key": "ak_demo_external_key_12345678"}
