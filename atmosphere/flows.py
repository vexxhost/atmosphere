from taskflow import engines
from taskflow.patterns import graph_flow

from atmosphere import clients
from atmosphere.operator.api import objects, types
from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm
from atmosphere.tasks.kubernetes import cert_manager


def get_engine(config):
    api = clients.get_pykube_api()

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

    objects.Namespace(
        api=api,
        metadata=types.ObjectMeta(
            name=constants.NAMESPACE_MONITORING,
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
        # cert-manager
        *cert_manager.issuer_tasks_from_config(config.issuer),
    )

    return flow
