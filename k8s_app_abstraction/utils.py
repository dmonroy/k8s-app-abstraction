from re import sub

import yaml


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
        if partial is not None:
            result = dict(merge(result, partial))

    return {k: v for k, v in result.items() if not k.startswith(".")}


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


def dict_to_yaml(data):
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

    return yaml.safe_dump(_format(data))
