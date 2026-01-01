"""
Kubernetes Data Collector
Enriches K8s events with additional cluster context and metrics
"""
import os
import json
from kubernetes import client, config
from typing import Dict, Any, Optional, List


class K8sDataCollector:
    """
    Collects and enriches Kubernetes data for incident analysis
    """

    def __init__(self, cluster_name: Optional[str] = None):
        """
        Initialize K8s data collector

        Args:
            cluster_name: Name of the Kubernetes cluster
        """
        self.cluster_name = cluster_name or os.environ.get('K8S_CLUSTER_NAME', 'unknown')
        self._setup_k8s_client()

    def _setup_k8s_client(self):
        """Setup Kubernetes client (for EKS or local kubeconfig)"""
        try:
            # Try in-cluster config first (for pods running in K8s)
            config.load_incluster_config()
            print("✅ Using in-cluster Kubernetes configuration")
        except:
            try:
                # Fallback to local kubeconfig
                config.load_kube_config()
                print("✅ Using local kubeconfig")
            except Exception as e:
                print(f"❌ Failed to setup K8s client: {e}")
                self.v1 = None
                self.apps_v1 = None
                return

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def enrich_pod_event(self, pod_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich pod event with additional context

        Args:
            pod_data: Basic pod event data from EventBridge

        Returns:
            Dict: Enriched pod data with additional context
        """
        if not self.v1:
            print("⚠️ K8s client not available, returning basic pod data")
            return pod_data

        try:
            namespace = pod_data.get('namespace', 'default')
            pod_name = pod_data.get('pod_name')

            if not pod_name:
                return pod_data

            # Get current pod status
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=namespace)

            # Enrich with current pod information
            enriched_data = {
                **pod_data,
                'cluster_name': self.cluster_name,
                'pod_ip': pod.status.pod_ip,
                'host_ip': pod.status.host_ip,
                'phase': pod.status.phase,
                'qos_class': pod.status.qos_class,
                'start_time': pod.status.start_time.isoformat() if pod.status.start_time else None,
                'owner_references': self._extract_owner_references(pod),
                'resource_requests': self._extract_resource_requests(pod),
                'resource_limits': self._extract_resource_limits(pod),
                'environment_variables': self._extract_env_vars(pod),
                'volume_mounts': self._extract_volume_mounts(pod),
                'conditions': self._extract_pod_conditions(pod),
                'container_statuses': self._extract_container_statuses(pod)
            }

            # Add deployment/replicaset context if applicable
            owner_info = self._get_owner_context(pod)
            if owner_info:
                enriched_data.update(owner_info)

            return enriched_data

        except Exception as e:
            print(f"❌ Error enriching pod data: {e}")
            return pod_data

    def get_node_context(self, node_name: str) -> Dict[str, Any]:
        """
        Get node context information

        Args:
            node_name: Name of the Kubernetes node

        Returns:
            Dict: Node context information
        """
        if not self.v1:
            return {}

        try:
            node = self.v1.read_node(name=node_name)

            return {
                'node_name': node_name,
                'node_info': {
                    'architecture': node.status.node_info.architecture,
                    'os_image': node.status.node_info.os_image,
                    'kernel_version': node.status.node_info.kernel_version,
                    'kubelet_version': node.status.node_info.kubelet_version,
                    'container_runtime_version': node.status.node_info.container_runtime_version
                },
                'capacity': dict(node.status.capacity) if node.status.capacity else {},
                'allocatable': dict(node.status.allocatable) if node.status.allocatable else {},
                'conditions': [
                    {
                        'type': condition.type,
                        'status': condition.status,
                        'reason': condition.reason,
                        'message': condition.message
                    }
                    for condition in (node.status.conditions or [])
                ]
            }

        except Exception as e:
            print(f"❌ Error getting node context: {e}")
            return {'node_name': node_name, 'error': str(e)}

    def get_namespace_events(self, namespace: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent events in a namespace

        Args:
            namespace: Kubernetes namespace
            limit: Maximum number of events to return

        Returns:
            List: Recent events in the namespace
        """
        if not self.v1:
            return []

        try:
            events = self.v1.list_namespaced_event(
                namespace=namespace,
                limit=limit,
                field_selector='involvedObject.kind=Pod'
            )

            return [
                {
                    'name': event.metadata.name,
                    'namespace': event.namespace,
                    'reason': event.reason,
                    'message': event.message,
                    'type': event.type,
                    'count': event.count,
                    'first_timestamp': event.first_timestamp.isoformat() if event.first_timestamp else None,
                    'last_timestamp': event.last_timestamp.isoformat() if event.last_timestamp else None,
                    'involved_object': {
                        'kind': event.involved_object.kind,
                        'name': event.involved_object.name,
                        'namespace': event.involved_object.namespace
                    }
                }
                for event in events.items
            ]

        except Exception as e:
            print(f"❌ Error getting namespace events: {e}")
            return []

    def _extract_owner_references(self, pod) -> List[Dict[str, Any]]:
        """Extract owner references from pod"""
        if not pod.metadata.owner_references:
            return []

        return [
            {
                'kind': ref.kind,
                'name': ref.name,
                'uid': ref.uid,
                'controller': ref.controller
            }
            for ref in pod.metadata.owner_references
        ]

    def _extract_resource_requests(self, pod) -> Dict[str, str]:
        """Extract resource requests from pod containers"""
        requests = {}
        for container in pod.spec.containers:
            if container.resources and container.resources.requests:
                requests[container.name] = dict(container.resources.requests)
        return requests

    def _extract_resource_limits(self, pod) -> Dict[str, str]:
        """Extract resource limits from pod containers"""
        limits = {}
        for container in pod.spec.containers:
            if container.resources and container.resources.limits:
                limits[container.name] = dict(container.resources.limits)
        return limits

    def _extract_env_vars(self, pod) -> Dict[str, List[str]]:
        """Extract environment variables from containers (names only for security)"""
        env_vars = {}
        for container in pod.spec.containers:
            if container.env:
                env_vars[container.name] = [env.name for env in container.env]
        return env_vars

    def _extract_volume_mounts(self, pod) -> Dict[str, List[Dict[str, str]]]:
        """Extract volume mounts from containers"""
        volume_mounts = {}
        for container in pod.spec.containers:
            if container.volume_mounts:
                volume_mounts[container.name] = [
                    {
                        'name': vm.name,
                        'mount_path': vm.mount_path,
                        'read_only': vm.read_only
                    }
                    for vm in container.volume_mounts
                ]
        return volume_mounts

    def _extract_pod_conditions(self, pod) -> List[Dict[str, Any]]:
        """Extract pod conditions"""
        if not pod.status.conditions:
            return []

        return [
            {
                'type': condition.type,
                'status': condition.status,
                'reason': condition.reason,
                'message': condition.message,
                'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else None
            }
            for condition in pod.status.conditions
        ]

    def _extract_container_statuses(self, pod) -> List[Dict[str, Any]]:
        """Extract container statuses"""
        if not pod.status.container_statuses:
            return []

        return [
            {
                'name': status.name,
                'ready': status.ready,
                'restart_count': status.restart_count,
                'image': status.image,
                'image_id': status.image_id,
                'container_id': status.container_id,
                'started': status.started,
                'state': self._extract_container_state(status.state) if status.state else None,
                'last_state': self._extract_container_state(status.last_state) if status.last_state else None
            }
            for status in pod.status.container_statuses
        ]

    def _extract_container_state(self, state) -> Dict[str, Any]:
        """Extract container state information"""
        if state.waiting:
            return {
                'state': 'waiting',
                'reason': state.waiting.reason,
                'message': state.waiting.message
            }
        elif state.running:
            return {
                'state': 'running',
                'started_at': state.running.started_at.isoformat() if state.running.started_at else None
            }
        elif state.terminated:
            return {
                'state': 'terminated',
                'exit_code': state.terminated.exit_code,
                'reason': state.terminated.reason,
                'message': state.terminated.message,
                'started_at': state.terminated.started_at.isoformat() if state.terminated.started_at else None,
                'finished_at': state.terminated.finished_at.isoformat() if state.terminated.finished_at else None
            }
        return {}

    def _get_owner_context(self, pod) -> Optional[Dict[str, Any]]:
        """Get deployment/replicaset context for the pod"""
        try:
            if not pod.metadata.owner_references:
                return None

            # Find ReplicaSet owner
            for ref in pod.metadata.owner_references:
                if ref.kind == 'ReplicaSet':
                    rs = self.apps_v1.read_namespaced_replica_set(
                        name=ref.name,
                        namespace=pod.metadata.namespace
                    )

                    # Check if ReplicaSet has a Deployment owner
                    if rs.metadata.owner_references:
                        for rs_ref in rs.metadata.owner_references:
                            if rs_ref.kind == 'Deployment':
                                deployment = self.apps_v1.read_namespaced_deployment(
                                    name=rs_ref.name,
                                    namespace=pod.metadata.namespace
                                )

                                return {
                                    'deployment_name': deployment.metadata.name,
                                    'deployment_replicas': deployment.spec.replicas,
                                    'deployment_ready_replicas': deployment.status.ready_replicas or 0,
                                    'deployment_strategy': deployment.spec.strategy.type if deployment.spec.strategy else None
                                }

                    return {
                        'replicaset_name': rs.metadata.name,
                        'replicaset_replicas': rs.spec.replicas
                    }

            return None

        except Exception as e:
            print(f"⚠️ Error getting owner context: {e}")
            return None