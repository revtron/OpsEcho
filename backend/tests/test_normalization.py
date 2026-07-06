from normalization.engine import NormalizationEngine

engine = NormalizationEngine()


def test_normalize_k8s_pod_running():
    event = {
        "event_type": "kubernetes",
        "source": "k8s-production",
        "raw_data": {
            "type": "Pod",
            "name": "web-api-7d6f8c4b9-abcde",
            "namespace": "production",
            "status": "Running",
            "reason": "New pod created",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "healthy"
    assert result["severity"] == "info"
    assert result["kind"] == "Pod"
    assert result["name"] == "web-api-7d6f8c4b9-abcde"


def test_normalize_k8s_pod_crashloop():
    event = {
        "event_type": "kubernetes",
        "source": "k8s-staging",
        "raw_data": {
            "type": "Pod",
            "name": "redis-cache-6f8d4c2-xyz78",
            "namespace": "staging",
            "status": "Failed",
            "reason": "CrashLoopBackOff",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "failed"
    assert result["severity"] == "critical"
    assert result["failure_reason"] == "CrashLoopBackOff"


def test_normalize_k8s_deployment_degraded():
    event = {
        "event_type": "kubernetes",
        "source": "k8s-production",
        "raw_data": {
            "type": "Deployment",
            "name": "api-gateway",
            "namespace": "production",
            "status": "Running",
            "replicas": 5,
            "available_replicas": 3,
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "degraded"
    assert result["severity"] == "warning"


def test_normalize_k8s_node_not_ready():
    event = {
        "event_type": "kubernetes",
        "source": "k8s-production",
        "raw_data": {
            "type": "Node",
            "name": "ip-10-0-1-42",
            "status": "NotReady",
            "reason": "NodeNotReady",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "failed"
    assert result["severity"] == "critical"
    assert result["failure_reason"] == "NodeNotReady"


def test_normalize_terraform_success():
    event = {
        "event_type": "terraform",
        "source": "terraform-production",
        "raw_data": {
            "changes": {
                "create": ["aws_db_instance.prod-db"],
                "update": ["aws_ecs_service.web-app"],
                "delete": [],
            }
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "healthy"
    assert result["action"] == "terraform_apply"


def test_normalize_terraform_failure():
    event = {
        "event_type": "terraform",
        "source": "terraform-production",
        "raw_data": {
            "error": "Error acquiring the state lock",
            "errors": [{"message": "Error acquiring the state lock"}],
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "failed"
    assert result["severity"] == "critical"


def test_normalize_git_push():
    event = {
        "event_type": "git",
        "source": "github.com/org/web-app",
        "raw_data": {
            "event_type": "push",
            "branch": "main",
            "total_commits": 3,
            "repository": {"name": "web-app"},
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "healthy"
    assert result["action"] == "git_push"
    assert result["branch"] == "main"


def test_normalize_ec2_healthy():
    event = {
        "event_type": "ec2",
        "source": "aws-ec2-us-east-1",
        "raw_data": {
            "instance_id": "i-0a1b2c3d4e5f6a7b8",
            "name": "web-server-prod-01",
            "state": "running",
            "status_check": "ok",
            "system_status_check": "ok",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "healthy"
    assert result["severity"] == "info"


def test_normalize_ec2_impaired():
    event = {
        "event_type": "ec2",
        "source": "aws-ec2-us-east-1",
        "raw_data": {
            "instance_id": "i-0c3d4e5f6a7b8c9d0",
            "name": "api-server-prod-01",
            "state": "running",
            "status_check": "impaired",
            "system_status_check": "ok",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "failed"
    assert result["severity"] == "critical"


def test_normalize_docker_die():
    event = {
        "event_type": "docker",
        "source": "docker-local",
        "raw_data": {
            "action": "die",
            "status": "exited with code 137",
            "id": "abc123",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "failed"


def test_normalize_docker_start():
    event = {
        "event_type": "docker",
        "source": "docker-local",
        "raw_data": {
            "action": "start",
            "status": "started",
            "id": "abc123",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "healthy"


def test_normalize_aws_event():
    event = {
        "event_type": "aws",
        "source": "aws-cloudtrail",
        "raw_data": {
            "eventName": "CreateInstance",
            "region": "us-east-1",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "healthy"


def test_normalize_aws_failure_event():
    event = {
        "event_type": "aws",
        "source": "aws-cloudtrail",
        "raw_data": {
            "eventName": "TerminateInstances",
            "region": "us-east-1",
        }
    }
    result = engine.normalize_event(event)
    assert result["status"] == "degraded"
    assert result["severity"] == "warning"
