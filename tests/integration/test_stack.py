from contextlib import AbstractContextManager, closing
from tempfile import TemporaryDirectory

import pytest

from k8s_app_abstraction.models.pod_controllers import (
    Daemonset,
    Deployment,
    Statefulset,
)
from k8s_app_abstraction.models.stack import HelmChart, Stack


class ephemeral_rollout(AbstractContextManager):
    """Context to automatically uninstall a rollout."""

    def __init__(self, chart: HelmChart, *args, **kwargs):
        self.chart = chart
        self.args = (args,)
        self.kwargs = kwargs

    def __enter__(self):
        return self.chart.rollout(*self.args, **self.kwargs)

    def __exit__(self, *exc_info):
        self.chart.uninstall()


@pytest.mark.integration
def test_stack_install():
    stack = Stack(
        name="my-stack",
        deployments=[Deployment(name="a-deploy", image="bar", replicas=2)],
        daemonsets=[Daemonset(name="a-daemonset", image="bar")],
        statefulsets=[Statefulset(name="a-statefulset", image="bar")],
    )

    chart = stack.chart

    # Performs a `helm upgrade --install` against a real kubernetes cluster
    # Uninstall the named release at exit
    with ephemeral_rollout(chart):
        k8s_resources = {}
        for res in chart.get_kubernetes_resources():
            k8s_resources[f"{res.kind}/{res.metadata.name}"] = res

        assert k8s_resources["Deployment/a-deploy"].spec.replicas == 2
        assert (
            k8s_resources["Deployment/a-deploy"].spec.template.spec.containers[0].image
            == "bar"
        )
        assert k8s_resources["StatefulSet/a-statefulset"].spec.replicas == 1
        assert (
            k8s_resources["StatefulSet/a-statefulset"]
            .spec.template.spec.containers[0]
            .image
            == "bar"
        )
        assert (
            k8s_resources["DaemonSet/a-daemonset"]
            .spec.template.spec.containers[0]
            .image
            == "bar"
        )
