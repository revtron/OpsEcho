from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
from db.database import get_db, SessionLocal
from db.models import InfrastructureEvent, EventSummary
from collectors.k8s_watcher import K8sWatcher
from collectors.terraform_parser import TerraformParser
from collectors.git_webhook import GitWebhook
from collectors.aws_ec2 import EC2HealthCollector
from ai_layer.explainer import OperationalExplainer
import httpx

# Lazy-initialized AI explainer with health check
_explainer = None
_ai_available = None


def get_explainer():
    global _explainer, _ai_available
    if _ai_available is None:
        try:
            r = httpx.get("http://localhost:11434/api/tags", timeout=2)
            _ai_available = r.status_code == 200
        except Exception:
            _ai_available = False
        if _ai_available:
            try:
                _explainer = OperationalExplainer(model_name="phi")
                print("[AI] Ollama available — using AI summaries")
            except Exception:
                _explainer = None
                _ai_available = False
                print("[AI] Failed to initialize explainer, using fallback")
        else:
            print("[AI] Ollama not running — using template summaries")
    return _explainer


def _generate_demo_summary(enriched_data: dict) -> str:
    """Generate a demo summary without requiring Ollama."""
    event_type = enriched_data.get("event_type", "unknown")
    source = enriched_data.get("source", "unknown")
    raw_data = enriched_data.get("raw_data", {})
    normalized = enriched_data.get("normalized_data", {})
    severity = normalized.get("severity", "info")
    status = normalized.get("status", "unknown")
    failure_reason = normalized.get("failure_reason")

    prefix = ""
    if severity == "critical":
        prefix = "🔴 CRITICAL: "
    elif severity == "warning":
        prefix = "🟡 WARNING: "
    elif status == "healthy":
        prefix = "🟢 "

    if event_type == "kubernetes":
        kind = normalized.get("kind", "Resource")
        name = normalized.get("name", "unknown")
        namespace = normalized.get("namespace", "default")

        if failure_reason:
            return (
                f"{prefix}Kubernetes {kind} '{name}' in namespace '{namespace}' is in {status} state.\n\n"
                f"Failure: {failure_reason}\n\n"
                f"Impact: Service availability in {namespace} namespace is affected. "
                f"Immediate investigation recommended. Restart count: {normalized.get('restart_count', 0)}."
            )
        return (
            f"{prefix}Kubernetes {kind} '{name}' in namespace '{namespace}' is now {status}.\n\n"
            f"Probable reason: {raw_data.get('reason', 'Routine infrastructure operation')}.\n\n"
            f"Potential impact: Service availability in {namespace} namespace may be affected. "
            f"Monitor error rates and latency for the next 15 minutes."
        )
    elif event_type == "terraform":
        errors = raw_data.get("errors", [])
        if errors:
            error_msgs = "; ".join(e.get("message", str(e)) for e in errors[:3])
            return (
                f"{prefix}Terraform apply FAILED in '{source}': {error_msgs}.\n\n"
                f"Action required: Review Terraform logs and fix the configuration errors before re-applying."
            )
        changes = raw_data.get("changes", {})
        created = len(changes.get("create", []))
        updated = len(changes.get("update", []))
        deleted = len(changes.get("delete", []))
        resources = []
        if created:
            resources.append(f"created {created} resource(s): {', '.join(changes['create'][:3])}")
        if updated:
            resources.append(f"updated {updated} resource(s): {', '.join(changes['update'][:3])}")
        if deleted:
            resources.append(f"deleted {deleted} resource(s): {', '.join(changes['delete'][:3])}")
        changes_str = "; ".join(resources)
        return (
            f"{prefix}Terraform apply completed in '{source}': {changes_str}.\n\n"
            f"Probable reason: Infrastructure-as-code update pushed via CI/CD pipeline.\n\n"
            f"Potential impact: Cloud resources are being modified. "
            f"Expected no downtime for stateful resources. Verify DNS propagation if load balancers were updated."
        )
    elif event_type == "git":
        repo_name = raw_data.get("repository", {}).get("name", "unknown")
        branch = raw_data.get("branch", "")
        pr_number = raw_data.get("pull_request", {}).get("number", "")
        pr_title = raw_data.get("pull_request", {}).get("title", "")
        total_commits = raw_data.get("total_commits", 0)
        if branch:
            return (
                f"{prefix}Git push to '{repo_name}' on branch '{branch}' with {total_commits} commit(s).\n\n"
                f"Probable reason: Developer push triggering CI/CD pipeline.\n\n"
                f"Potential impact: New build and deployment pipeline will be triggered. "
                f"Check pipeline status for any failures."
            )
        else:
            return (
                f"{prefix}GitHub PR #{pr_number} opened in '{repo_name}': '{pr_title}'.\n\n"
                f"Probable reason: Developer submitted code changes for review.\n\n"
                f"Potential impact: Pending code review required before merge. "
                f"Review changes for infrastructure impact."
            )
    elif event_type == "ec2":
        name = normalized.get("name", "unknown")
        state = normalized.get("state", "unknown")
        check = normalized.get("status_check", "unknown")
        inst_type = normalized.get("instance_type", "")
        ip = normalized.get("private_ip") or normalized.get("public_ip") or ""
        events_list = raw_data.get("events", [])

        if failure_reason:
            return (
                f"{prefix}EC2 instance '{name}' ({inst_type}) is {state} — {check}.\n\n"
                f"Issue: {failure_reason}\n\n"
                f"Impact: Instance {name} ({ip}) in {source} is affected. "
                f"{'Scheduled events: ' + '; '.join(e.get('description','') for e in events_list) + '.' if events_list else ''}"
                f"Investigate and take corrective action."
            )
        return (
            f"{prefix}EC2 instance '{name}' ({inst_type}) is {state} with {check} status checks.\n\n"
            f"IP: {ip}. Region: {source}.\n\n"
            f"Potential impact: Instance is healthy. No action required."
        )

    return (
        f"{prefix}{event_type} event detected from '{source}'.\n\n"
        f"Probable reason: Routine infrastructure operation.\n\n"
        f"Potential impact: Monitor system health for any anomalies."
    )


