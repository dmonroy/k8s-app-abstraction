from io import StringIO
from textwrap import dedent
from unittest import mock

import pytest
import requests

from k8s_app_abstraction.models.stack import Stack

DEFINITION = """
include:
  - /etc/company/base.yml
  - ~/user.yml

deployments:
  app:
    image: awesome/app
    replicas: 3
"""

BASE_YAML = """
include:
- /etc/company/databases.yml
- https://dev.inter.net/something-amazing/manifest.yml

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

WEB_YAML = """
deployments:
  other-app:
    image: other-app
"""

MOCKED_FILES = {
    "/etc/company/base.yml": BASE_YAML,
    "/etc/company/databases.yml": DATABASES_YAML,
    "~/user.yml": USER_YAML,
}

MOCKED_URLS = {
    "https://dev.inter.net/something-amazing/manifest.yml": WEB_YAML,
}


def test_include_fine_not_found():
    with pytest.raises(FileNotFoundError) as err:
        Stack.new(name="test", definition=DEFINITION)


def test_include():
    def mock_open(name, *args, **kwargs):
        if name not in MOCKED_FILES:
            return open(name, *args, **kwargs)

        return StringIO(MOCKED_FILES[name])

    def mock_requests_get(url, *args, **kwargs):
        if url not in MOCKED_URLS:
            return requests.get(url, *args, **kwargs)

        class FakeResponse:
            content = MOCKED_URLS[url]

        return FakeResponse()

    with mock.patch("k8s_app_abstraction.utils.open", new=mock_open):
        with mock.patch(
            "k8s_app_abstraction.utils.requests.get", new=mock_requests_get
        ):
            stack = Stack.new(name="test", definition=DEFINITION)
            resources = {
                f"{r.__class__.__name__}/{r.name}": r for r in stack.get_all_resources
            }

            # FROM top level yaml
            assert "Deployment/app" in resources

            # FROM top level include
            assert "Deployment/foo" in resources
            assert "Deployment/pypi-cache" in resources

            # FROM nested includes
            assert "Statefulset/redis" in resources
            assert "Statefulset/postgres" in resources

            # From URL
            assert "Deployment/other-app" in resources
