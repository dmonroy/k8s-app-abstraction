import yaml
from pydantic import BaseModel

from k8s_app_abstraction.utils import camelize, dict_to_yaml


class Base(BaseModel):
    def generate(self):
        raise NotImplementedError()


class YamlMixin:
    def generate(self):
        raise NotImplementedError()

    def yaml_files(self):

        for el in self.generate():
            filename = "{}.yml".format(
                "-".join([el["kind"].lower(), el["metadata"]["name"].lower()])
            )
            yield filename, dict_to_yaml(el)

    def to_yaml(self) -> str:
        return "---\n".join(content for file, content in self.yaml_files())
