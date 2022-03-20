from typing import Optional, Union

from kubernetes import client
from kubernetes.client import (
    V1Container,
    V1LabelSelector,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
)

from k8s_app_abstraction.models.resource import NamespacedResource, ResourceList
from k8s_app_abstraction.utils import merge


class BasePodController(NamespacedResource):
    _api = client.AppsV1Api
    api_version: str = "apps/v1"
    image: str
    entrypoint: Optional[Union[list, None]] = None
    command: Optional[Union[list, None]] = None

    @property
    def _pod_controller_defaults(self):
        return dict(
            selector=V1LabelSelector(
                match_labels={
                    k: v
                    for k, v in self.metadata.labels.items()
                    if k.startswith("app.kubernetes.io/")
                }
            ),
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(labels=self.metadata.labels),
                spec=V1PodSpec(
                    containers=self.containers,
                ),
            ),
        )

    @property
    def containers(self):
        return [
            V1Container(
                args=self.command,
                command=self.entrypoint,
                name=self.name,
                image=self.image,
            )
        ]

    @property
    def _pod_controller_extras(self):
        return {}

    @property
    def _api_resource_class(self):
        raise NotImplementedError()

    @property
    def _api_spec_class(self):
        raise NotImplementedError()

    def generate(self):
        return self._api_resource_class(
            **self._resource_defaults,
            spec=self._api_spec_class(
                **self._pod_controller_defaults, **self._pod_controller_extras
            ),
        ).to_dict()


class ReplicaSetController(BasePodController):
    replicas: int = 1

    @property
    def _pod_controller_defaults(self):
        return dict(
            merge(
                super(ReplicaSetController, self)._pod_controller_defaults,
                {"replicas": self.replicas},
            )
        )


class Deployment(ReplicaSetController):
    _kind = "Deployment"
    _api_resource_class = client.V1Deployment
    _api_spec_class = client.V1DeploymentSpec
    _api_loader = "read_namespaced_deployment"


class Daemonset(BasePodController):
    _kind = "DaemonSet"
    _api_resource_class = client.V1DaemonSet
    _api_spec_class = client.V1DaemonSetSpec
    _api_loader = "read_namespaced_daemon_set"


class Statefulset(ReplicaSetController):
    _kind = "StatefulSet"
    _api_resource_class = client.V1StatefulSet
    _api_spec_class = client.V1StatefulSetSpec
    _api_loader = "read_namespaced_stateful_set"

    @property
    def _pod_controller_extras(self):
        return {"service_name": self.name}


class DeploymentList(ResourceList):
    pass


class DaemonsetList(ResourceList):
    pass


class StatefulsetList(ResourceList):
    pass


class CronjobList(ResourceList):
    pass