def _generate_demo_embedding(text: str) -> str:
    """Generate a deterministic demo embedding."""
    import numpy as np
    hash_obj = hash(text)
    np.random.seed(abs(hash_obj) % 2**32)
    embedding = np.random.rand(768).tolist()
    return json.dumps(embedding)

router = APIRouter()

k8s_watcher = K8sWatcher()
terraform_parser = TerraformParser()
git_webhook = GitWebhook()
ec2_collector = EC2HealthCollector()


def _create_event(db: Session, event_type: str, source: str, raw_data: dict) -> InfrastructureEvent:
    """Create an InfrastructureEvent with status/severity/failure_reason extracted."""
    from normalization.engine import NormalizationEngine
    engine = NormalizationEngine()
    normalized = engine.normalize_event({
        "event_type": event_type,
        "source": source,
        "raw_data": raw_data,
    })

    db_event = InfrastructureEvent(
        event_type=event_type,
        source=source,
        raw_data=raw_data,
        normalized_data=normalized,
        status=normalized.get("status", "unknown"),
        severity=normalized.get("severity", "info"),
        failure_reason=normalized.get("failure_reason"),
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.post("/k8s")
async def receive_k8s_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_event = _create_event(db, "kubernetes", event.get("source", "unknown"), event)
    background_tasks.add_task(process_event, db_event.id)
    return {"status": "received", "event_id": db_event.id}


@router.post("/terraform")
async def receive_terraform_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_event = _create_event(db, "terraform", event.get("source", "unknown"), event)
    background_tasks.add_task(process_event, db_event.id)
    return {"status": "received", "event_id": db_event.id}


@router.post("/git")
async def receive_git_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_event = _create_event(db, "git", event.get("source", "unknown"), event)
    background_tasks.add_task(process_event, db_event.id)
    return {"status": "received", "event_id": db_event.id}


@router.post("/ec2")
async def receive_ec2_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_event = _create_event(db, "ec2", event.get("source", "aws-ec2"), event)
    background_tasks.add_task(process_event, db_event.id)
    return {"status": "received", "event_id": db_event.id}


@router.get("/ec2-health")
async def get_ec2_health():
    instances = ec2_collector.get_instance_health()
    return {"instances": instances, "total": len(instances)}


@router.post("/demo")
async def seed_demo_events(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    demo_events = [
        {
            "event_type": "kubernetes",
            "source": "k8s-production",
            "raw_data": {
                "type": "Pod", "name": "web-api-7d6f8c4b9-abcde",
                "namespace": "production", "status": "Running",
                "reason": "New pod created", "labels": {"app": "web-api"}
            }
        },
        {
            "event_type": "kubernetes",
            "source": "k8s-production",
            "raw_data": {
                "type": "Deployment", "name": "api-gateway",
                "namespace": "production", "status": "Running",
                "replicas": 5, "available_replicas": 3,
                "reason": "Rolling update in progress"
            }
        },
        {
            "event_type": "kubernetes",
            "source": "k8s-staging",
            "raw_data": {
                "type": "Pod", "name": "redis-cache-6f8d4c2-xyz78",
                "namespace": "staging", "status": "Failed",
                "reason": "CrashLoopBackOff", "labels": {"app": "redis-cache"}
            }
        },
        {
            "event_type": "kubernetes",
            "source": "k8s-production",
            "raw_data": {
                "type": "Pod", "name": "worker-service-9d2e1f3-ghijk",
                "namespace": "production", "status": "Running",
                "reason": "Scaled up by HPA", "labels": {"app": "worker-service"},
                "restart_count": 4,
                "container_statuses": [
                    {
                        "name": "worker",
                        "ready": True,
                        "restart_count": 4,
                        "state": "running",
                        "last_reason": "OOMKill"
                    }
                ]
            }
        },
        {
            "event_type": "kubernetes",
            "source": "k8s-production",
            "raw_data": {
                "type": "Node", "name": "ip-10-0-1-42",
                "status": "NotReady",
                "reason": "NodeNotReady",
                "labels": {"node.kubernetes.io/role": "worker"},
            }
        },
        {
            "event_type": "terraform",
            "source": "terraform-production",
            "raw_data": {
                "changes": {
                    "create": ["aws_db_instance.prod-db", "aws_s3_bucket.logs"],
                    "update": ["aws_ecs_service.web-app", "aws_security_group.api-sg"],
                    "delete": ["aws_lb.old-alb"]
                }
            }
        },
        {
            "event_type": "terraform",
            "source": "terraform-staging",
            "raw_data": {
                "changes": {
                    "create": ["aws_ec2_instance.dev-box"],
                    "update": ["aws_vpc.main"],
                    "delete": []
                }
            }
        },
        {
            "event_type": "terraform",
            "source": "terraform-production",
            "raw_data": {
                "changes": {"create": [], "update": [], "delete": []},
                "error": "Error acquiring the state lock: conditional request failed",
                "errors": [{"type": "state_lock_error", "message": "Error acquiring the state lock: conditional request failed"}]
            }
        },
        {
            "event_type": "git",
            "source": "github.com/org/web-app",
            "raw_data": {
                "event_type": "push", "branch": "main",
                "total_commits": 3, "commits": ["a1b2c3d", "e4f5g6h", "i7j8k9l"],
                "repository": {"name": "web-app", "owner": "org"},
                "author": "dev-team"
            }
        },
        {
            "event_type": "git",
            "source": "github.com/org/infra",
            "raw_data": {
                "event_type": "pull_request", "action": "opened",
                "pull_request": {"number": 142, "title": "feat: migrate RDS to Aurora"},
                "repository": {"name": "infra", "owner": "org"}
            }
        },
        {
            "event_type": "kubernetes",
            "source": "k8s-production",
            "raw_data": {
                "type": "Pod", "name": "payment-service-5f4e3d2-abcd1",
                "namespace": "production", "status": "Pending",
                "reason": "InsufficientMemory",
                "labels": {"app": "payment-service"}
            }
        },
        {
            "event_type": "kubernetes",
            "source": "k8s-production",
            "raw_data": {
                "type": "Deployment", "name": "frontend",
                "namespace": "production", "status": "Running",
                "replicas": 10, "available_replicas": 10,
                "reason": "Stable"
            }
        },
        {
            "event_type": "ec2",
            "source": "aws-ec2-us-east-1",
            "raw_data": {
                "instance_id": "i-0a1b2c3d4e5f6a7b8",
                "name": "web-server-prod-01",
                "instance_type": "t3.large",
                "state": "running",
                "status_check": "ok",
                "system_status_check": "ok",
                "region": "us-east-1",
                "private_ip": "10.0.1.12",
                "public_ip": "52.1.2.3",
                "vpc_id": "vpc-0a1b2c3d",
                "events": [],
            }
        },
        {
            "event_type": "ec2",
            "source": "aws-ec2-us-east-1",
            "raw_data": {
                "instance_id": "i-0c3d4e5f6a7b8c9d0",
                "name": "api-server-prod-01",
                "instance_type": "t3.xlarge",
                "state": "running",
                "status_check": "impaired",
                "system_status_check": "ok",
                "region": "us-east-1",
                "private_ip": "10.0.2.10",
                "public_ip": "52.1.2.10",
                "vpc_id": "vpc-0a1b2c3d",
                "events": [
                    {"code": "instance-retirement", "description": "Instance scheduled for retirement"}
                ],
            }
        },
        {
            "event_type": "ec2",
            "source": "aws-ec2-us-east-1",
            "raw_data": {
                "instance_id": "i-0d4e5f6a7b8c9d0e1",
                "name": "db-replica-01",
                "instance_type": "r5.large",
                "state": "running",
                "status_check": "degraded",
                "system_status_check": "degraded",
                "region": "us-east-1",
                "private_ip": "10.0.3.5",
                "events": [],
            }
        },
        {
            "event_type": "ec2",
            "source": "aws-ec2-us-east-1",
            "raw_data": {
                "instance_id": "i-0e5f6a7b8c9d0e1f2",
                "name": "batch-worker-01",
                "instance_type": "c5.2xlarge",
                "state": "stopped",
                "status_check": "unknown",
                "system_status_check": "unknown",
                "region": "us-east-1",
                "private_ip": "10.0.4.20",
                "events": [],
            }
        },
    ]

    created_ids = []
    for evt_data in demo_events:
        db_event = _create_event(db, evt_data["event_type"], evt_data["source"], evt_data["raw_data"])
        created_ids.append(db_event.id)

    for eid in created_ids:
        background_tasks.add_task(process_event, eid)

    return {"status": "ok", "events_created": len(created_ids), "event_ids": created_ids}


@router.get("/", response_model=List[dict])
async def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    events = db.query(InfrastructureEvent).offset(skip).limit(limit).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "source": e.source,
            "timestamp": e.timestamp,
            "is_processed": e.is_processed,
            "status": e.status,
            "severity": e.severity,
            "failure_reason": e.failure_reason,
        }
        for e in events
    ]


