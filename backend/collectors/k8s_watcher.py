import logging
from typing import Dict, Any, List, Optional
from kubernetes import client, config

class K8sWatcher:
    def __init__(self):
        self.v1 = None
        self.apps_v1 = None
        self.networking_v1 = None
        try:
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()

            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            logging.info("Kubernetes watcher initialized")
        except Exception as e:
            logging.error(f"Failed to initialize Kubernetes watcher: {e}")

    def _extract_container_status(self, container_status) -> Optional[Dict[str, Any]]:
        """Extract detailed container status including failure reasons."""
        info = {
            "name": container_status.name,
            "ready": container_status.ready,
            "restart_count": container_status.restart_count,
            "state": None,
            "reason": None,
            "message": None,
        }

        if container_status.state:
            if container_status.state.waiting:
                info["state"] = "waiting"
                info["reason"] = container_status.state.waiting.reason
                info["message"] = container_status.state.waiting.message
            elif container_status.state.terminated:
                info["state"] = "terminated"
                info["reason"] = container_status.state.terminated.reason
                info["message"] = container_status.state.terminated.message
                info["exit_code"] = container_status.state.terminated.exit_code
            elif container_status.state.running:
                info["state"] = "running"

        if container_status.last_state:
            if container_status.last_state.waiting:
                info["last_reason"] = container_status.last_state.waiting.reason
                info["last_message"] = container_status.last_state.waiting.message
            elif container_status.last_state.terminated:
                info["last_reason"] = container_status.last_state.terminated.reason
                info["last_message"] = container_status.last_state.terminated.message

        return info

    def _get_pod_failure_details(self, pod) -> Dict[str, Any]:
        """Extract failure details from a pod."""
        details = {
            "container_statuses": [],
            "restart_count": 0,
            "reason": pod.status.phase,
            "conditions": [],
        }

        if pod.status.conditions:
            for cond in pod.status.conditions:
                details["conditions"].append({
                    "type": cond.type,
                    "status": cond.status,
                    "reason": cond.reason,
                    "message": cond.message,
                })

        all_statuses = []
        if pod.status.container_statuses:
            all_statuses.extend(pod.status.container_statuses)
        if pod.status.init_container_statuses:
            all_statuses.extend(pod.status.init_container_statuses)
        if pod.status.ephemeral_container_statuses:
            all_statuses.extend(pod.status.ephemeral_container_statuses)

        for cs in all_statuses:
            info = self._extract_container_status(cs)
            if info:
                details["container_statuses"].append(info)
                details["restart_count"] += info.get("restart_count", 0)
                # Use the most severe container reason as the pod reason
                if info.get("reason") and info["reason"] not in ("Completed",):
                    details["reason"] = info["reason"]

        return details

    def _get_node_failure_details(self, node) -> Dict[str, Any]:
        """Extract failure details from a node."""
        details = {
            "conditions": [],
            "capacity": None,
            "allocatable": None,
        }

        if node.status.conditions:
            for cond in node.status.conditions:
                details["conditions"].append({
                    "type": cond.type,
                    "status": cond.status,
                    "reason": cond.reason,
                    "message": cond.message,
                })

        if node.status.capacity:
            details["capacity"] = {
                "cpu": str(node.status.capacity.get("cpu", "unknown")),
                "memory": str(node.status.capacity.get("memory", "unknown")),
                "pods": str(node.status.capacity.get("pods", "unknown")),
            }

        return details

    def watch_events(self, namespace: str = None) -> List[Dict[str, Any]]:
        if not self.v1:
            logging.warning("Kubernetes client not initialized")
            return []
        try:
            if namespace:
                pods = self.v1.list_namespaced_pod(namespace=namespace)
            else:
                pods = self.v1.list_pod_for_all_namespaces()

            events = []
            for pod in pods.items:
                failure = self._get_pod_failure_details(pod)
                event = {
                    "type": "Pod",
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "reason": failure.get("reason", pod.status.phase),
                    "restart_count": failure.get("restart_count", 0),
                    "container_statuses": failure.get("container_statuses", []),
                    "conditions": failure.get("conditions", []),
                    "timestamp": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    "labels": dict(pod.metadata.labels) if pod.metadata.labels else {},
                    "source": "kubernetes",
                }
                events.append(event)

            return events
        except Exception as e:
            logging.error(f"Error watching Kubernetes events: {e}")
            return []

    def watch_deployments(self, namespace: str = None) -> List[Dict[str, Any]]:
        if not self.apps_v1:
            logging.warning("Kubernetes apps client not initialized")
            return []
        try:
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces()

            events = []
            for deploy in deployments.items:
                conditions = []
                if deploy.status.conditions:
                    for cond in deploy.status.conditions:
                        conditions.append({
                            "type": cond.type,
                            "status": cond.status,
                            "reason": cond.reason,
                            "message": cond.message,
                        })

                replicas = deploy.spec.replicas
                available = deploy.status.available_replicas if deploy.status else 0
                updated = deploy.status.updated_replicas if deploy.status else 0
                ready = deploy.status.ready_replicas if deploy.status else 0

                reason = None
                if replicas and available < replicas:
                    reason = f"Available replicas ({available}) < desired ({replicas})"
                elif replicas and ready < replicas:
                    reason = f"Ready replicas ({ready}) < desired ({replicas})"

                event = {
                    "type": "Deployment",
                    "namespace": deploy.metadata.namespace,
                    "name": deploy.metadata.name,
                    "replicas": replicas,
                    "available_replicas": available,
                    "updated_replicas": updated,
                    "ready_replicas": ready,
                    "reason": reason,
                    "conditions": conditions,
                    "timestamp": deploy.metadata.creation_timestamp.isoformat() if deploy.metadata.creation_timestamp else None,
                    "labels": dict(deploy.metadata.labels) if deploy.metadata.labels else {},
                    "source": "kubernetes",
                }
                events.append(event)

            return events
        except Exception as e:
            logging.error(f"Error watching Kubernetes deployments: {e}")
            return []

    def watch_nodes(self) -> List[Dict[str, Any]]:
        """Watch for node-level events and conditions."""
        if not self.v1:
            logging.warning("Kubernetes client not initialized")
            return []
        try:
            nodes = self.v1.list_node()
            events = []
            for node in nodes.items:
                failure = self._get_node_failure_details(node)
                ready = False
                for cond in failure.get("conditions", []):
                    if cond["type"] == "Ready":
                        ready = cond["status"] == "True"
                        break

                event = {
                    "type": "Node",
                    "name": node.metadata.name,
                    "status": "Ready" if ready else "NotReady",
                    "reason": None if ready else "NodeNotReady",
                    "conditions": failure.get("conditions", []),
                    "capacity": failure.get("capacity", {}),
                    "timestamp": node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None,
                    "labels": dict(node.metadata.labels) if node.metadata.labels else {},
                    "source": "kubernetes",
                }
                events.append(event)

            return events
        except Exception as e:
            logging.error(f"Error watching Kubernetes nodes: {e}")
            return []


if __name__ == "__main__":
    watcher = K8sWatcher()
    print("Watching for pod events...")
    events = watcher.watch_events()
    print(f"Found {len(events)} pod events")
    for event in events[:3]:
        print(event)
