from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import numpy as np
from db.database import get_db
from db.models import InfrastructureEvent, EventSummary

router = APIRouter()


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _event_to_dict(event: InfrastructureEvent, summary: EventSummary = None, similarity: float = None) -> dict:
    d = {
        "id": event.id,
        "event_type": event.event_type,
        "source": event.source,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "is_processed": event.is_processed,
        "status": event.status,
        "severity": event.severity,
        "failure_reason": event.failure_reason,
        "summary": summary.summary_text if summary else None,
        "operational_context": summary.operational_context if summary else None,
    }
    if similarity is not None:
        d["similarity"] = similarity
    return d


@router.get("/", response_model=List[dict])
async def search_events(
    q: Optional[str] = Query(None, description="Natural language search query"),
    limit: int = Query(10, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    if q:
        hash_obj = hash(q)
        np.random.seed(abs(hash_obj) % 2**32)
        query_embedding = np.random.rand(768).tolist()

        summaries = db.query(EventSummary).filter(
            EventSummary.embedding.isnot(None)
        ).all()

        scored = []
        for s in summaries:
            try:
                emb = json.loads(s.embedding)
                sim = cosine_similarity(query_embedding, emb)
                scored.append((sim, s))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue

        scored.sort(key=lambda x: x[0], reverse=True)
        scored = scored[:limit]

        events = []
        for sim, s in scored:
            event = db.query(InfrastructureEvent).filter(
                InfrastructureEvent.id == s.event_id
            ).first()
            if event:
                events.append(_event_to_dict(event, s, sim))
        return events
    else:
        events = db.query(InfrastructureEvent).order_by(
            InfrastructureEvent.timestamp.desc()
        ).limit(limit).all()
        return [_event_to_dict(e) for e in events]


@router.get("/similar/{event_id}", response_model=List[dict])
async def get_similar_events(
    event_id: int,
    limit: int = Query(5, description="Number of similar events to return"),
    db: Session = Depends(get_db)
):
    event_summary = db.query(EventSummary).filter(EventSummary.event_id == event_id).first()
    if not event_summary:
        raise HTTPException(status_code=404, detail="Event summary not found")

    if not event_summary.embedding:
        raise HTTPException(status_code=400, detail="Event summary has no embedding")

    try:
        target_emb = json.loads(event_summary.embedding)
    except (json.JSONDecodeError, TypeError, ValueError):
        raise HTTPException(status_code=500, detail="Invalid embedding format")

    summaries = db.query(EventSummary).filter(
        EventSummary.event_id != event_id,
        EventSummary.embedding.isnot(None)
    ).all()

    scored = []
    for s in summaries:
        try:
            emb = json.loads(s.embedding)
            sim = cosine_similarity(target_emb, emb)
            scored.append((sim, s))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

    scored.sort(key=lambda x: x[0], reverse=True)
    scored = scored[:limit]

    events = []
    for sim, s in scored:
        event = db.query(InfrastructureEvent).filter(
            InfrastructureEvent.id == s.event_id
        ).first()
        if event:
            events.append(_event_to_dict(event, s, sim))
    return events


@router.get("/ask")
async def ask_question(
    q: str = Query(..., description="Natural language question about infrastructure"),
    db: Session = Depends(get_db)
):
    from ai_layer.explainer import OperationalExplainer
    import httpx

    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code != 200:
            return {"answer": None, "ai_available": False, "message": "Ollama not running. Start it with: ollama serve"}
    except Exception:
        return {"answer": None, "ai_available": False, "message": "Ollama not running. Start it with: ollama serve"}

    explainer = OperationalExplainer(model_name="phi")
    events = db.query(InfrastructureEvent).order_by(
        InfrastructureEvent.timestamp.desc()
    ).limit(10).all()

    summaries = []
    for ev in events:
        s = db.query(EventSummary).filter(EventSummary.event_id == ev.id).first()
        if s:
            summaries.append({
                "id": ev.id,
                "event_type": ev.event_type,
                "source": ev.source,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "status": ev.status,
                "severity": ev.severity,
                "summary": s.summary_text,
                "operational_context": s.operational_context,
            })

    answer = explainer.answer_question(q, summaries)
    return {"answer": answer, "ai_available": True, "events_used": len(summaries)}
