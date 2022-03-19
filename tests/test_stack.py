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

    deploy = generated["Daemonset/a-daemonset"]
    assert deploy["apiVersion"] == "apps/v1"
