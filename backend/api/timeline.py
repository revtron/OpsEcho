from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from db.database import get_db
from db.models import InfrastructureEvent, EventSummary

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_timeline(
    hours: int = Query(24, description="Number of hours to look back"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status (healthy, degraded, failed, pending, unknown)"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)"),
    limit: int = Query(100, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = db.query(InfrastructureEvent).filter(
        InfrastructureEvent.timestamp >= since
    )

    if event_type:
        query = query.filter(InfrastructureEvent.event_type == event_type)
    if status:
        query = query.filter(InfrastructureEvent.status == status)
    if severity:
        query = query.filter(InfrastructureEvent.severity == severity)

    query = query.order_by(InfrastructureEvent.timestamp.desc()).limit(limit)

    events = query.all()

    result = []
    for event in events:
        summary = db.query(EventSummary).filter(EventSummary.event_id == event.id).first()

        resource = None
        if event.normalized_data and isinstance(event.normalized_data, dict):
            nd = event.normalized_data
            resource = {
                "kind": nd.get("kind"),
                "name": nd.get("name"),
                "namespace": nd.get("namespace"),
                "phase": nd.get("phase"),
                "replicas": nd.get("replicas"),
                "available_replicas": nd.get("available_replicas"),
                "restart_count": nd.get("restart_count", 0),
                "instance_id": nd.get("instance_id"),
                "instance_type": nd.get("instance_type"),
                "state": nd.get("state"),
                "status_check": nd.get("status_check"),
                "system_status_check": nd.get("system_status_check"),
                "private_ip": nd.get("private_ip"),
                "public_ip": nd.get("public_ip"),
                "region": nd.get("region"),
                "vpc_id": nd.get("vpc_id"),
                "events": nd.get("events"),
            }

        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "is_processed": event.is_processed,
            "status": event.status,
            "severity": event.severity,
            "failure_reason": event.failure_reason,
            "resource": resource,
            "summary": summary.summary_text if summary else None,
            "operational_context": summary.operational_context if summary else None,
        })

    return result
