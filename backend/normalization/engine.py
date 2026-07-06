import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

# Known Kubernetes failure reasons and their severities
K8S_FAILURE_REASONS = {
    "CrashLoopBackOff": "critical",
    "ImagePullBackOff": "warning",
    "ErrImagePull": "warning",
    "ErrImageNeverPull": "warning",
    "OOMKill": "critical",
    "OOMKilling": "critical",
    "OutOfMemory": "critical",
    "NodeNotReady": "critical",
    "NodeWithUnhealthy": "critical",
    "ProbeError": "warning",
    "ReadinessProbeFailed": "warning",
    "LivenessProbeFailed": "critical",
    "StartupProbeFailed": "critical",
    "ContainerCreating": "info",
    "PodInitializing": "info",
    "Evicted": "warning",
    "NodeAffinity": "warning",
    "Unschedulable": "warning",
    "InsufficientMemory": "warning",
    "InsufficientCPU": "warning",
    "InsufficientResources": "warning",
}

SEVERITY_ORDER = {"critical": 3, "warning": 2, "info": 1}


class NormalizationEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Normalization engine initialized")

    def normalize_event(self, raw_event: Dict[Any, Any]) -> Dict[Any, Any]:
        try:
            event_type = raw_event.get("event_type", "unknown")

            normalized = {
                "id": raw_event.get("id"),
                "event_type": event_type,
                "timestamp": raw_event.get("timestamp") or datetime.utcnow().isoformat(),
                "source": raw_event.get("source", "unknown"),
                "raw_data": raw_event.get("raw_data", {}),
                "normalized_at": datetime.utcnow().isoformat(),
                "status": "unknown",
                "severity": "info",
                "failure_reason": None,
            }

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
            elif event_type == "ec2":
                normalized.update(self._normalize_ec2_event(raw_event.get("raw_data", {})))

            return normalized

        except Exception as e:
            self.logger.error(f"Error normalizing event: {e}")
            return {
                "id": raw_event.get("id"),
                "event_type": raw_event.get("event_type", "unknown"),
                "timestamp": raw_event.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "source": raw_event.get("source", "unknown"),
                "raw_data": raw_event.get("raw_data", {}),
                "normalized_at": datetime.now(timezone.utc).isoformat(),
                "status": "unknown",
                "severity": "info",
                "failure_reason": None,
                "error": str(e),
            }

    def _determine_k8s_status(
        self, raw_data: Dict[Any, Any]
    ) -> Tuple[str, str, str]:
        """Determine status, severity, and failure_reason for a K8s event."""
        phase = raw_data.get("status", "").lower()
        reason = raw_data.get("reason", "")
        available = raw_data.get("available_replicas")
        desired = raw_data.get("replicas")

        # Check for known failure reasons first
        if reason in K8S_FAILURE_REASONS:
            return "failed", K8S_FAILURE_REASONS[reason], reason

        # Check degraded deployment
        if (
            desired is not None
            and available is not None
            and desired > available
        ):
            return "degraded", "warning", f"Available replicas ({available}) < desired ({desired})"

        # Map phase to status/severity
        if phase in ["running", "succeeded", "completed"]:
            return "healthy", "info", None
        elif phase in ["failed", "error"]:
            return "failed", "critical", reason or phase
        elif phase == "pending":
            return "pending", "warning", reason or "pending"
        elif phase == "unknown":
            return "unknown", "warning", "unknown phase"

        return "healthy", "info", None

    def _normalize_k8s_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        normalized = {}
        status, severity, failure_reason = self._determine_k8s_status(raw_data)

        normalized["status"] = status
        normalized["severity"] = severity
        normalized["failure_reason"] = failure_reason

        phase = raw_data.get("status", "Unknown")

        if raw_data.get("type") == "Pod":
            normalized.update({
                "kind": "Pod",
                "name": raw_data.get("name"),
                "namespace": raw_data.get("namespace"),
                "phase": phase,
                "action": self._determine_k8s_action(raw_data, status),
                "container_statuses": raw_data.get("container_statuses", []),
                "restart_count": raw_data.get("restart_count", 0),
            })
        elif raw_data.get("type") == "Deployment":
            normalized.update({
                "kind": "Deployment",
                "name": raw_data.get("name"),
                "namespace": raw_data.get("namespace"),
                "phase": phase,
                "replicas": raw_data.get("replicas"),
                "available_replicas": raw_data.get("available_replicas"),
                "action": self._determine_k8s_action(raw_data, status),
            })
        elif raw_data.get("type") == "Node":
            normalized.update({
                "kind": "Node",
                "name": raw_data.get("name"),
                "phase": phase,
                "action": self._determine_k8s_action(raw_data, status),
            })
        else:
            normalized.update({
                "kind": raw_data.get("type", "Unknown"),
                "name": raw_data.get("name", "unknown"),
                "namespace": raw_data.get("namespace", "default"),
                "action": "unknown",
            })

        return normalized

    def _determine_k8s_action(self, raw_data: Dict[Any, Any], status: str = None) -> str:
        if status == "failed":
            return "failed"
        if status == "degraded":
            return "degraded"
        phase = raw_data.get("status", "").lower()
        if phase in ["running", "succeeded"]:
            return "created" if raw_data.get("timestamp") else "running"
        elif phase == "pending":
            return "pending"
        elif phase in ["completed", "succeeded"]:
            return "completed"
        else:
            return "updated"

    def _normalize_terraform_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        normalized = {
            "status": "healthy",
            "severity": "info",
            "failure_reason": None,
        }

        if "error" in raw_data or "errors" in raw_data:
            error_msg = raw_data.get("error") or str(raw_data.get("errors", ""))
            normalized["status"] = "failed"
            normalized["severity"] = "critical"
            normalized["failure_reason"] = error_msg[:500]
            normalized["action"] = "terraform_failed"
            return normalized

        if "changes" in raw_data:
            changes = raw_data["changes"]
            normalized.update({
                "action": "terraform_apply",
                "resources_created": len(changes.get("create", [])),
                "resources_updated": len(changes.get("update", [])),
                "resources_deleted": len(changes.get("delete", [])),
                "changes_summary": changes,
            })
        else:
            normalized.update({
                "action": "terraform_unknown",
                "changes_summary": raw_data,
            })

        return normalized

    def _normalize_git_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        normalized = {
            "status": "healthy",
            "severity": "info",
            "failure_reason": None,
        }

        event_type = raw_data.get("event_type", "")
        if event_type == "push":
            normalized.update({
                "action": "git_push",
                "branch": raw_data.get("branch"),
                "commit_count": raw_data.get("total_commits", 0),
                "repository": raw_data.get("repository", {}).get("name", "unknown"),
            })
        elif event_type == "pull_request":
            pr = raw_data.get("pull_request", {})
            action = raw_data.get("action", "unknown")
            normalized.update({
                "action": f"git_pull_request_{action}",
                "pr_number": pr.get("number"),
                "pr_title": pr.get("title"),
                "repository": raw_data.get("repository", {}).get("name", "unknown"),
            })
        else:
            normalized.update({
                "action": "git_unknown",
                "event_type": event_type,
            })

        # Check for CI failures in commit/push messages
        if raw_data.get("ci_status") == "failure":
            normalized["status"] = "failed"
            normalized["severity"] = "warning"
            normalized["failure_reason"] = raw_data.get("ci_description", "CI pipeline failed")

        return normalized

    def _normalize_cicd_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        raw_status = raw_data.get("status", "unknown")
        if raw_status in ("failed", "failure", "error"):
            status, severity = "failed", "critical"
            reason = raw_data.get("reason") or raw_data.get("description") or "CI/CD pipeline failed"
        elif raw_status in ("unstable", "degraded"):
            status, severity = "degraded", "warning"
            reason = raw_data.get("reason") or "CI/CD pipeline unstable"
        else:
            status, severity = "healthy", "info"
            reason = None

        normalized = {
            "status": status,
            "severity": severity,
            "failure_reason": reason,
            "action": raw_data.get("action", "unknown"),
            "pipeline": raw_data.get("pipeline", "unknown"),
            "status": raw_status,
            "duration": raw_data.get("duration"),
            "commit": raw_data.get("commit"),
        }

        return normalized

    def _normalize_docker_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        action = raw_data.get("action", "unknown")
        docker_status = raw_data.get("status", "")

        if any(kw in docker_status.lower() or kw in action.lower()
               for kw in ["die", "kill", "oom", "error", "fail", "destroy"]):
            status, severity = "failed", "warning"
            reason = f"Container {action}: {docker_status}" if docker_status else f"Container {action}"
        elif action in ("start", "restart", "create"):
            status, severity = "healthy", "info"
            reason = None
        else:
            status, severity = "healthy", "info"
            reason = None

        normalized = {
            "status": status,
            "severity": severity,
            "failure_reason": reason,
            "action": action,
            "container_id": raw_data.get("id"),
            "image": raw_data.get("image"),
        }

        return normalized

    def _normalize_ec2_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        state = raw_data.get("state", "unknown")
        status_check = raw_data.get("status_check", "unknown")
        system_check = raw_data.get("system_status_check", "unknown")

        status = "healthy"
        severity = "info"
        reason = None

        if state == "running":
            if status_check == "impaired" or system_check == "impaired":
                status = "failed"
                severity = "critical"
                reason = f"Instance status check impaired (instance: {status_check}, system: {system_check})"
            elif status_check == "degraded" or system_check == "degraded":
                status = "degraded"
                severity = "warning"
                reason = f"Instance status check degraded (instance: {status_check}, system: {system_check})"
            elif status_check == "insufficient-data":
                status = "pending"
                severity = "info"
                reason = "Status check: insufficient data"
            else:
                status = "healthy"
                severity = "info"
                reason = None
        elif state == "stopped":
            status = "degraded"
            severity = "warning"
            reason = "Instance stopped"
        elif state == "stopping":
            status = "degraded"
            severity = "warning"
            reason = "Instance stopping"
        elif state == "pending":
            status = "pending"
            severity = "info"
            reason = "Instance pending"
        elif state == "terminated":
            status = "failed"
            severity = "warning"
            reason = "Instance terminated"
        elif state in ("shutting-down",):
            status = "degraded"
            severity = "warning"
            reason = f"Instance {state}"

        events = raw_data.get("events", [])
        if events:
            event_descs = [e.get("description", e.get("code", "")) for e in events]
            combined = "; ".join(filter(None, event_descs))
            if combined:
                reason = f"{reason + '; ' if reason else ''}{combined}"
                if severity == "info":
                    severity = "warning"
                if status == "healthy":
                    status = "degraded"

        normalized = {
            "status": status,
            "severity": severity,
            "failure_reason": reason,
            "kind": "EC2",
            "name": raw_data.get("name") or raw_data.get("instance_id", "unknown"),
            "instance_id": raw_data.get("instance_id"),
            "instance_type": raw_data.get("instance_type"),
            "state": state,
            "status_check": status_check,
            "system_status_check": system_check,
            "private_ip": raw_data.get("private_ip"),
            "public_ip": raw_data.get("public_ip"),
            "region": raw_data.get("region"),
            "vpc_id": raw_data.get("vpc_id"),
            "subnet_id": raw_data.get("subnet_id"),
            "events": events,
        }

        return normalized

    def _normalize_aws_event(self, raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
        event_name = raw_data.get("eventName", "unknown")

        aws_failure_keywords = ["Fail", "Error", "Terminate", "Stop", "Delete", "Revoke", "Deny"]
        if any(kw in event_name for kw in aws_failure_keywords):
            status, severity = "degraded", "warning"
            reason = f"AWS API call: {event_name}"
        else:
            status, severity = "healthy", "info"
            reason = None

        normalized = {
            "status": status,
            "severity": severity,
            "failure_reason": reason,
            "action": event_name,
            "resource_type": raw_data.get("resources", [{}])[0].get("type") if raw_data.get("resources") else "unknown",
            "resource_id": raw_data.get("resources", [{}])[0].get("ARN") if raw_data.get("resources") else "unknown",
            "region": raw_data.get("region"),
            "source_ip": raw_data.get("sourceIPAddress"),
        }

        return normalized


if __name__ == "__main__":
    engine = NormalizationEngine()

    k8s_event = {
        "event_type": "kubernetes",
        "source": "kubernetes",
        "raw_data": {
            "type": "Pod",
            "name": "web-app-5d6f8c4b9-abcde",
            "namespace": "production",
            "status": "Running",
            "timestamp": "2024-01-01T12:00:00Z",
        },
    }

    normalized = engine.normalize_event(k8s_event)
    print("Normalized K8s event:")
    print(f"  Kind: {normalized.get('kind')}")
    print(f"  Name: {normalized.get('name')}")
    print(f"  Namespace: {normalized.get('namespace')}")
    print(f"  Status: {normalized.get('status')}")
    print(f"  Severity: {normalized.get('severity')}")
    print(f"  Failure reason: {normalized.get('failure_reason')}")
