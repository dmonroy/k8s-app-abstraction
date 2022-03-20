import os
from subprocess import STDOUT
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import call

import kubernetes
import pytest
import yaml

from k8s_app_abstraction.models.pod_controllers import (
    Daemonset,
    Deployment,
    Statefulset,
)
from k8s_app_abstraction.models.stack import Stack


def test_basic():
    """Instantiate a stack with an empty definition"""

    definition = ""
    stack = Stack.new("my-stack", definition)
    assert stack.name == "my-stack"
    assert stack.dict()["name"] == "my-stack"


def test_stack_api():
    stack = Stack(
        name="my-stack",
        deployments=[Deployment(name="a-deploy", image="bar")],
        daemonsets=[Daemonset(name="a-daemonset", image="bar")],
        statefulsets=[Statefulset(name="a-statefulset", image="bar")],
    )

    assert len(stack.deployments) == 1
    assert len(stack.daemonsets) == 1
    assert len(stack.statefulsets) == 1
    assert len(stack.cronjobs) == 0

    assert stack.deployments[0].name == "a-deploy"
    assert stack.deployments[0].image == "bar"
    assert stack.deployments[0].replicas == 1

    assert stack.daemonsets[0].name == "a-daemonset"
    assert stack.daemonsets[0].image == "bar"

    assert stack.statefulsets[0].name == "a-statefulset"
    assert stack.statefulsets[0].image == "bar"
    assert stack.statefulsets[0].replicas == 1


def test_stack_to_yaml():
    stack = Stack(
        name="my-stack",
        deployments=[Deployment(name="a-deploy", image="bar", replicas=2)],
        daemonsets=[Daemonset(name="a-daemonset", image="bar")],
        statefulsets=[Statefulset(name="a-statefulset", image="bar")],
    )
    stack_yaml = stack.to_yaml()
    generated = {
        f"{item['kind']}/{item['metadata']['name']}": item
        for item in yaml.safe_load_all(stack_yaml)
    }

    deploy = generated["Deployment/a-deploy"]
    assert deploy["apiVersion"] == "apps/v1"
    assert deploy["spec"]["replicas"] == 2

    daemonset = generated["DaemonSet/a-daemonset"]
    assert daemonset["apiVersion"] == "apps/v1"


def test_stack_to_chart():
    stack = Stack(
        name="my-stack",
        deployments=[Deployment(name="a-deploy", image="bar", replicas=2)],
        daemonsets=[Daemonset(name="a-daemonset", image="bar")],
        statefulsets=[Statefulset(name="a-statefulset", image="bar")],
    )
    files = dict(stack.chart.generate_files())
    assert list(files.keys()) == [
        "Chart.yaml",
        "templates/deployment-a-deploy.yml",
        "templates/daemonset-a-daemonset.yml",
        "templates/statefulset-a-statefulset.yml",
    ]


def test_stack_dump():
    stack = Stack(
        name="my-stack",
        deployments=[Deployment(name="a-deploy", image="bar", replicas=2)],
        daemonsets=[Daemonset(name="a-daemonset", image="bar")],
        statefulsets=[Statefulset(name="a-statefulset", image="bar")],
    )

    with TemporaryDirectory() as location:
        stack.chart.dump(location)
        assert os.listdir(location) == ["templates", "Chart.yaml"]
        assert set(os.listdir(os.path.join(location, "templates"))) == {
            "deployment-a-deploy.yml",
            "daemonset-a-daemonset.yml",
            "statefulset-a-statefulset.yml",
        }


@mock.patch("k8s_app_abstraction.models.stack.config")
@mock.patch("k8s_app_abstraction.models.stack.client")
def test_stack_install(mock_client, mock_config):
    # Force compatibility with mocked kubernetes api and library version
    kver = kubernetes.__version__.split(".")[0]
    mock_client.VersionApi().get_code().git_version = f"v1.{kver}.0"
    mock_client.VersionApi().get_code().minor = kver
    stack = Stack(
        name="my-stack",
        deployments=[Deployment(name="a-deploy", image="bar", replicas=2)],
        daemonsets=[Daemonset(name="a-daemonset", image="bar")],
        statefulsets=[Statefulset(name="a-statefulset", image="bar")],
    )

    with TemporaryDirectory() as location:
        with mock.patch(
            "k8s_app_abstraction.models.stack.check_output"
        ) as check_output:
            stack.chart.rollout(location)

        check_output.assert_called_once_with(
            ["helm", "upgrade", "--install", "my-stack", location], stderr=STDOUT
        )
