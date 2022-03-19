from typing import Optional, Union

from kubernetes.client import (
    V1Container,
    V1DaemonSet,
    V1DaemonSetSpec,
    V1Deployment,
    V1DeploymentSpec,
    V1LabelSelector,
    V1PodSpec,
    V1PodTemplateSpec,
    V1StatefulSet,
    V1StatefulSetSpec,
)

from k8s_app_abstraction.models.resource import NamespacedResource, ResourceList
from k8s_app_abstraction.utils import merge


class BasePodController(NamespacedResource):

    image: str
    entrypoint: Optional[Union[list, None]] = None
    command: Optional[Union[list, None]] = None

    @property
    def _pod_controller_defaults(self):
        return dict(
            selector=V1LabelSelector(match_labels={"app": self.name}),
            template=V1PodTemplateSpec(
                spec=V1PodSpec(
                    containers=self.containers,
                )
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

    def generate(self):
        return V1Deployment(
            **self._resource_defaults,
            spec=V1DeploymentSpec(**self._pod_controller_defaults),
        ).to_dict()


class Daemonset(BasePodController):
    _kind = "Daemonset"

    def generate(self):
        return V1DaemonSet(
            **self._resource_defaults,
            spec=V1DaemonSetSpec(**self._pod_controller_defaults),
        ).to_dict()


class Statefulset(ReplicaSetController):
    _kind = "Statefulset"

    def generate(self):
        return V1StatefulSet(
            **self._resource_defaults,
            spec=V1StatefulSetSpec(
                **self._pod_controller_defaults, service_name=self.name
            ),
        ).to_dict()


class DeploymentList(ResourceList):
    pass


class DaemonsetList(ResourceList):
    pass


class StatefulsetList(ResourceList):
    pass


class CronjobList(ResourceList):
    pass
