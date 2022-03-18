from textwrap import dedent

import pytest
from pydantic import ValidationError

from k8s_app_abstraction.models.pod_controllers import (
    Daemonset,
    Deployment,
    Statefulset,
)
from k8s_app_abstraction.models.stack import Stack


def test_deployment():
    deploy = Deployment(name="foo", image="my/image")
    assert deploy.image == "my/image"
    assert deploy.replicas == 1


def test_deployment_yaml():
    stack = Stack.new(
        name="yaml-stack",
        definition=dedent(
            """
            deployments:
              foo:
                image: bar
                replicas: 3
            """
        ),
    )

    assert stack.deployments[0].image == "bar"
    assert stack.deployments[0].replicas == 3


def test_deployment_yaml_invalid():
    with pytest.raises(ValidationError) as e:
        Stack.new(
            name="yaml-stack",
            definition=dedent(
                """
                deployments: yes
                """
            ),
        )

    assert e.value.errors()[0]["msg"] == "Invalid value for DeploymentList"


def test_statefulset():
    deploy = Statefulset(name="foo", image="my/image")
    assert deploy.image == "my/image"
    assert deploy.replicas == 1


def test_statefulset_yaml():
    stack = Stack.new(
        name="yaml-stack",
        definition=dedent(
            """
            statefulsets:
              foo:
                image: bar
                replicas: 2
            """
        ),
    )

    assert stack.statefulsets[0].image == "bar"
    assert stack.statefulsets[0].replicas == 2


def test_statefulset_yaml_invalid():
    with pytest.raises(ValidationError) as e:
        Stack.new(
            name="yaml-stack",
            definition=dedent(
                """
                statefulsets: 3
                """
            ),
        )

    assert e.value.errors()[0]["msg"] == "Invalid value for StatefulsetList"


def test_daemonset():
    deploy = Daemonset(name="foo", image="my/image")
    assert deploy.image == "my/image"


def test_daemonset_yaml():
    stack = Stack.new(
        name="yaml-stack",
        definition=dedent(
            """
            daemonsets:
              foo:
                image: bar
            """
        ),
    )

    assert stack.daemonsets[0].image == "bar"


def test_daemonset_yaml_invalid():
    with pytest.raises(ValidationError) as e:
        Stack.new(
            name="yaml-stack",
            definition=dedent(
                """
                daemonsets: no
                """
            ),
        )

    assert e.value.errors()[0]["msg"] == "Invalid value for DaemonsetList"
