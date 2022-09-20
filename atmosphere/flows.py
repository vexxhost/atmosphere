from taskflow.patterns import graph_flow

from atmosphere.config import CONF
from atmosphere.tasks import flux, kubernetes, openstack_helm

HELM_REPOSITORIES_BY_NAMESPACE = {
    "kube-system": {
        "ceph": "https://ceph.github.io/csi-charts",
    },
    "openstack": {
        "bitnami": "https://charts.bitnami.com/bitnami",
        "coredns": "https://coredns.github.io/helm",
        "ingress-nginx": "https://kubernetes.github.io/ingress-nginx",
        "openstack-helm-infra": "https://tarballs.opendev.org/openstack/openstack-helm-infra/",
        "openstack-helm": "https://tarballs.opendev.org/openstack/openstack-helm/",
        "percona": "https://percona.github.io/percona-helm-charts/",
    },
}

OPENSTACK_HELM_CHARTS_BY_NAMESPACE = {
    "openstack": ["memcached"],
}


def generate_for_openstack_helm_chart(chart):
    flow = graph_flow.Flow(chart)

    if getattr(CONF, chart).enabled:
        flow.add(
            openstack_helm.GenerateReleaseSecretTask(inject={"chart": chart}),
            kubernetes.EnsureSecretTask(),
        )

    return flow


def get_deployment_flow():
    flow = graph_flow.Flow("deploy")

    for namespace, repos in HELM_REPOSITORIES_BY_NAMESPACE.items():
        for repo, url in repos.items():
            task = flux.EnsureHelmRepositoryTask(
                name=repo,
                inject={"namespace": namespace, "name": repo, "url": url},
                provides=f"helm-repository-{repo}",
            )
            flow.add(task)

    for namespace, charts in OPENSTACK_HELM_CHARTS_BY_NAMESPACE.items():
        for chart in charts:
            flow.add(generate_for_openstack_helm_chart(chart))

    return flow


DEPLOY = get_deployment_flow()
