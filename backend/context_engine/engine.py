import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import InfrastructureEvent, EventSummary, Deployment, Service
import json

class OperationalContextEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Operational context engine initialized")

    def enrich_event(self, normalized_event: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Enrich a normalized infrastructure event with operational context.
        This is the core differentiator of OpsEcho.
        """
        try:
            # Start with the normalized event
            enriched = normalized_event.copy()
            
            # Add deployment history
            deployment_history = self._get_deployment_history(normalized_event)
            enriched["deployment_history"] = deployment_history
            
            # Add related incidents
            related_incidents = self._get_related_incidents(normalized_event)
            enriched["related_incidents"] = related_incidents
            
            # Add dependency relationships
            dependencies = self._get_service_dependencies(normalized_event)
            enriched["dependencies"] = dependencies
            
            # Add previous failures
            previous_failures = self._get_previous_failures(normalized_event)
            enriched["previous_failures"] = previous_failures
            
            # Add service ownership
            ownership = self._get_service_ownership(normalized_event)
            enriched["ownership"] = ownership
            
            # Add historical patterns
            historical_patterns = self._get_historical_patterns(normalized_event)
            enriched["historical_patterns"] = historical_patterns
            
            # Add infrastructure correlations
            correlations = self._get_infrastructure_correlations(normalized_event)
            enriched["correlations"] = correlations
            
            # Add enrichment timestamp
            enriched["enriched_at"] = datetime.now(timezone.utc).isoformat()
            
            return enriched
            
        except Exception as e:
            self.logger.error(f"Error enriching event: {e}")
            # Return the normalized event with error info
            normalized_event["enrichment_error"] = str(e)
            return normalized_event

    def _get_deployment_history(self, event: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        """
        Get deployment history related to this event.
        """
        try:
            db = SessionLocal()
            # Look for deployments in the same service/namespace around the same time
            # This is a simplified implementation
            deployments = db.query(Deployment).filter(
                Deployment.timestamp >= datetime.now(timezone.utc) - timedelta(days=7)
            ).limit(10).all()
            
            history = []
            for deploy in deployments:
                history.append({
                    "id": deploy.id,
                    "deployment_id": deploy.deployment_id,
                    "service_name": deploy.service_name,
                    "environment": deploy.environment,
                    "status": deploy.status,
                    "timestamp": deploy.timestamp.isoformat() if deploy.timestamp else None
                })
            
            db.close()
            return history
        except Exception as e:
            self.logger.error(f"Error getting deployment history: {e}")
            return []

    def _get_related_incidents(self, event: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        """
        Get incidents related to this event.
        In a full implementation, this would connect to incident management systems.
        For MVP, we'll look for similar events that had issues.
        """
        try:
            db = SessionLocal()
            # Look for events of the same type that occurred recently and might be related
            # This is a placeholder - in reality, you'd have an incidents table
            events = db.query(InfrastructureEvent).filter(
                InfrastructureEvent.event_type == event.get("event_type"),
                InfrastructureEvent.timestamp >= datetime.now(timezone.utc) - timedelta(days=30)
            ).limit(5).all()
            
            incidents = []
            for ev in events:
                # In a real system, you'd check if this event was marked as an incident
                incidents.append({
                    "event_id": ev.id,
                    "event_type": ev.event_type,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "source": ev.source,
                    "note": "Placeholder - would be linked to actual incident system"
                })
            
            db.close()
            return incidents
        except Exception as e:
            self.logger.error(f"Error getting related incidents: {e}")
            return []

    def _get_service_dependencies(self, event: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        """
        Get service dependencies for services affected by this event.
        """
        try:
            db = SessionLocal()
            # Extract service name from event
            service_name = self._extract_service_name(event)
            if not service_name:
                db.close()
                return []
            
            # Find the service and its dependencies
            service = db.query(Service).filter(Service.name == service_name).first()
            if not service:
                db.close()
                return []
            
            dependencies = []
            if service.dependencies:
                for dep_name in service.dependencies:
                    dep_service = db.query(Service).filter(Service.name == dep_name).first()
                    if dep_service:
                        dependencies.append({
                            "name": dep_service.name,
                            "ownership": dep_service.ownership,
                            "metadata": dep_service.service_metadata
                        })
            
            db.close()
            return dependencies
        except Exception as e:
            self.logger.error(f"Error getting service dependencies: {e}")
            return []

    def _get_previous_failures(self, event: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        """
        Get previous failures related to this event.
        """
        try:
            db = SessionLocal()
            similar_events = db.query(InfrastructureEvent).filter(
                InfrastructureEvent.event_type == event.get("event_type"),
                InfrastructureEvent.status.in_(["failed", "degraded"])
            ).limit(5).all()

            failures = []
            for ev in similar_events:
                failures.append({
                    "event_id": ev.id,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "failure_type": ev.failure_reason or ev.status or "unknown",
                    "severity": ev.severity,
                })

            db.close()
            return failures
        except Exception as e:
            self.logger.error(f"Error getting previous failures: {e}")
            return []

    def _get_service_ownership(self, event: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Get ownership information for services affected by this event.
        """
        try:
            db = SessionLocal()
            service_name = self._extract_service_name(event)
            if not service_name:
                db.close()
                return {}
            
            service = db.query(Service).filter(Service.name == service_name).first()
            if not service:
                db.close()
                return {"service": service_name, "ownership": "unknown"}
            
            ownership_info = {
                "service": service.name,
                "ownership": service.ownership,
                "metadata": service.service_metadata
            }

            db.close()
            return ownership_info
        except Exception as e:
            self.logger.error(f"Error getting service ownership: {e}")
            return {"service": "unknown", "ownership": "unknown"}

    def _get_historical_patterns(self, event: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Get historical patterns for similar events.
        """
        try:
            db = SessionLocal()
            # Look for patterns in similar events over time
            event_type = event.get("event_type")
            source = event.get("source")
            
            # Get events of same type from same source over last 90 days
            pattern_events = db.query(InfrastructureEvent).filter(
                InfrastructureEvent.event_type == event_type,
                InfrastructureEvent.source == source,
                InfrastructureEvent.timestamp >= datetime.now(timezone.utc) - timedelta(days=90)
            ).all()
            
            # Calculate simple patterns
            patterns = {
                "total_similar_events": len(pattern_events),
                "frequency_per_week": len(pattern_events) / (90/7) if len(pattern_events) > 0 else 0,
                "recent_trend": "stable"  # Placeholder
            }
            
            # Analyze timestamps for patterns (simplified)
            if len(pattern_events) >= 2:
                timestamps = [ev.timestamp for ev in pattern_events if ev.timestamp]
                if len(timestamps) >= 2:
                    # Sort by timestamp
                    timestamps.sort()
                    # Calculate average time between events
                    if len(timestamps) > 1:
                        diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                                for i in range(len(timestamps)-1)]
                        avg_diff = sum(diffs) / len(diffs) if diffs else 0
                        patterns["average_interval_hours"] = avg_diff / 3600
            
            db.close()
            return patterns
        except Exception as e:
            self.logger.error(f"Error getting historical patterns: {e}")
            return {}

    def _get_infrastructure_correlations(self, event: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        """
        Get infrastructure correlations - what other infrastructure changes happened around the same time.
        """
        try:
            db = SessionLocal()
            # Look for other infrastructure events in the same time window
            event_time = datetime.fromisoformat(event.get("timestamp").replace("Z", "+00:00")) if isinstance(event.get("timestamp"), str) else event.get("timestamp")
            if not event_time:
                event_time = datetime.now(timezone.utc)
            
            time_window = timedelta(hours=2)  # Look 2 hours before and after
            
            correlated_events = db.query(InfrastructureEvent).filter(
                InfrastructureEvent.timestamp >= event_time - time_window,
                InfrastructureEvent.timestamp <= event_time + time_window,
                InfrastructureEvent.id != event.get("id")  # Exclude the event itself
            ).limit(10).all()
            
            correlations = []
            for ev in correlated_events:
                correlations.append({
                    "event_id": ev.id,
                    "event_type": ev.event_type,
                    "source": ev.source,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "time_diff_minutes": ((ev.timestamp - event_time).total_seconds() / 60) if ev.timestamp else None
                })
            
            db.close()
            return correlations
        except Exception as e:
            self.logger.error(f"Error getting infrastructure correlations: {e}")
            return []

    def _extract_service_name(self, event: Dict[Any, Any]) -> str:
        """
        Extract service name from an event.
        This is a simplified implementation - in reality, you'd have more sophisticated logic.
        """
        try:
            # Try to get from normalized data first
            normalized = event.get("normalized_data", {})
            if isinstance(normalized, str):
                normalized = json.loads(normalized)
            
            # Different extraction logic based on event type
            event_type = event.get("event_type")
            
            if event_type == "kubernetes":
                # For K8s, look for app labels or service names
                raw_data = event.get("raw_data", {})
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                # Try to get from labels or annotations
                resource_kind = raw_data.get("kind") or raw_data.get("type")
                if resource_kind == "Pod":
                    # In a real system, you'd extract from pod labels
                    return raw_data.get("name", "").split("-")[0] if "-" in raw_data.get("name", "") else raw_data.get("name", "unknown")
                elif resource_kind == "Deployment":
                    return raw_data.get("name", "unknown")
                    
            elif event_type == "terraform":
                # For Terraform, look for resource names that indicate services
                raw_data = event.get("raw_data", {})
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                changes = raw_data.get("changes", {})
                created = changes.get("create", [])
                updated = changes.get("update", [])
                
                # Look for service-like resources
                all_resources = created + updated
                for resource in all_resources:
                    if any(keyword in resource.lower() for keyword in ["service", "app", "web", "api"]):
                        return resource
                
                # Fallback to first resource
                if all_resources:
                    return all_resources[0]
                    
            elif event_type == "git":
                # For Git, look at repository name or modified files
                raw_data = event.get("raw_data", {})
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                repo_name = raw_data.get("repository", {}).get("name", "unknown")
                return repo_name
                
            elif event_type == "ci_cd":
                # For CI/CD, look at the pipeline or service being deployed
                raw_data = event.get("raw_data", {})
                if isinstance(raw_data, str):
                    raw_data = json.loads(raw_data)
                
                return raw_data.get("service", raw_data.get("pipeline", "unknown"))
            
            # Default fallback
            return event.get("source", "unknown")
            
        except Exception as e:
            self.logger.error(f"Error extracting service name: {e}")
            return "unknown"

# For testing
if __name__ == "__main__":
    engine = OperationalContextEngine()
    
    # Test event
    test_event = {
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
            "status": "Running",
            "action": "running"
        }
    }
    
    enriched = engine.enrich_event(test_event)
    print("Enriched event:")
    print(f"  Deployment history: {len(enriched.get('deployment_history', []))} items")
    print(f"  Related incidents: {len(enriched.get('related_incidents', []))} items")
    print(f"  Dependencies: {len(enriched.get('dependencies', []))} items")
    print(f"  Ownership: {enriched.get('ownership', {})}")