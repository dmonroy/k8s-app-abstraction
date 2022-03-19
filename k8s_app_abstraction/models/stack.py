from typing import Optional

from pydantic import validator

from k8s_app_abstraction.models.base import Base, YamlMixin
from k8s_app_abstraction.models.pod_controllers import (
    CronjobList,
    Daemonset,
    DaemonsetList,
    Deployment,
    DeploymentList,
    Statefulset,
    StatefulsetList,
)
from k8s_app_abstraction.models.resource import ResourceList
from k8s_app_abstraction.utils import parse_yaml


class Stack(Base, YamlMixin):
    name: str
    deployments: Optional[DeploymentList] = []
    daemonsets: Optional[DaemonsetList] = []
    statefulsets: Optional[StatefulsetList] = []
    cronjobs: Optional[CronjobList] = []

    @classmethod
    def new(cls, name: str, definition: str) -> "Stack":
        return Stack(name=name, **parse_yaml(definition))

    def generate(self):
        for k in self.__annotations__.keys():
            x = getattr(self, k)
            if hasattr(x, "generate"):
                if isinstance(x, ResourceList):
                    for res in x.generate():
                        yield res
                else:
                    yield x.generate()

    @validator("deployments", pre=True)
    def cast_deployments(cls, value):
        if isinstance(value, list):
            return DeploymentList(value)

        if isinstance(value, dict):
            dl = DeploymentList()
            for name, structure in value.items():
                dl.append(Deployment(name=name, **structure))

            return dl

        raise ValueError("Invalid value for DeploymentList")

    @validator("daemonsets", pre=True)
    def cast_daemonsets(cls, value):
        if isinstance(value, list):
            return DaemonsetList(value)

        if isinstance(value, dict):
            dl = DaemonsetList()
            for name, structure in value.items():
                dl.append(Daemonset(name=name, **structure))

            return dl

        raise ValueError("Invalid value for DaemonsetList")

    @validator("statefulsets", pre=True)
    def cast_statefulsets(cls, value):
        if isinstance(value, list):
            return StatefulsetList(value)

        if isinstance(value, dict):
            dl = StatefulsetList()
            for name, structure in value.items():
                dl.append(Statefulset(name=name, **structure))

            return dl

        raise ValueError("Invalid value for StatefulsetList")
