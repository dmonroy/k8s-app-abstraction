from typing import Optional

from kubernetes.client import V1ObjectMeta

from k8s_app_abstraction.models.base import Base, YamlMixin
from k8s_app_abstraction.utils import merge


class Resource(Base, YamlMixin):
    name: str
    _kind = None
    _apis = {}

    @property
    def _resource_defaults(self):
        return {
            "kind": self._kind,
            "api_version": self.api_version,
            "metadata": self.metadata,
        }

    @property
    def _metadata_defaults(self):
        return {
            "name": self.name,
            "labels": {
                "app.kubernetes.io/name": self.name,
                "app.kubernetes.io/instance": self.name,
                # "app.kubernetes.io/component": self.component,
                # "app.kubernetes.io/version": self.stack.app_version,
            },
        }

    @property
    def metadata(self):
        return V1ObjectMeta(**self._metadata_defaults)

    @property
    def kubernetes_loader(self):
        api_name = self._api.__name__
        if api_name not in self._apis:
            self._apis[api_name] = self._api()
        api = self._apis[api_name]
        return getattr(api, self._api_loader)

    def kubernetes_resource(self):
        return self.kubernetes_loader(name=self.name)

    def get_from_kubernetes(self):
        return self.kubernetes_resource()


class ResourceList(list):
    def generate(self):
        for el in self:
            yield el.generate()


class NamespacedResource(Resource):
    namespace: Optional[str] = "default"

    @property
    def _metadata_defaults(self):
        return dict(
            merge(
                super(NamespacedResource, self)._metadata_defaults,
                {"namespace": self.namespace},
            )
        )

    def kubernetes_resource(self):
        return self.kubernetes_loader(namespace=self.namespace, name=self.name)
