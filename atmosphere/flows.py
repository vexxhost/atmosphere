from taskflow.patterns import graph_flow, linear_flow

from atmosphere.config import CONF
from atmosphere.tasks import kubernetes, openstack_helm


def generate_for_openstack_helm_chart(chart):
    flow = graph_flow.Flow(chart)

    if getattr(CONF, chart).enabled:
        flow.add(
            openstack_helm.GenerateReleaseSecretTask(inject={"chart": chart}),
            kubernetes.EnsureSecretTask(),
        )

    return flow


DEPLOY = linear_flow.Flow("deploy").add(
    generate_for_openstack_helm_chart("memcached"),
)
