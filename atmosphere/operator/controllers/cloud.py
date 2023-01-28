import kopf

from atmosphere import clients
from atmosphere.models import config
from atmosphere.operator.api import Cloud, objects, types
from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm


@kopf.on.resume(Cloud.version, Cloud.kind)
@kopf.on.create(Cloud.version, Cloud.kind)
def create_fn(namespace: str, name: str, spec: dict, **_):
    cfg = config.Config.from_file()
    api = clients.get_pykube_api()

    objects.Namespace(
        api=api,
        metadata=types.ObjectMeta(
            name=constants.NAMESPACE_MONITORING,
        ),
    ).apply()

    if cfg.kube_prometheus_stack.enabled:
        objects.HelmRepository(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name=constants.HELM_REPOSITORY_PROMETHEUS_COMMUINTY,
                namespace=cfg.kube_prometheus_stack.namespace,
            ),
            spec=types.HelmRepositorySpec(
                url=constants.HELM_REPOSITORY_PROMETHEUS_COMMUINTY_URL,
            ),
        ).apply()
        objects.HelmRelease(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                namespace=cfg.kube_prometheus_stack.namespace,
            ),
            spec=types.HelmReleaseSpec(
                chart=types.HelmChartTemplate(
                    spec=types.HelmChartTemplateSpec(
                        chart=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                        version=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
                        source_ref=types.CrossNamespaceObjectReference(
                            kind="HelmRepository",
                            name=constants.HELM_REPOSITORY_PROMETHEUS_COMMUINTY,
                            namespace=cfg.kube_prometheus_stack.namespace,
                        ),
                    )
                ),
                values={
                    **constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
                    **cfg.kube_prometheus_stack.overrides,
                    **{
                        "alertmanager": {
                            "config": openstack_helm.generate_alertmanager_config_for_opsgenie(
                                cfg.opsgenie
                            )
                        }
                    },
                },
            ),
        ).apply()
