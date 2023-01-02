import logging

import kopf
from taskflow import engines
from taskflow.listeners import logging as logging_listener
from taskflow.patterns import graph_flow

from atmosphere import clients, flows
from atmosphere.models import config
from atmosphere.operator import tasks, utils
from atmosphere.operator.api import Cloud, objects, types

API = clients.get_pykube_api()


@kopf.on.resume(Cloud.version, Cloud.kind)
@kopf.on.create(Cloud.version, Cloud.kind)
def create_fn(namespace: str, name: str, spec: dict, **_):
    # TODO(mnaser): Get rid of this flow.
    cfg = config.Config.from_file()
    engine = flows.get_engine(cfg)
    engine.run()

    flow = graph_flow.Flow("deploy").add(
        tasks.GenerateImageTagsConfigMap(provides="image_tags"),
        tasks.GenerateSecrets(provides="secrets"),
    )

    if spec["magnum"].get("enabled", True):
        objects.OpenstackHelmRabbitmqCluster(
            api=API,
            metadata=types.NamespacedObjectMeta(
                name="magnum",
                namespace=namespace,
            ),
            spec=types.OpenstackHelmRabbitmqClusterSpec(
                image=utils.get_image_ref(
                    "rabbitmq_server", override_registry=spec["imageRepository"]
                ).string()
            ),
        ).apply()
        flow.add(
            tasks.InstallClusterApiTask(),
            tasks.GetChartValues(
                inject={
                    "helm_repository": "openstack-helm",
                    "helm_repository_url": "https://tarballs.opendev.org/openstack/openstack-helm/",
                    "chart_name": "magnum",
                    "chart_version": "0.2.8",
                },
                provides="magnum_chart_values",
            ),
            tasks.GenerateReleaseValues(
                inject={"chart_name": "magnum"},
                provides="magnum_release_values",
            ),
            tasks.GenerateMagnumChartValuesFrom(
                inject={"chart_name": "magnum"},
                provides="magnum_values_from",
            ),
            tasks.ApplyHelmReleaseTask(
                inject={
                    "helm_repository": "openstack-helm",
                    "chart_name": "magnum",
                    "chart_version": "0.2.8",
                    "release_name": "magnum",
                },
                rebind={
                    "values": "magnum_release_values",
                    "values_from": "magnum_values_from",
                },
            ),
        )
        objects.OpenstackHelmIngress(
            api=API,
            metadata=types.OpenstackHelmIngressObjectMeta(
                name="container-infra",
                namespace=namespace,
            ),
            spec=types.OpenstackHelmIngressSpec(
                clusterIssuer=spec["certManagerClusterIssuer"],
                ingressClassName=spec["ingressClassName"],
                host=spec["magnum"]["endpoint"],
            ),
        ).apply()

    engine = engines.load(
        flow,
        store={
            "api": API,
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
