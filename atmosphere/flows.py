from taskflow import engines
from taskflow.patterns import graph_flow

from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm
from atmosphere.tasks.kubernetes import v1


def get_engine(config):
    return engines.load(
        get_deployment_flow(config),
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )


def get_deployment_flow(config):
    flow = graph_flow.Flow("deploy").add(
        # monitoring
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_MONITORING),
        *openstack_helm.kube_prometheus_stack_tasks_from_config(
            config.kube_prometheus_stack,
            opsgenie=config.opsgenie,
        ),
        # openstack
        v1.ApplyNamespaceTask(name=constants.NAMESPACE_OPENSTACK),
        *openstack_helm.ingress_nginx_tasks_from_config(config.ingress_nginx),
    )

    return flow
