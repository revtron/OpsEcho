import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "OpsEcho API is running"}


def test_receive_k8s_event():
    payload = {
        "type": "Pod",
        "name": "web-api-7d6f8c4b9-abcde",
        "namespace": "production",
        "status": "Running",
        "reason": "New pod created",
        "source": "k8s-production",
    }
    response = client.post("/api/events/k8s", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "event_id" in data


def test_receive_terraform_event():
    payload = {
        "source": "terraform-production",
        "changes": {
            "create": ["aws_db_instance.prod-db"],
            "update": [],
            "delete": [],
        }
    }
    response = client.post("/api/events/terraform", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


def test_receive_git_event():
    payload = {
        "source": "github.com/org/web-app",
        "event_type": "push",
        "branch": "main",
        "total_commits": 1,
        "repository": {"name": "web-app"},
    }
    response = client.post("/api/events/git", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


def test_receive_ec2_event():
    payload = {
        "source": "aws-ec2",
        "instance_id": "i-0a1b2c3d4e5f6a7b8",
        "name": "web-server-prod-01",
        "state": "running",
        "status_check": "ok",
    }
    response = client.post("/api/events/ec2", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


def test_get_events_empty():
    response = client.get("/api/events/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_events_after_creation():
    client.post("/api/events/k8s", json={
        "type": "Pod", "name": "test", "namespace": "default",
        "status": "Running", "source": "test",
    })
    response = client.get("/api/events/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "kubernetes"


def test_timeline_endpoint():
    response = client.get("/api/timeline/")
    assert response.status_code == 200


def test_search_endpoint():
    response = client.get("/api/search/?q=test")
    assert response.status_code == 200


def test_ec2_health_endpoint():
    response = client.get("/api/events/ec2-health")
    assert response.status_code == 200
    data = response.json()
    assert "instances" in data
    assert "total" in data
