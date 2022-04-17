import os
from re import sub
from urllib.parse import urlparse

import requests
import yaml


def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def merge(dict1, dict2):
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(merge(dict1[k], dict2[k])))
            else:
                # If one of the values is not a dict, you can't merge it.
                # Value from second dict overrides one in first, then we
                # move on.
                yield (k, dict2[k])
                # Alternatively, replace this with exception raiser to alert
                # you of value conflicts
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])


def parse_yaml(content):
    result = {}
    for partial in yaml.safe_load_all(content):
        if not partial:
            continue

        include = partial.pop("include", [])
        included = {}
        for child in include:
            child_dict = dict(load_yaml_files(child))
            included = dict(merge(included, child_dict))

        if include:
            partial = dict(merge(included, partial))

        result = dict(merge(result, partial))

    return {k: v for k, v in result.items() if not k.startswith(".")}


def load_yaml_files(*args):
    def load_yaml_file(filepath) -> str:
        if uri_validator(filepath):
            return requests.get(filepath).content

        with open(filepath) as f:
            return f.read()

    def _load_all_files():
        for filepath in args:
            yield load_yaml_file(filepath)

    return parse_yaml("\n---\n".join(_ for _ in _load_all_files() if _))


def camelize(key) -> str:
    """camelCase given key"""
    enumerated = enumerate(key.lower().split("_"))
    return "".join(_ if i == 0 else _.capitalize() for i, _ in enumerated)


def snakelize(s):
    return "_".join(
        sub(
            "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))
        ).split()
    ).lower()


def dict_to_yaml(data, context: dict = None):
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

        if isinstance(res, LazyString):
            return res.render(context)

        return res

    return yaml.safe_dump(_format(data))


class Context(object):
    def __init__(self, context):
        self.context = context

    def resolve(self, name):
        return name

    def prefix(self, name):
        return f"{self.context['stack'].name}-{name}"


class LazyString(str):

    context: object = None

    def get_template(self):
        return self

    def render(self, context):
        rtemplate = Environment(loader=BaseLoader).from_string(self.get_template())

        context = Context(context)

        return rtemplate.render(resolve=context.resolve, prefix=context.prefix)


class Prefixed(LazyString):
    def get_template(self):
        return "{{ prefix('%s') }}" % self
