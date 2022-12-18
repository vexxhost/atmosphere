import logging

import kopf
from taskflow import engines, exceptions
from taskflow.listeners import logging as logging_listener
from taskflow.patterns import graph_flow

from atmosphere import flows
from atmosphere.models import config
from atmosphere.operator import constants, tasks
from atmosphere.operator.api import Cloud


@kopf.on.resume(Cloud.version, Cloud.kind)
@kopf.on.create(Cloud.version, Cloud.kind)
def create_fn(namespace: str, name: str, spec: dict, **_):
    flow = graph_flow.Flow("deploy").add(
        tasks.BuildApiClient(),
        tasks.ApplyNamespaceTask(namespace),
        tasks.ApplyHelmRepositoryTask(
            inject={
                "repository_name": "atmosphere",
                "url": "http://atmosphere.openstack/charts/",
            },
            provides="helm_repository",
        ),
        tasks.GenerateImageTagsConfigMap(provides="image_tags"),
        tasks.GenerateSecrets(provides="secrets"),
    )

    if spec["certManager"]["enabled"]:
        flow.add(
            tasks.ApplyNamespaceTask(
                name=constants.NAMESPACE_CERT_MANAGER,
                provides="cert_manager_namespace",
            ),
            tasks.ApplyHelmReleaseTask(
                config=constants.HELM_RELEASE_CERT_MANAGER,
                rebind={"namespace": "cert_manager_namespace"},
            ),
            tasks.ApplyClusterIssuerTask(provides="cluster_issuer"),
        )
    else:
        flow.add(
            tasks.GetClusterIssuerTask(provides="cluster_issuer"),
        )

    if spec["memcached"]["enabled"]:
        flow.add(
            tasks.GetChartValues(
                chart_name="memcached",
                chart_version="0.1.12",
            ),
            tasks.GenerateOpenStackHelmReleaseValues(
                inject={"chart_name": "memcached"},
                provides="memcached_release_values",
            ),
            tasks.GenerateOpenStackHelmValuesFrom(
                inject={"chart_name": "memcached"},
                rebind={
                    "chart_values": "memcached_chart_values",
                },
                provides="memcached_values_from",
            ),
            tasks.ApplyHelmReleaseTask(
                config={
                    "chart_name": "memcached",
                    "chart_version": "0.1.12",
                    "release_name": "memcached",
                },
                rebind={
                    "values": "memcached_release_values",
                    "values_from": "memcached_values_from",
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
            ),
        )

    if spec["ingressNginx"]["enabled"]:
        flow.add(
            tasks.ApplyHelmReleaseTask(
                config=constants.HELM_RELEASE_INGRESS_NGINX,
            ),
        )

    flow.add(
        # TODO(mnaser): We need to find a way to create a dependency on
        #               cert-manager being enabled.
        tasks.ApplyHelmReleaseTask(
            config=constants.HELM_RELEASE_RABBITMQ_CLUSTER_OPERATOR,
        ),
        tasks.ApplyHelmReleaseTask(
            config=constants.HELM_RELEASE_PXC_OPERATOR,
        ),
        tasks.ApplyPerconaXtraDBClusterTask(
            provides="percona_xtradb_cluster",
        ),
    )

    if spec["keystone"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("keystone"))

    if spec["barbican"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("barbican"))

    if spec["glance"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("glance"))

    if spec["cinder"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("cinder"))

    if spec["neutron"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("neutron"))

    if spec["nova"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("nova"))

    if spec["octavia"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("octavia"))

    if spec["magnum"]["enabled"]:
        flow.add(
            tasks.InstallClusterApiTask(),
            tasks.ApplyRabbitmqClusterTask("magnum"),
            tasks.GetChartValues(
                chart_name="magnum",
                chart_version="0.2.8",
            ),
            tasks.GenerateOpenStackHelmWithInfraReleaseValues(
                inject={"chart_name": "magnum"},
                rebind={"rabbitmq": "magnum_rabbitmq_cluster"},
                provides="magnum_release_values",
            ),
            tasks.GenerateOpenStackHelmWithInfraValuesFrom(
                inject={"chart_name": "magnum"},
                rebind={
                    "chart_values": "magnum_chart_values",
                    "rabbitmq": "magnum_rabbitmq_cluster",
                },
                provides="magnum_values_from",
            ),
            tasks.ApplyHelmReleaseTask(
                config={
                    "chart_name": "magnum",
                    "chart_version": "0.2.8",
                    "release_name": "magnum",
                },
                rebind={
                    "values": "magnum_release_values",
                    "values_from": "magnum_values_from",
                },
            ),
            tasks.ApplyIngressTask(
                inject={"endpoint": "container_infra"},
                rebind={
                    "chart_values": "magnum_chart_values",
                    "helm_release": "magnum_helm_release",
                },
            ),
        )

    if spec["senlin"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("senlin"))

    if spec["designate"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("designate"))

    if spec["heat"]["enabled"]:
        flow.add(tasks.ApplyRabbitmqClusterTask("heat"))

    if spec["monitoring"]["enabled"]:
        flow.add(
            tasks.ApplyNamespaceTask(
                name=constants.NAMESPACE_MONITORING,
                provides="monitoring_namespace",
            ),
        )

        if spec["monitoring"]["nodeFeatureDiscovery"]["enabled"]:
            flow.add(
                tasks.ApplyHelmReleaseTask(
                    config=constants.HELM_RELEASE_NODE_FEATURE_DISCOVERY,
                    rebind={"namespace": "monitoring_namespace"},
                ),
            )

    engine = engines.load(
        flow,
        store={
            "name": name,
            "spec": spec,
        },
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )

    with logging_listener.DynamicLoggingListener(engine, level=logging.INFO):
        try:
            engine.run()
        except exceptions.WrappedFailure as ex:
            raise ex[0]

    # TODO(mmaser): Get rid of this and move it to the main taskflow engine
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()
