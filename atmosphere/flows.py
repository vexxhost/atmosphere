from taskflow import engines
from taskflow.patterns import graph_flow

from atmosphere import clients
from atmosphere.operator.api import objects, types
from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm
from atmosphere.tasks.kubernetes import cert_manager, rook, v1
from atmosphere.tasks.kubernetes import cert_manager, v1


def get_engine(config):
    api = clients.get_pykube_api()

    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_CEPH,
            namespace=constants.NAMESPACE_KUBE_SYSTEM,
        ),
        spec=types.HelmRepositorySpec(
            url="https://ceph.github.io/csi-charts",
        ),
    ).apply()

    if config.ingress_nginx.enabled:
        objects.HelmRepository(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name=constants.HELM_REPOSITORY_INGRESS_NGINX,
                namespace=config.ingress_nginx.namespace,
            ),
            spec=types.HelmRepositorySpec(
                url=constants.HELM_REPOSITORY_INGRESS_NGINX_URL,
            ),
        ).apply()
        objects.HelmRelease(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name=constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                namespace=config.ingress_nginx.namespace,
            ),
            spec=types.HelmReleaseSpec(
                chart=types.HelmChartTemplate(
                    spec=types.HelmChartTemplateSpec(
                        chart=constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                        version=constants.HELM_RELEASE_INGRESS_NGINX_VERSION,
                        source_ref=types.CrossNamespaceObjectReference(
                            kind="HelmRepository",
                            name=constants.HELM_REPOSITORY_INGRESS_NGINX,
                            namespace=config.ingress_nginx.namespace,
                        ),
                    )
                ),
                values={
                    **constants.HELM_RELEASE_INGRESS_NGINX_VALUES,
                    **config.ingress_nginx.overrides,
                },
            ),
        ).apply()

    # NOTE(mnaser): We're running this first since we do get often timeouts
    #               when waiting for the self-signed certificate authority to
    #               be ready.
    objects.Namespace(
        api=api,
        metadata=types.ObjectMeta(
            name=constants.NAMESPACE_CERT_MANAGER,
        ),
    ).apply()
    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_JETSTACK,
            namespace=constants.NAMESPACE_CERT_MANAGER,
        ),
        spec=types.HelmRepositorySpec(
            url="https://charts.jetstack.io",
        ),
    ).apply()
    objects.HelmRelease(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_RELEASE_CERT_MANAGER_NAME,
            namespace=constants.NAMESPACE_CERT_MANAGER,
        ),
        spec=types.HelmReleaseSpec(
            chart=types.HelmChartTemplate(
                spec=types.HelmChartTemplateSpec(
                    chart=constants.HELM_RELEASE_CERT_MANAGER_NAME,
                    version=constants.HELM_RELEASE_CERT_MANAGER_VERSION,
                    source_ref=types.CrossNamespaceObjectReference(
                        kind="HelmRepository",
                        name=constants.HELM_REPOSITORY_JETSTACK,
                        namespace=constants.NAMESPACE_CERT_MANAGER,
                    ),
                )
            ),
            depends_on=[
                types.NamespacedObjectReference(
                    name=constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                    namespace=config.ingress_nginx.namespace,
                )
            ],
            values=constants.HELM_RELEASE_CERT_MANAGER_VALUES,
        ),
    ).apply()

    objects.Namespace(
        api=api,
        metadata=types.ObjectMeta(
            name=constants.NAMESPACE_MONITORING,
        ),
    ).apply()
    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_NODE_FEATURE_DISCOVERY,
            namespace=constants.NAMESPACE_MONITORING,
        ),
        spec=types.HelmRepositorySpec(
            url="https://kubernetes-sigs.github.io/node-feature-discovery/charts",
        ),
    ).apply()
    objects.HelmRelease(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name="node-feature-discovery",
            namespace=constants.NAMESPACE_MONITORING,
        ),
        spec=types.HelmReleaseSpec(
            chart=types.HelmChartTemplate(
                spec=types.HelmChartTemplateSpec(
                    chart="node-feature-discovery",
                    version="0.11.2",
                    source_ref=types.CrossNamespaceObjectReference(
                        kind="HelmRepository",
                        name=constants.HELM_REPOSITORY_NODE_FEATURE_DISCOVERY,
                        namespace=constants.NAMESPACE_MONITORING,
                    ),
                )
            ),
            values=constants.HELM_RELEASE_NODE_FEATURE_DISCOVERY_VALUES,
        ),
    ).apply()

    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_BITNAMI,
            namespace=constants.NAMESPACE_OPENSTACK,
        ),
        spec=types.HelmRepositorySpec(
            url="https://charts.bitnami.com/bitnami",
        ),
    ).apply()
    objects.HelmRelease(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
            namespace=constants.NAMESPACE_OPENSTACK,
        ),
        spec=types.HelmReleaseSpec(
            chart=types.HelmChartTemplate(
                spec=types.HelmChartTemplateSpec(
                    chart=constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
                    version=constants.HELM_RELEASE_RABBITMQ_OPERATOR_VERSION,
                    source_ref=types.CrossNamespaceObjectReference(
                        kind="HelmRepository",
                        name=constants.HELM_REPOSITORY_BITNAMI,
                        namespace=constants.NAMESPACE_OPENSTACK,
                    ),
                )
            ),
            depends_on=[
                types.NamespacedObjectReference(
                    name=constants.HELM_RELEASE_CERT_MANAGER_NAME,
                    namespace=constants.NAMESPACE_CERT_MANAGER,
                )
            ],
            values=constants.HELM_RELEASE_RABBITMQ_OPERATOR_VALUES,
        ),
    ).apply()
    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_OPENSTACK_HELM_INFRA,
            namespace=constants.NAMESPACE_OPENSTACK,
        ),
        spec=types.HelmRepositorySpec(
            url="https://tarballs.opendev.org/openstack/openstack-helm-infra/",
        ),
    ).apply()
    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_COREDNS,
            namespace=constants.NAMESPACE_OPENSTACK,
        ),
        spec=types.HelmRepositorySpec(url="https://coredns.github.io/helm"),
    ).apply()
    objects.HelmRepository(
        api=api,
        metadata=types.NamespacedObjectMeta(
            name=constants.HELM_REPOSITORY_OPENSTACK_HELM,
            namespace=constants.NAMESPACE_OPENSTACK,
        ),
        spec=types.HelmRepositorySpec(
            url="https://tarballs.opendev.org/openstack/openstack-helm/",
        ),
    ).apply()

    if config.kube_prometheus_stack.enabled:
        objects.HelmRepository(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name=constants.HELM_REPOSITORY_PROMETHEUS_COMMUINTY,
                namespace=config.kube_prometheus_stack.namespace,
            ),
            spec=types.HelmRepositorySpec(
                url=constants.HELM_REPOSITORY_PROMETHEUS_COMMUINTY_URL,
            ),
        ).apply()
        objects.HelmRelease(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                namespace=config.kube_prometheus_stack.namespace,
            ),
            spec=types.HelmReleaseSpec(
                chart=types.HelmChartTemplate(
                    spec=types.HelmChartTemplateSpec(
                        chart=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                        version=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
                        source_ref=types.CrossNamespaceObjectReference(
                            kind="HelmRepository",
                            name=constants.HELM_REPOSITORY_PROMETHEUS_COMMUINTY,
                            namespace=config.kube_prometheus_stack.namespace,
                        ),
                    )
                ),
                depends_on=[
                    types.NamespacedObjectReference(
                        name=constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
                        namespace=constants.NAMESPACE_OPENSTACK,
                    ),
                    types.NamespacedObjectReference(
                        name="node-feature-discovery",
                        namespace=constants.NAMESPACE_MONITORING,
                    ),
                ],
                values={
                    **constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
                    **config.kube_prometheus_stack.overrides,
                    **{
                        "alertmanager": {
                            "config": openstack_helm.generate_alertmanager_config_for_opsgenie(
                                config.opsgenie
                            )
                        }
                    },
                },
            ),
        ).apply()

    return engines.load(
        get_deployment_flow(config),
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )


# TODO(mnaser): Move this into the Cloud CRD
def get_deployment_flow(config):
    flow = graph_flow.Flow("deploy").add(
        # kube-system
        *rook.tasks_from_config(config),
        # cert-manager
        *cert_manager.issuer_tasks_from_config(config.issuer),
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
