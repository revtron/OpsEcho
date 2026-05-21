import logging
from typing import Dict, Any
from datetime import datetime

class NormalizationEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Normalization engine initialized")

    def normalize_event(self, raw_event: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Normalize raw infrastructure events into a common format.
        """
        try:
            event_type = raw_event.get("event_type", "unknown")
            
            # Start with basic normalized structure
            normalized = {
                "id": raw_event.get("id"),
                "event_type": event_type,
                "timestamp": raw_event.get("timestamp") or datetime.utcnow().isoformat(),
                "source": raw_event.get("source", "unknown"),
                "raw_data": raw_event.get("raw_data", {}),
                "normalized_at": datetime.utcnow().isoformat()
            }
            
            # Type-specific normalization
            if event_type == "kubernetes":
                normalized.update(self._normalize_k8s_event(raw_event.get("raw_data", {})))
            elif event_type == "terraform":
                normalized.update(self._normalize_terraform_event(raw_event.get("raw_data", {})))
            elif event_type == "git":
                normalized.update(self._normalize_git_event(raw_event.get("raw_data", {})))
            elif event_type == "ci_cd":
                normalized.update(self._normalize_cicd_event(raw_event.get("raw_data", {})))
            elif event_type == "docker":
                normalized.update(self._normalize_docker_event(raw_event.get("raw_data", {})))
            elif event_type == "aws":
                normalized.update(self._normalize_aws_event(raw_event.get("raw_data", {})))
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing event: {e}")
            # Return basic normalization even on error
            return {
                "id": raw_event.get("id"),
                "event_type": raw_event.get("event_type", "unknown"),
                "timestamp": raw_event.get("timestamp") or datetime.utcnow().isoformat(),
                "source": raw_event.get("source", "unknown"),
                "raw_data": raw_event.get("raw_data", {}),
                "normalized_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    def _normalize_k8s_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize Kubernetes events."""
        normalized = {}
        
        # Handle different K8s event types
        if raw_data.get("type") == "Pod":
            normalized.update({
                "kind": "Pod",
                "name": raw_data.get("name"),
                "namespace": raw_data.get("namespace"),
                "status": raw_data.get("status"),
                "action": self._determine_k8s_action(raw_data)
            })
        elif raw_data.get("type") == "Deployment":
            normalized.update({
                "kind": "Deployment",
                "name": raw_data.get("name"),
                "namespace": raw_data.get("namespace"),
                "replicas": raw_data.get("replicas"),
                "available_replicas": raw_data.get("available_replicas"),
                "action": self._determine_k8s_action(raw_data)
            })
        else:
            normalized.update({
                "kind": raw_data.get("type", "Unknown"),
                "name": raw_data.get("name", "unknown"),
                "namespace": raw_data.get("namespace", "default"),
                "action": "unknown"
            })
            
        return normalized

    def _normalize_terraform_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize Terraform events."""
        normalized = {}
        
        # Extract Terraform-specific information
        if "changes" in raw_data:
            changes = raw_data["changes"]
            normalized.update({
                "action": "terraform_apply",
                "resources_created": len(changes.get("create", [])),
                "resources_updated": len(changes.get("update", [])),
                "resources_deleted": len(changes.get("delete", [])),
                "changes_summary": changes
            })
        else:
            normalized.update({
                "action": "terraform_unknown",
                "changes_summary": raw_data
            })
            
        return normalized

    def _normalize_git_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize Git events."""
        normalized = {}
        
        event_type = raw_data.get("event_type", "")
        if event_type == "push":
            normalized.update({
                "action": "git_push",
                "branch": raw_data.get("branch"),
                "commit_count": raw_data.get("total_commits", 0),
                "repository": raw_data.get("repository", {}).get("name", "unknown")
            })
        elif event_type == "pull_request":
            pr = raw_data.get("pull_request", {})
            normalized.update({
                "action": f"git_pull_request_{raw_data.get('action', 'unknown')}",
                "pr_number": pr.get("number"),
                "pr_title": pr.get("title"),
                "repository": raw_data.get("repository", {}).get("name", "unknown")
            })
        else:
            normalized.update({
                "action": "git_unknown",
                "event_type": event_type
            })
            
        return normalized

    def _normalize_cicd_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize CI/CD events."""
        normalized = {}
        
        normalized.update({
            "action": raw_data.get("action", "unknown"),
            "pipeline": raw_data.get("pipeline", "unknown"),
            "status": raw_data.get("status", "unknown"),
            "duration": raw_data.get("duration"),
            "commit": raw_data.get("commit")
        })
        
        return normalized

    def _normalize_docker_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize Docker events."""
        normalized = {}
        
        normalized.update({
            "action": raw_data.get("action", "unknown"),
            "container_id": raw_data.get("id"),
            "image": raw_data.get("image"),
            "status": raw_data.get("status")
        })
        
        return normalized

    def _normalize_aws_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Normalize AWS events."""
        normalized = {}
        
        normalized.update({
            "action": raw_data.get("eventName", "unknown"),
            "resource_type": raw_data.get("resources", [{}])[0].get("type") if raw_data.get("resources") else "unknown",
            "resource_id": raw_data.get("resources", [{}])[0].get("ARN") if raw_data.get("resources") else "unknown",
            "region": raw_data.get("region"),
            "source_ip": raw_data.get("sourceIPAddress")
        })
        
        return normalized

    def _determine_k8s_action(self, raw_data: Dict[Any, Any]) -> str:
        """Determine the action type for a Kubernetes event."""
        status = raw_data.get("status", "").lower()
        if status in ["running", "succeeded"]:
            return "created" if raw_data.get("timestamp") else "running"
        elif status in ["failed", "error"]:
            return "failed"
        elif status == "pending":
            return "pending"
        elif status in ["completed", "succeeded"]:
            return "completed"
        else:
            return "updated"

# For testing
if __name__ == "__main__":
    engine = NormalizationEngine()
    
    # Test K8s event
    k8s_event = {
        "event_type": "kubernetes",
        "source": "kubernetes",
        "raw_data": {
            "type": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
            "namespace": "production",
            "status": "Running",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }
    
    normalized = engine.normalize_event(k8s_event)
    print("Normalized K8s event:")
    print(f"  Kind: {normalized.get('kind')}")
    print(f"  Name: {normalized.get('name')}")
    print(f"  Namespace: {normalized.get('namespace')}")
    print(f"  Status: {normalized.get('status')}")
    print(f"  Action: {normalized.get('action')}")