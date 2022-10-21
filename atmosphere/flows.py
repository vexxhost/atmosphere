from taskflow import engines
from taskflow.patterns import graph_flow

from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm
from atmosphere.tasks.kubernetes import cert_manager, flux, v1


def get_engine(config):
    return engines.load(
        get_deployment_flow(config),
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )


def get_deployment_flow(config):
    flow = graph_flow.Flow("deploy").add(
        # kube-system
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_KUBE_SYSTEM),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_KUBE_SYSTEM,
            name=constants.HELM_REPOSITORY_CEPH,
            url="https://ceph.github.io/csi-charts",
        ),
        # cert-manager
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_CERT_MANAGER),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_CERT_MANAGER,
            name=constants.HELM_REPOSITORY_JETSTACK,
            url="https://charts.jetstack.io",
        ),
        flux.ApplyHelmReleaseTask(
            namespace=constants.NAMESPACE_CERT_MANAGER,
            name=constants.HELM_RELEASE_CERT_MANAGER_NAME,
            repository=constants.HELM_REPOSITORY_JETSTACK,
            chart=constants.HELM_RELEASE_CERT_MANAGER_NAME,
            version=constants.HELM_RELEASE_CERT_MANAGER_VERSION,
            values=constants.HELM_RELEASE_CERT_MANAGER_VALUES,
        ),
        *cert_manager.issuer_tasks_from_config(config.issuer),
        # monitoring
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_MONITORING),
        *openstack_helm.kube_prometheus_stack_tasks_from_config(
            config.kube_prometheus_stack
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_MONITORING,
            name=constants.HELM_REPOSITORY_NODE_FEATURE_DISCOVERY,
            url="https://kubernetes-sigs.github.io/node-feature-discovery/charts",
        ),
        flux.ApplyHelmReleaseTask(
            namespace=constants.NAMESPACE_MONITORING,
            name="node-feature-discovery",
            repository=constants.HELM_REPOSITORY_NODE_FEATURE_DISCOVERY,
            chart="node-feature-discovery",
            version="0.11.2",
            values=constants.HELM_RELEASE_NODE_FEATURE_DISCOVERY_VALUES,
        ),
        # openstack
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_OPENSTACK),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_REPOSITORY_BITNAMI,
            url="https://charts.bitnami.com/bitnami",
        ),
        flux.ApplyHelmReleaseTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
            repository=constants.HELM_REPOSITORY_BITNAMI,
            chart=constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
            version=constants.HELM_RELEASE_RABBITMQ_OPERATOR_VERSION,
            values=constants.HELM_RELEASE_RABBITMQ_OPERATOR_VALUES,
            requires=constants.HELM_RELEASE_RABBITMQ_OPERATOR_REQUIRES,
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_REPOSITORY_PERCONA,
            url="https://percona.github.io/percona-helm-charts/",
        ),
        flux.ApplyHelmReleaseTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_RELEASE_PXC_OPERATOR_NAME,
            repository=constants.HELM_REPOSITORY_PERCONA,
            chart=constants.HELM_RELEASE_PXC_OPERATOR_NAME,
            version=constants.HELM_RELEASE_PXC_OPERATOR_VERSION,
            values=constants.HELM_RELEASE_PXC_OPERATOR_VALUES,
        ),
        openstack_helm.ApplyPerconaXtraDBClusterTask(),
        *openstack_helm.ingress_nginx_tasks_from_config(config.ingress_nginx),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_REPOSITORY_OPENSTACK_HELM_INFRA,
            url="https://tarballs.opendev.org/openstack/openstack-helm-infra/",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_REPOSITORY_COREDNS,
            url="https://coredns.github.io/helm",
        ),
        flux.ApplyHelmRepositoryTask(
            namespace=constants.NAMESPACE_OPENSTACK,
            name=constants.HELM_REPOSITORY_OPENSTACK_HELM,
            url="https://tarballs.opendev.org/openstack/openstack-helm/",
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_KEYSTONE_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_BARBICAN_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_GLANCE_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_CINDER_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_NEUTRON_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_NOVA_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_OCTAVIA_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_SENLIN_NAME,
        ),
        openstack_helm.ApplyRabbitmqClusterTask(
            name=constants.HELM_RELEASE_HEAT_NAME,
        ),
    )

    if config.memcached.enabled:
        flow.add(
            openstack_helm.ApplyReleaseSecretTask(
                config=config,
                namespace=config.memcached.namespace,
                chart="memcached",
            ),
            openstack_helm.ApplyHelmReleaseTask(
                namespace=config.memcached.namespace,
                repository=constants.HELM_REPOSITORY_OPENSTACK_HELM_INFRA,
                name="memcached",
                version="0.1.12",
            ),
            v1.ApplyServiceTask(
                namespace=config.memcached.namespace,
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
                            "protocol": "TCP",
                            "port": 9150,
                            "targetPort": 9150,
                        }
                    ],
                },
            ),
        )

    return flow
