import yaml
from pydantic import BaseModel

from k8s_app_abstraction.utils import camelize


class Base(BaseModel):
    def generate(self):
        raise NotImplementedError()


class YamlMixin:
    def generate(self):
        raise NotImplementedError()

    def to_yaml(self) -> str:
        def _format(res):
            if isinstance(res, dict):
                new = {}
                for k, v in res.items():
                    k = camelize(k)
                    if v is not None:
                        new[k] = _format(v)
                return new

            if isinstance(res, list):
                return [_format(_) for _ in res]

            return res

        return "---\n".join(map(yaml.safe_dump, map(_format, self.generate())))
