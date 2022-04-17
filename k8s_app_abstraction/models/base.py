from typing import Generator, Optional

from pydantic import BaseModel

from k8s_app_abstraction.utils import dict_to_yaml


class Base(BaseModel):
    def generate(self) -> Generator:
        raise NotImplementedError()


class YamlMixin:
    def generate(self) -> Generator:
        raise NotImplementedError()

    def yaml_files(self, context: dict = None) -> Generator:

        for el in self.generate():
            filename = "{}.yml".format(
                "-".join([el["kind"].lower(), el["metadata"]["name"]])
            )
            yield filename, dict_to_yaml(el, context=context)

    def to_yaml(self, context: dict = None) -> str:
        return "---\n".join(
            content for file, content in self.yaml_files(context=context)
        )
