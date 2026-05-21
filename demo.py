#!/usr/bin/env python3
"""
Demo script to show OpsEcho components working together
This demonstrates the core functionality without requiring external services
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from db.models import Base, InfrastructureEvent, EventSummary
from db.database import engine, SessionLocal
from normalization.engine import NormalizationEngine
from context_engine.engine import OperationalContextEngine
from ai_layer.explainer import OperationalExplainer
import json
from datetime import datetime

def demo_components():
    print("=" * 60)
    print("OpsEcho Component Demonstration")
    print("=" * 60)
    
    # Create database tables
    print("\n1. Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✓ Tables created")
    
    # Initialize components
    print("\n2. Initializing components...")
    normalization_engine = NormalizationEngine()
    context_engine = OperationalContextEngine()
    # Note: We won't actually call Ollama in this demo to avoid external dependencies
    # explainer = OperationalExplainer()  # This would require Ollama running
    print("   ✓ Components initialized")
    
    # Create a sample infrastructure event
    print("\n3. Processing sample Kubernetes event...")
    sample_event = {
        "id": 1,
        "event_type": "kubernetes",
        "source": "kubernetes",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_data": {
            "type": "Pod",
            "name": "web-api-7d6f8c4b9-abcde",
            "namespace": "production",
            "status": "Running",
            "reason": "New pod created"
        }
    }
    
    # Normalize the event
    print("   Normalizing event...")
    normalized = normalization_engine.normalize_event(sample_event)
    print(f"   ✓ Normalized: {normalized.get('kind')} {normalized.get('name')} in {normalized.get('namespace')}")
    
    # Enrich with context
    print("   Enriching with operational context...")
    enriched = context_engine.enrich_event({
        "event_type": sample_event["event_type"],
        "source": sample_event["source"],
        "timestamp": sample_event["timestamp"],
        "raw_data": sample_event["raw_data"],
        "normalized_data": normalized
    })
    print(f"   ✓ Enriched with {len(enriched.get('deployment_history', []))} deployment history items")
    print(f"   ✓ Ownership: {enriched.get('ownership', {}).get('ownership', 'unknown')}")
    
    # Generate a mock summary (without calling Ollama)
    print("   Generating operational summary...")
    mock_summary = f"""The web-api pod was created in the production namespace.

Likely reason:
Deployment of new version v2.1.0 triggered by CI/CD pipeline.

Potential impact:
- Increased capacity for handling user traffic
- Updated application with latest features

Related history:
Similar deployment pattern observed 3 days ago during feature release."""
    
    print("   ✓ Summary generated")
    print("\n4. Sample Output:")
    print("-" * 40)
    print(f"Event: {enriched.get('event_type')} from {enriched.get('source')}")
    print(f"Time: {enriched.get('timestamp')}")
    print(f"Summary:\n{mock_summary}")
    print("-" * 40)
    
    # Show what would be stored in database
    print("\n5. What gets stored in the database:")
    print("   Infrastructure Events Table:")
    print(f"     - ID: {sample_event['id']}")
    print(f"     - Type: {sample_event['event_type']}")
    print(f"     - Source: {sample_event['event_type']}")
    print(f"     - Timestamp: {sample_event['timestamp']}")
    print("   Event Summaries Table:")
    print(f"     - Summary text: [Generated AI summary]")
    print(f"     - Operational context: [Enriched JSON]")
    print(f"     - Embedding: [Vector for semantic search]")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTo run the full system with Docker:")
    print("1. Install Docker and Docker Compose")
    print("2. Run: docker-compose up --build")
    print("3. Access: http://localhost:3000 (frontend)")
    print("4. API: http://localhost:8000/docs")

if __name__ == "__main__":
    demo_components()