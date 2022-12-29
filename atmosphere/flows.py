from taskflow import engines
from taskflow.patterns import graph_flow

from atmosphere import utils
from atmosphere.operator import tasks
from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm
from atmosphere.tasks.kubernetes import cert_manager


def get_engine(config):
    return engines.load(
        get_deployment_flow(config),
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )


def get_deployment_flow(config):
    flow = graph_flow.Flow("deploy").add(
        tasks.BuildApiClient(),
        # openstack
        tasks.ApplyNamespaceTask(
            constants.NAMESPACE_OPENSTACK, provides="openstack_namespace"
        ),
        tasks.ApplyHelmRepositoryTask(
            inject={
                "repository_name": "atmosphere",
                "url": "http://atmosphere.openstack/charts/",
            },
            provides="helm_repository",
            rebind={
                "namespace": "openstack_namespace",
            },
        ),
        # kube-system
        tasks.ApplyNamespaceTask(
            constants.NAMESPACE_KUBE_SYSTEM, provides="kube_system_namespace"
        ),
        # cert-manager
        tasks.ApplyNamespaceTask(
            constants.NAMESPACE_CERT_MANAGER, provides="cert_manager_namespace"
        ),
        tasks.ApplyHelmReleaseTask(
            config={
                "chart_name": constants.HELM_RELEASE_CERT_MANAGER_NAME,
                "chart_version": constants.HELM_RELEASE_CERT_MANAGER_VERSION,
                "release_name": constants.HELM_RELEASE_CERT_MANAGER_NAME,
                "values": constants.HELM_RELEASE_CERT_MANAGER_VALUES,
                "spec": {},
                "values_from": [],
            },
            rebind={
                "namespace": "cert_manager_namespace",
            },
        ),
        *cert_manager.issuer_tasks_from_config(config.issuer),
        # monitoring
        tasks.ApplyNamespaceTask(
            constants.NAMESPACE_MONITORING, provides="monitoring_namespace"
        ),
        *openstack_helm.kube_prometheus_stack_tasks_from_config(
            config.kube_prometheus_stack,
            opsgenie=config.opsgenie,
        ),
        tasks.ApplyHelmReleaseTask(
            config={
                "chart_name": "node-feature-discovery",
                "chart_version": "0.11.2",
                "release_name": "node-feature-discovery",
                "values": constants.HELM_RELEASE_NODE_FEATURE_DISCOVERY_VALUES,
                "spec": {},
                "values_from": [],
            },
            rebind={
                "namespace": "monitoring_namespace",
            },
        ),
        tasks.ApplyHelmReleaseTask(
            config={
                "chart_name": constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
                "chart_version": constants.HELM_RELEASE_RABBITMQ_OPERATOR_VERSION,
                "release_name": constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME,
                "values": constants.HELM_RELEASE_RABBITMQ_OPERATOR_VALUES,
                "spec": {},
                "values_from": [],
            },
            rebind={
                "namespace": "openstack_namespace",
            },
        ),
        tasks.ApplyHelmReleaseTask(
            config={
                "chart_name": constants.HELM_RELEASE_PXC_OPERATOR_NAME,
                "chart_version": constants.HELM_RELEASE_PXC_OPERATOR_VERSION,
                "release_name": constants.HELM_RELEASE_PXC_OPERATOR_NAME,
                "values": constants.HELM_RELEASE_PXC_OPERATOR_VALUES,
                "spec": {},
                "values_from": [],
            },
            rebind={
                "namespace": "openstack_namespace",
            },
        ),
        tasks.ApplyPerconaXtraDBClusterTask(
            inject={
                "spec": {
                    "imageRepository": utils.get_legacy_image_repository(),
                },
            },
            rebind={
                "namespace": "openstack_namespace",
                "pxc_operator_helm_release": "pxc_operator_helm_release",
            },
        ),
        *openstack_helm.ingress_nginx_tasks_from_config(config.ingress_nginx),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_KEYSTONE_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_BARBICAN_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_GLANCE_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_CINDER_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_NEUTRON_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_NOVA_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_OCTAVIA_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_SENLIN_NAME),
        tasks.ApplyRabbitmqClusterTask(constants.HELM_RELEASE_HEAT_NAME),
    )

    if config.memcached.enabled:
        flow.add(
            openstack_helm.ApplyReleaseSecretTask(
                config=config,
                chart="memcached",
                rebind={
                    "namespace": "openstack_namespace",
                },
            ),
            tasks.ApplyHelmReleaseTask(
                config={
                    "chart_name": "memcached",
                    "chart_version": "0.1.12",
                    "release_name": "memcached",
                    "values": constants.HELM_RELEASE_PXC_OPERATOR_VALUES,
                    "values_from": [
                        {
                            "kind": "Secret",
                            "name": "atmosphere-memcached",
                        }
                    ],
                    "spec": {},
                },
                rebind={
                    "namespace": "openstack_namespace",
                },
            ),
            tasks.ApplyServiceTask(
                name="memcached-metrics",
                inject={
                    "labels": {
                        "application": "memcached",
                        "component": "server",
                    },
                    "ports": [
                        {
                            "name": "metrics",
                            "port": 9150,
                            "targetPort": 9150,
                        },
                    ],
                },
                rebind={
                    "namespace": "openstack_namespace",
                },
            ),
        )

    return flow
