from taskflow.patterns import graph_flow

from atmosphere.config import CONF
from atmosphere.tasks import flux, kubernetes, openstack_helm


def generate_for_openstack_helm_chart(chart):
    flow = graph_flow.Flow(chart)

    if getattr(CONF, chart).enabled:
        flow.add(
            openstack_helm.GenerateReleaseSecretTask(inject={"chart": chart}),
            kubernetes.EnsureSecretTask(),
        )

    return flow


DEPLOY = graph_flow.Flow("deploy").add(
    flux.EnsureHelmRepositoryTask(
        provides="openstack-helm-infra",
        inject={
            "namespace": "openstack",
            "name": "openstack-helm-infra",
            "url": "https://tarballs.opendev.org/openstack/openstack-helm-infra/",
        },
    ),
    generate_for_openstack_helm_chart("memcached"),
)
