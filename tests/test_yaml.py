from io import StringIO
from textwrap import dedent
from unittest import mock

import pytest

from k8s_app_abstraction.models.stack import Stack

DEFINITION = dedent(
    """
    include:
      - /etc/company/base.yml
      - ~/user.yml

    deployments:
      app:
        image: awesome/app
        replicas: 3
    """
)

BASE_YAML = """
include:
- /etc/company/databases.yml

deployments:
  foo:
    image: bar
"""

DATABASES_YAML = """
statefulsets:
  redis:
    image: redis:latest
  postgres:
    image: postgres:latest
"""

USER_YAML = """
deployments:
  pypi-cache:
    image: my-pypi
"""


MOCKED_FILES = {
    "/etc/company/base.yml": BASE_YAML,
    "/etc/company/databases.yml": DATABASES_YAML,
    "~/user.yml": USER_YAML,
}


def test_include_fine_not_found():
    with pytest.raises(FileNotFoundError) as err:
        Stack.new(name="test", definition=DEFINITION)


def test_include():
    def mock_open(name, *args, **kwargs):
        if name not in MOCKED_FILES:
            return open(name, *args, **kwargs)

        return StringIO(MOCKED_FILES[name])

    with mock.patch("k8s_app_abstraction.utils.open", new=mock_open):
        stack = Stack.new(name="test", definition=DEFINITION)
