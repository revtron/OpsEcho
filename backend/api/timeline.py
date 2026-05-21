from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from db.database import get_db
from db.models import InfrastructureEvent, EventSummary

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_timeline(
    hours: int = Query(24, description="Number of hours to look back"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
):
    """
    Get a timeline of infrastructure events.
    """
    # Calculate the time window
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Build the query
    query = db.query(InfrastructureEvent).filter(
        InfrastructureEvent.timestamp >= since
    )
    
    if event_type:
        query = query.filter(InfrastructureEvent.event_type == event_type)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(InfrastructureEvent.timestamp.desc()).limit(limit)
    
    events = query.all()
    
    # Format the response
    result = []
    for event in events:
        # Get the summary if available
        summary = db.query(EventSummary).filter(EventSummary.event_id == event.id).first()
        
        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "is_processed": event.is_processed,
            "summary": summary.summary_text if summary else None,
            "operational_context": summary.operational_context if summary else None
        })
    
    return result