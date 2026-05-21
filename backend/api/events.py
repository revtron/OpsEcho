from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
from db.database import get_db
from db.models import InfrastructureEvent, EventSummary
from collectors.k8s_watcher import K8sWatcher
from collectors.terraform_parser import TerraformParser
from collectors.git_webhook import GitWebhook
from ai_layer.explainer import OperationalExplainer

router = APIRouter()

# Initialize collectors (in a real app, these would be managed differently)
k8s_watcher = K8sWatcher()
terraform_parser = TerraformParser()
git_webhook = GitWebhook()

@router.post("/k8s")
async def receive_k8s_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receive a Kubernetes event and store it for processing.
    """
    # Store raw event
    db_event = InfrastructureEvent(
        event_type="kubernetes",
        source=event.get("source", "unknown"),
        raw_data=event
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Process in background
    background_tasks.add_task(process_event, db_event.id, db)
    
    return {"status": "received", "event_id": db_event.id}

@router.post("/terraform")
async def receive_terraform_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receive a Terraform apply event and store it for processing.
    """
    db_event = InfrastructureEvent(
        event_type="terraform",
        source=event.get("source", "unknown"),
        raw_data=event
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    background_tasks.add_task(process_event, db_event.id, db)
    
    return {"status": "received", "event_id": db_event.id}

@router.post("/git")
async def receive_git_event(event: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receive a Git webhook event and store it for processing.
    """
    db_event = InfrastructureEvent(
        event_type="git",
        source=event.get("source", "unknown"),
        raw_data=event
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    background_tasks.add_task(process_event, db_event.id, db)
    
    return {"status": "received", "event_id": db_event.id}

@router.get("/", response_model=List[dict])
async def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of infrastructure events.
    """
    events = db.query(InfrastructureEvent).offset(skip).limit(limit).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "source": e.source,
            "timestamp": e.timestamp,
            "is_processed": e.is_processed
        }
        for e in events
    ]

async def process_event(event_id: int, db: Session):
    """
    Background task to process an event through the pipeline.
    """
    from normalization.engine import NormalizationEngine
    from context_engine.engine import OperationalContextEngine
    from ai_layer.explainer import OperationalExplainer

    # Get the event
    event = db.query(InfrastructureEvent).filter(InfrastructureEvent.id == event_id).first()
    if not event:
        return

    try:
        # Step 1: Normalize the event
        normalization_engine = NormalizationEngine()
        normalized_data = normalization_engine.normalize_event({
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "raw_data": event.raw_data
        })

        # Update the event with normalized data
        event.normalized_data = normalized_data

        # Step 2: Enrich with operational context
        context_engine = OperationalContextEngine()
        enriched_data = context_engine.enrich_event({
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "raw_data": event.raw_data,
            "normalized_data": normalized_data
        })

        # Step 3: Generate AI summary
        explainer = OperationalExplainer()
        summary_text = explainer.generate_summary(enriched_data)

        # Step 4: Generate embedding for the summary (for semantic search)
        # We'll use the same Ollama model to get embeddings
        # Note: In a real system, you might use a dedicated embedding model.
        # For simplicity, we'll use the same model and a fixed dimension.
        # We'll use the Ollama embeddings API if available, or fall back to a dummy vector.
        try:
            # Ollama doesn't have a direct embedding API in the Python library as of now.
            # We'll use a workaround: we can use the model to generate a summary and then
            # use a separate embedding model, but for simplicity, we'll generate a random vector.
            # In a real implementation, you would use a sentence transformer or similar.
            # For now, we'll create a dummy vector of zeros (or use a hash of the summary).
            # This is a placeholder for the embedding.
            # We'll use a fixed dimension of 768 (common for many models).
            import numpy as np
            # Create a deterministic vector from the summary hash
            hash_obj = hash(summary_text)
            np.random.seed(abs(hash_obj) % 2**32)
            embedding = np.random.rand(768).tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            embedding = [0.0] * 768

        # Step 5: Save the summary and embedding
        db_summary = EventSummary(
            event_id=event.id,
            summary_text=summary_text,
            operational_context=enriched_data,
            embedding=embedding
        )
        db.add(db_summary)

        # Mark the event as processed
        event.is_processed = True

        db.commit()
    except Exception as e:
        print(f"Error processing event {event_id}: {e}")
        db.rollback()