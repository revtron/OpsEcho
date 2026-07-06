from context_engine.engine import OperationalContextEngine

engine = OperationalContextEngine()


def test_enrich_kubernetes_event():
    event = {
        "event_type": "kubernetes",
        "source": "kubernetes",
        "timestamp": "2024-01-01T12:00:00Z",
        "raw_data": {
            "type": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
            "namespace": "production",
            "status": "Running"
        },
        "normalized_data": {
            "kind": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
            "namespace": "production",
            "status": "healthy",
            "action": "running"
        }
    }
    result = engine.enrich_event(event)
    assert "deployment_history" in result
    assert "related_incidents" in result
    assert "dependencies" in result
    assert "previous_failures" in result
    assert "ownership" in result
    assert "historical_patterns" in result
    assert "correlations" in result
    assert "enriched_at" in result


def test_enrich_event_preserves_original():
    event = {
        "event_type": "kubernetes",
        "source": "test-cluster",
        "timestamp": "2024-01-01T12:00:00Z",
        "raw_data": {"status": "Running"},
        "normalized_data": {"status": "healthy"}
    }
    result = engine.enrich_event(event)
    assert result["event_type"] == "kubernetes"
    assert result["source"] == "test-cluster"


def test_enrich_terraform_event():
    event = {
        "event_type": "terraform",
        "source": "terraform-production",
        "timestamp": "2024-01-01T12:00:00Z",
        "raw_data": {
            "changes": {
                "create": ["aws_db_instance.prod-db"],
                "update": [],
                "delete": [],
            }
        },
        "normalized_data": {"status": "healthy", "action": "terraform_apply"}
    }
    result = engine.enrich_event(event)
    assert "enriched_at" in result


def test_extract_service_name_k8s_pod_with_kind():
    event = {
        "event_type": "kubernetes",
        "source": "kubernetes",
        "raw_data": {
            "kind": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
        }
    }
    name = engine._extract_service_name(event)
    assert name == "web"


def test_extract_service_name_k8s_deployment():
    event = {
        "event_type": "kubernetes",
        "source": "kubernetes",
        "raw_data": {
            "kind": "Deployment",
            "name": "api-gateway",
        }
    }
    name = engine._extract_service_name(event)
    assert name == "api-gateway"


def test_extract_service_name_git():
    event = {
        "event_type": "git",
        "source": "github.com/org/web-app",
        "raw_data": {
            "repository": {"name": "web-app"},
        }
    }
    name = engine._extract_service_name(event)
    assert name == "web-app"


def test_extract_service_name_fallback_to_source():
    event = {
        "event_type": "unknown-type",
        "source": "test-cluster",
        "raw_data": {
            "type": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
        }
    }
    name = engine._extract_service_name(event)
    assert name == "test-cluster"
