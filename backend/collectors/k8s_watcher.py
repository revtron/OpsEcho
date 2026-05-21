import logging
from typing import Dict, Any
from kubernetes import client, config, watch

class K8sWatcher:
    def __init__(self):
        try:
            # Try to load in-cluster config first, then fallback to kubeconfig
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
            raise

    def watch_events(self, namespace: str = None):
        """
        Watch for Kubernetes events and yield them.
        In a real implementation, this would be a long-running process.
        For this MVP, we'll simulate watching by returning recent events.
        """
        # This is a simplified implementation for MVP
        # In reality, you'd use the watch.Watch() interface to stream events
        try:
            # Get recent pod events as an example
            if namespace:
                pods = self.v1.list_namespaced_pod(namespace=namespace)
            else:
                pods = self.v1.list_pod_for_all_namespaces()
            
            events = []
            for pod in pods.items:
                # Convert pod status to event-like structure
                event = {
                    "type": "Pod",
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "timestamp": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    "source": "kubernetes"
                }
                events.append(event)
            
            return events
        except Exception as e:
            logging.error(f"Error watching Kubernetes events: {e}")
            return []

    def watch_deployments(self, namespace: str = None):
        """Watch for deployment changes."""
        try:
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces()
            
            events = []
            for deploy in deployments.items:
                event = {
                    "type": "Deployment",
                    "namespace": deploy.metadata.namespace,
                    "name": deploy.metadata.name,
                    "replicas": deploy.spec.replicas,
                    "available_replicas": deploy.status.available_replicas if deploy.status else 0,
                    "timestamp": deploy.metadata.creation_timestamp.isoformat() if deploy.metadata.creation_timestamp else None,
                    "source": "kubernetes"
                }
                events.append(event)
            
            return events
        except Exception as e:
            logging.error(f"Error watching Kubernetes deployments: {e}")
            return []

# For testing purposes
if __name__ == "__main__":
    watcher = K8sWatcher()
    print("Watching for pod events...")
    events = watcher.watch_events()
    print(f"Found {len(events)} pod events")
    for event in events[:3]:  # Show first 3
        print(event)