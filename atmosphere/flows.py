from taskflow.patterns import graph_flow

from atmosphere.config import CONF
from atmosphere.tasks.composite import openstack_helm
from atmosphere.tasks.kubernetes import flux, v1

NAMESPACE_CERT_MANAGER = "cert-manager"
NAMESPACE_KUBE_SYSTEM = "kube-system"
NAMESPACE_MONITORING = "monitoring"
NAMESPACE_OPENSTACK = "openstack"

HELM_REPOSITORY_BITNAMI = "bitnami"
HELM_REPOSITORY_CEPH = "ceph"
HELM_REPOSITORY_COREDNS = "coredns"
HELM_REPOSITORY_INGRESS_NGINX = "ingress-nginx"
HELM_REPOSITORY_JETSTACK = "jetstack"
HELM_REPOSITORY_NODE_FEATURE_DISCOVERY = "node-feature-discovery"
HELM_REPOSITORY_OPENSTACK_HELM = "openstack-helm"
HELM_REPOSITORY_OPENSTACK_HELM_INFRA = "openstack-helm-infra"
HELM_REPOSITORY_PERCONA = "percona"
HELM_REPOSITORY_PROMETHEUS_COMMUINTY = "prometheus-community"

CONTROL_PLANE_NODE_SELECTOR = {
    "openstack-control-plane": "enabled",
}

NODE_FEATURE_DISCOVERY_VALUES = {
    "master": {"nodeSelector": CONTROL_PLANE_NODE_SELECTOR}
}

PERCONA_XTRADB_OPERATOR_VALUES = {
    "nodeSelector": CONTROL_PLANE_NODE_SELECTOR,
}


def get_deployment_flow():
    flow = graph_flow.Flow("deploy").add(
        # kube-system
        v1.ApplyNamespaceTask(name=NAMESPACE_KUBE_SYSTEM),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_KUBE_SYSTEM,
            name=HELM_REPOSITORY_CEPH,
            url="https://ceph.github.io/csi-charts",
        ),
        # cert-manager
        v1.ApplyNamespaceTask(name=NAMESPACE_CERT_MANAGER),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_CERT_MANAGER,
            name=HELM_REPOSITORY_JETSTACK,
            url="https://charts.jetstack.io",
        ),
        # monitoring
        v1.ApplyNamespaceTask(name=NAMESPACE_MONITORING),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_MONITORING,
            name=HELM_REPOSITORY_PROMETHEUS_COMMUINTY,
            url="https://prometheus-community.github.io/helm-charts",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_MONITORING,
            name=HELM_REPOSITORY_NODE_FEATURE_DISCOVERY,
            url="https://kubernetes-sigs.github.io/node-feature-discovery/charts",
        ),
        flux.ApplyHelmReleaseTask(
            namespace=NAMESPACE_MONITORING,
            name="node-feature-discovery",
            repository=HELM_REPOSITORY_NODE_FEATURE_DISCOVERY,
            chart="node-feature-discovery",
            version="0.11.2",
            values=NODE_FEATURE_DISCOVERY_VALUES,
        ),
        # openstack
        v1.ApplyNamespaceTask(name=NAMESPACE_OPENSTACK),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_OPENSTACK,
            name=HELM_REPOSITORY_BITNAMI,
            url="https://charts.bitnami.com/bitnami",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_OPENSTACK,
            name=HELM_REPOSITORY_PERCONA,
            url="https://percona.github.io/percona-helm-charts/",
        ),
        flux.ApplyHelmReleaseTask(
            namespace=NAMESPACE_OPENSTACK,
            name="pxc-operator",
            repository=HELM_REPOSITORY_PERCONA,
            chart="pxc-operator",
            version="1.10.0",
            values=PERCONA_XTRADB_OPERATOR_VALUES,
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_OPENSTACK,
            name=HELM_REPOSITORY_INGRESS_NGINX,
            url="https://kubernetes.github.io/ingress-nginx",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_OPENSTACK,
            name=HELM_REPOSITORY_OPENSTACK_HELM_INFRA,
            url="https://tarballs.opendev.org/openstack/openstack-helm-infra/",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_OPENSTACK,
            name=HELM_REPOSITORY_COREDNS,
            url="https://coredns.github.io/helm",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=NAMESPACE_OPENSTACK,
            name=HELM_REPOSITORY_OPENSTACK_HELM,
            url="https://tarballs.opendev.org/openstack/openstack-helm/",
        ),
    )

    if CONF.memcached.enabled:
        flow.add(
            openstack_helm.ApplyReleaseSecretTask(
                namespace=NAMESPACE_OPENSTACK, chart="memcached"
            ),
            openstack_helm.ApplyHelmReleaseTask(
                namespace=NAMESPACE_OPENSTACK,
                repository=HELM_REPOSITORY_OPENSTACK_HELM_INFRA,
                name="memcached",
                version="0.1.12",
            ),
            v1.ApplyServiceTask(
                namespace=NAMESPACE_OPENSTACK,
                name="memcached-metrics",
                labels={
                    "application": "memcached",
                    "component": "server",
                },
                spec={
                    "selector": {
                        "application": "memcached",
                        "component": "server",
                    },
                    "ports": [
                        {
                            "name": "metrics",
                            "port": 9150,
                            "targetPort": 9150,
                        }
                    ],
                },
            ),
        )

    return flow
