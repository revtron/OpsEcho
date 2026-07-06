import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["OLLAMA_URL"] = "http://localhost:11434"

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import Base, engine, SessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_k8s_event():
    return {
        "type": "Pod",
        "name": "web-api-7d6f8c4b9-abcde",
        "namespace": "production",
        "status": "Running",
        "reason": "New pod created",
        "labels": {"app": "web-api"}
    }


@pytest.fixture
def sample_ec2_event():
    return {
        "instance_id": "i-0a1b2c3d4e5f6a7b8",
        "name": "web-server-prod-01",
        "instance_type": "t3.large",
        "state": "running",
        "status_check": "ok",
        "system_status_check": "ok",
        "region": "us-east-1",
    }
