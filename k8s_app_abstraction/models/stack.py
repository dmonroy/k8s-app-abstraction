import os
from distutils.version import LooseVersion, StrictVersion
from enum import Enum
from subprocess import STDOUT, CalledProcessError, check_output
from tempfile import TemporaryDirectory
from typing import Optional

import kubernetes
import yaml
from kubernetes import client, config
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
from k8s_app_abstraction.models.resource import Resource, ResourceList
from k8s_app_abstraction.utils import dict_to_yaml, load_yaml_files, parse_yaml


class Stack(Base, YamlMixin):
    class Config:
        arbitrary_types_allowed = True

    name: str
    description: Optional[str]
    version: Optional[StrictVersion]
    app_version: Optional[LooseVersion]
    deployments: Optional[DeploymentList] = []
    daemonsets: Optional[DaemonsetList] = []
    statefulsets: Optional[StatefulsetList] = []
    cronjobs: Optional[CronjobList] = []

    @classmethod
    def new(cls, name: str, definition: str) -> "Stack":
        return Stack(name=name, **parse_yaml(definition))

    @classmethod
    def from_files(cls, *args: str) -> "Stack":
        definition = load_yaml_files(*args)

    @property
    def chart(self):
        return HelmChart(stack=self, template_generator=self.yaml_files)

    def to_yaml(self, context: Optional[dict] = None) -> str:
        return super(Stack, self).to_yaml(
            context={"stack": self} if context is None else context
        )

    @property
    def get_all_resources(self):
        for k in self.__annotations__.keys():
            x = getattr(self, k)
            if isinstance(x, Resource):
                yield x
            if isinstance(x, ResourceList):
                for res in x:
                    yield res

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
                if isinstance(structure, Deployment):
                    dl.append(structure)
                else:
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


class HelmChart(Base, YamlMixin):
    class TypeEnum(str, Enum):
        application = "application"
        library = "library"

    stack: Stack
    type: TypeEnum = TypeEnum.application
    description: Optional[str] = "A Helm chart for Kubernetes created dynamically"

    def generate(self):
        return self.stack.generate()

    def generate_files(self):
        yield self.generate_info_file()
        for filename, template in self.yaml_files(
            context={
                "stack": self.stack,
            }
        ):
            yield f"templates/{filename}", template

    def generate_info_file(self):
        return "Chart.yaml", dict_to_yaml(
            {
                "name": self.stack.name,
                "description": self.stack.description,
                "version": self.stack.version or "0.1.0",
                "app_version": self.stack.app_version or self.stack.version or "0.1.0",
            },
            context=None,
        )

    def dump(self, folder):
        for filename, content in self.generate_files():
            absolute_filename = os.path.join(folder, filename)
            if "/" in filename:
                file_folder = absolute_filename.rsplit("/", 1)[0]
                os.makedirs(file_folder, exist_ok=True)

            with open(absolute_filename, "w") as f:
                f.write(content)

    def check_compatibility(self):
        server = client.VersionApi().get_code()
        library_version = StrictVersion(kubernetes.__version__)
        assert abs(int(server.minor) - library_version.version[0]) <= 1, (
            f"kubernetes library {library_version} is not "
            f"compatible with server version {server.git_version}"
        )

    def rollout(self, location: Optional[str] = None) -> "HelmRelease":
        # Load kubernetes config
        config.load_kube_config()

        self.check_compatibility()

        def _rollout(loc: str) -> HelmRelease:
            self.dump(loc)
            self.exec(self.rollout_command(loc))
            # return HelmRelease.load(self.stack.name)

        if location:
            return _rollout(location)

        with TemporaryDirectory() as location:
            return _rollout(location)

    def rollout_command(self, location):
        return ["helm", "upgrade", "--install", self.stack.name, location]

    def uninstall(self):
        return self.exec(["helm", "delete", self.stack.name])

    def exec(self, command: str):
        def _log(output):
            for line in output.decode("utf-8").splitlines():
                print(line)

        try:
            _log(check_output(command, stderr=STDOUT))
        except CalledProcessError as e:
            _log(e.output)
            raise e

    def get_kubernetes_resources(self):
        for res in self.stack.get_all_resources:
            yield res.get_from_kubernetes(stack=self.stack)


class HelmRelease(Base):
    resource_definitions: dict

    @classmethod
    def load(cls, name) -> "HelmRelease":
        command = ["helm", "get", "manifest", name]
        try:
            yaml_resources = check_output(command, stderr=STDOUT)
        except CalledProcessError as e:
            print(e.output)
            raise e

        return HelmRelease(
            resource_definitions={
                f"{res['kind']}/{res['metadata']['name']}": res
                for res in yaml.safe_load_all(yaml_resources)
            }
        )

    def refresh(self):
        for name, resource in self.resource_definitions.keys():
            pass
