from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from db.database import get_db
from db.models import InfrastructureEvent, EventSummary
from ai_layer.explainer import OperationalExplainer
import numpy as np

router = APIRouter()

@router.get("/", response_model=List[dict])
async def search_events(
    q: Optional[str] = Query(None, description="Natural language search query"),
    limit: int = Query(10, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search for infrastructure events using natural language.
    If a query is provided, uses semantic search via embeddings.
    Otherwise, returns recent events.
    """
    if q:
        # Semantic search: generate embedding for the query and find similar summaries
        explainer = OperationalExplainer()
        try:
            # Generate embedding for the query
            # We'll use the same method as in event processing: create a deterministic vector
            # In a real system, you would use the same embedding model for consistency.
            hash_obj = hash(q)
            np.random.seed(abs(hash_obj) % 2**32)
            query_embedding = np.random.rand(768).tolist()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating query embedding: {str(e)}")

        # Use pgvector to find similar embeddings
        # We'll use the cosine similarity (or L2 distance) provided by pgvector
        # For simplicity, we'll do a raw SQL query. In a real app, you might use SQLAlchemy with pgvector extension.
        from sqlalchemy import text
        sql = text("""
            SELECT e.id, e.event_type, e.source, e.timestamp, es.summary_text, es.operational_context,
                   1 - (es.embedding <=> :query_embedding) AS similarity
            FROM event_summaries es
            JOIN infrastructure_events e ON es.event_id = e.id
            WHERE es.embedding IS NOT NULL
            ORDER BY es.embedding <=> :query_embedding
            LIMIT :limit
        """)
        results = db.execute(sql, {
            "query_embedding": query_embedding,
            "limit": limit
        }).fetchall()

        # Format the results
        events = []
        for row in results:
            events.append({
                "id": row.id,
                "event_type": row.event_type,
                "source": row.source,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "summary": row.summary_text,
                "operational_context": row.operational_context,
                "similarity": float(row.similarity)
            })
        return events
    else:
        # Return recent events
        events = db.query(InfrastructureEvent).order_by(
            InfrastructureEvent.timestamp.desc()
        ).limit(limit).all()
        return [
            {
                "id": e.id,
                "event_type": e.event_type,
                "source": e.source,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "is_processed": e.is_processed
            }
            for e in events
        ]

@router.get("/similar/{event_id}", response_model=List[dict])
async def get_similar_events(
    event_id: int,
    limit: int = Query(5, description="Number of similar events to return"),
    db: Session = Depends(get_db)
):
    """
    Find events similar to a given event based on their summaries.
    """
    # Get the event's summary
    event_summary = db.query(EventSummary).filter(EventSummary.event_id == event_id).first()
    if not event_summary:
        raise HTTPException(status_code=404, detail="Event summary not found")

    if not event_summary.embedding:
        raise HTTPException(status_code=400, detail="Event summary has no embedding")

    # Use pgvector to find similar embeddings
    from sqlalchemy import text
    sql = text("""
        SELECT e.id, e.event_type, e.source, e.timestamp, es.summary_text,
               1 - (es.embedding <=> :event_embedding) AS similarity
        FROM event_summaries es
        JOIN infrastructure_events e ON es.event_id = e.id
        WHERE es.event_id != :event_id
        ORDER BY es.embedding <=> :event_embedding
        LIMIT :limit
    """)
    results = db.execute(sql, {
        "event_embedding": event_summary.embedding,
        "event_id": event_id,
        "limit": limit
    }).fetchall()

    # Format the results
    events = []
    for row in results:
        events.append({
            "id": row.id,
            "event_type": row.event_type,
            "source": row.source,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "summary": row.summary_text,
            "similarity": float(row.similarity)
        })
    return events