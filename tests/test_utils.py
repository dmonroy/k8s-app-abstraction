from textwrap import dedent

import pytest

from k8s_app_abstraction.utils import camelize, merge, parse_yaml


def test_merge_dict():
    a = {"foo": "bar"}
    b = {"baz": "spam"}

    assert dict(merge(a, b)) == {"foo": "bar", "baz": "spam"}


def test_merge_yaml():
    content = dedent(
        """
        foo: bar
        ---
        baz: spam
        ---
        # also an empty yaml
        """
    )

    assert parse_yaml(content) == {"foo": "bar", "baz": "spam"}


def test_nested_merge_yaml():
    content = dedent(
        """
        foo: bar
        users:
            John: Doe
            Jane: Smith
        ---
        baz: spam
        users:
            John: Doe
            Bob: Ford
        """
    )

    assert parse_yaml(content) == {
        "foo": "bar",
        "baz": "spam",
        "users": {"John": "Doe", "Jane": "Smith", "Bob": "Ford"},
    }


@pytest.mark.parametrize(
    "original,expected",
    [
        ("", ""),
        ("pod", "pod"),
        ("pod_spec", "podSpec"),
        ("Pod_Spec", "podSpec"),
    ],
)
def test_camelize(original, expected):
    assert camelize(original) == expected