async def process_event(event_id: int):
    """
    Background task to process an event through the pipeline.
    Uses its own DB session to avoid thread-safety issues.
    """
    from normalization.engine import NormalizationEngine
    from context_engine.engine import OperationalContextEngine

    db = SessionLocal()
    try:
        event = db.query(InfrastructureEvent).filter(InfrastructureEvent.id == event_id).first()
        if not event:
            return

        normalization_engine = NormalizationEngine()
        normalized_data = normalization_engine.normalize_event({
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "raw_data": event.raw_data,
        })

        event.normalized_data = normalized_data
        event.status = normalized_data.get("status", "unknown")
        event.severity = normalized_data.get("severity", "info")
        event.failure_reason = normalized_data.get("failure_reason")

        context_engine = OperationalContextEngine()
        enriched_data = context_engine.enrich_event({
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "raw_data": event.raw_data,
            "normalized_data": normalized_data,
        })

        is_critical = normalized_data.get("severity") in ("critical", "warning") or normalized_data.get("status") in ("failed", "degraded")
        use_ai = is_critical
        if use_ai:
            explainer = get_explainer()
        else:
            explainer = None

        if explainer:
            try:
                summary_text = explainer.generate_summary(enriched_data)
            except Exception:
                summary_text = _generate_demo_summary(enriched_data)
        else:
            summary_text = _generate_demo_summary(enriched_data)
        embedding = _generate_demo_embedding(summary_text)

        db_summary = EventSummary(
            event_id=event.id,
            summary_text=summary_text,
            operational_context=enriched_data,
            embedding=embedding,
        )
        db.add(db_summary)

        event.is_processed = True
        db.commit()
    except Exception as e:
        print(f"Error processing event {event_id}: {e}")
        db.rollback()
    finally:
        db.close()
