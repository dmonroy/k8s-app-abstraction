from typing import Optional

from kubernetes.client import V1ObjectMeta

from k8s_app_abstraction.models.base import Base, YamlMixin
from k8s_app_abstraction.utils import merge


class Resource(Base, YamlMixin):
    name: str
    _kind = None

    @property
    def _resource_defaults(self):
        return {
            "kind": self._kind,
            "api_version": "apps/v1",
            "metadata": self.metadata,
        }

    @property
    def _metadata_defaults(self):
        return {
            "name": self.name,
        }

    @property
    def metadata(self):
        return V1ObjectMeta(**self._metadata_defaults)


class ResourceList(list):
    def generate(self):
        for el in self:
            yield el.generate()


class NamespacedResource(Resource):
    namespace: Optional[str] = None

    @property
    def _metadata_defaults(self):
        return dict(
            merge(
                super(NamespacedResource, self)._metadata_defaults,
                {"namespace": self.namespace},
            )
        )
