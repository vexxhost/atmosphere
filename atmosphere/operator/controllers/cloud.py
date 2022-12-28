import logging

import kopf
from taskflow import engines
from taskflow.listeners import logging as logging_listener
from taskflow.patterns import graph_flow

from atmosphere.operator import tasks
from atmosphere.operator.api import Cloud


@kopf.on.resume(Cloud.version, Cloud.kind)
@kopf.on.create(Cloud.version, Cloud.kind)
def create_fn(namespace: str, name: str, spec: dict, **_):
    flow = graph_flow.Flow("deploy").add(
        tasks.BuildApiClient(),
        tasks.GenerateImageTagsConfigMap(provides="image_tags"),
        tasks.GenerateSecrets(provides="secrets"),
    )

    if spec["magnum"].get("enabled", True):
        flow.add(
            tasks.InstallClusterApiTask(),
            tasks.ApplyRabbitmqClusterTask(
                inject={"chart_name": "magnum"}, provides="magnum_rabbitmq"
            ),
            tasks.GetChartValues(
                inject={
                    "helm_repository": "atmosphere",
                    "helm_repository_url": "http://atmosphere.openstack/charts/",
                    "chart_name": "magnum",
                    "chart_version": "0.2.8",
                },
                provides="magnum_chart_values",
            ),
            tasks.GenerateReleaseValues(
                inject={"chart_name": "magnum"},
                rebind={"rabbitmq": "magnum_rabbitmq"},
                provides="magnum_release_values",
            ),
            tasks.GenerateMagnumChartValuesFrom(
                rebind={"rabbitmq": "magnum_rabbitmq"},
                provides="magnum_values_from",
            ),
            tasks.ApplyHelmReleaseTask(
                inject={
                    "helm_repository": "atmosphere",
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
                    "release_values": "magnum_release_values",
                },
            ),
        )

    engine = engines.load(
        flow,
        store={
            "namespace": namespace,
            "name": name,
            "spec": spec,
        },
        executor="greenthreaded",
        engine="parallel",
        max_workers=4,
    )

    with logging_listener.DynamicLoggingListener(engine, level=logging.INFO):
        engine.run()
