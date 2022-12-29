import textwrap

import mergedeep
import pytest

from atmosphere.models import config
from atmosphere.operator import tasks
from atmosphere.tasks import constants
from atmosphere.tasks.composite import openstack_helm


@pytest.mark.parametrize(
    "cfg_data,expected",
    [
        pytest.param(
            textwrap.dedent(
                """\
                """
            ),
            [
                {
                    "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                    "kind": "HelmRelease",
                    "metadata": {
                        "name": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                        "namespace": constants.NAMESPACE_MONITORING,
                    },
                    "spec": {
                        "chart": {
                            "spec": {
                                "chart": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                                "sourceRef": {
                                    "kind": "HelmRepository",
                                    "name": "atmosphere",
                                    "namespace": constants.NAMESPACE_OPENSTACK,
                                },
                                "version": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
                            }
                        },
                        "install": {"crds": "CreateReplace", "disableWait": True},
                        "interval": "60s",
                        "upgrade": {"crds": "CreateReplace", "disableWait": True},
                        "values": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
                        "valuesFrom": [],
                    },
                },
            ],
            id="default",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [kube_prometheus_stack.overrides]
                foo = "bar"
                """
            ),
            [
                {
                    "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                    "kind": "HelmRelease",
                    "metadata": {
                        "name": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                        "namespace": constants.NAMESPACE_MONITORING,
                    },
                    "spec": {
                        "chart": {
                            "spec": {
                                "chart": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                                "sourceRef": {
                                    "kind": "HelmRepository",
                                    "name": "atmosphere",
                                    "namespace": constants.NAMESPACE_OPENSTACK,
                                },
                                "version": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
                            }
                        },
                        "install": {"crds": "CreateReplace", "disableWait": True},
                        "interval": "60s",
                        "upgrade": {"crds": "CreateReplace", "disableWait": True},
                        "values": mergedeep.merge(
                            {},
                            constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
                            {"foo": "bar"},
                        ),
                        "valuesFrom": [],
                    },
                },
            ],
            id="overrides",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [opsgenie]
                enabled = true
                api_key = "foobar"
                heartbeat = "prod"
                """
            ),
            [
                {
                    "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                    "kind": "HelmRelease",
                    "metadata": {
                        "name": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                        "namespace": constants.NAMESPACE_MONITORING,
                    },
                    "spec": {
                        "chart": {
                            "spec": {
                                "chart": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                                "sourceRef": {
                                    "kind": "HelmRepository",
                                    "name": "atmosphere",
                                    "namespace": constants.NAMESPACE_OPENSTACK,
                                },
                                "version": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
                            }
                        },
                        "install": {"crds": "CreateReplace", "disableWait": True},
                        "interval": "60s",
                        "upgrade": {"crds": "CreateReplace", "disableWait": True},
                        "values": mergedeep.merge(
                            {},
                            constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
                            {
                                "alertmanager": {
                                    "config": openstack_helm.generate_alertmanager_config_for_opsgenie(
                                        config.OpsGenieConfig(
                                            {"api_key": "foobar", "heartbeat": "prod"}
                                        )
                                    )
                                }
                            },
                        ),
                        "valuesFrom": [],
                    },
                },
            ],
            id="opsgenie",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [kube_prometheus_stack]
                enabled = false
                """
            ),
            [],
            id="disabled",
        ),
    ],
)
def test_kube_prometheus_stack_tasks_from_config(pykube, cfg_data, expected):
    cfg = config.Config.from_string(cfg_data, validate=False)
    cfg.kube_prometheus_stack.validate()

    api_task = tasks.BuildApiClient()
    api = api_task.execute()
    namespace_task = tasks.ApplyNamespaceTask(constants.NAMESPACE_MONITORING)
    namespace = namespace_task.generate_object(api, constants.NAMESPACE_MONITORING)
    helm_repo_namespace_task = tasks.ApplyNamespaceTask(constants.NAMESPACE_OPENSTACK)
    helm_repo_namespace = helm_repo_namespace_task.generate_object(
        api, constants.NAMESPACE_OPENSTACK
    )
    helm_repository = tasks.ApplyHelmRepositoryTask(
        inject={
            "repository_name": "atmosphere",
            "url": "http://atmosphere.openstack/charts/",
            "namespace": helm_repo_namespace,
        },
    )
    assert [
        t.generate_object(
            api=api,
            namespace=namespace,
            release_name=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
            helm_repository=helm_repository.generate_object(
                api,
                repository_name="atmosphere",
                url="http://atmosphere.openstack/charts/",
                namespace=helm_repo_namespace,
            ),
            chart_name=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
            chart_version=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
            values=openstack_helm._kube_prometheus_stack_values_from_config(
                cfg.kube_prometheus_stack, opsgenie=cfg.opsgenie
            ),
            spec={},
            values_from=[],
        ).obj
        for t in openstack_helm.kube_prometheus_stack_tasks_from_config(
            cfg.kube_prometheus_stack, opsgenie=cfg.opsgenie
        )
    ] == expected


@pytest.mark.parametrize(
    "cfg_data,expected",
    [
        pytest.param(
            textwrap.dedent(
                """\
                """
            ),
            [
                {
                    "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                    "kind": "HelmRelease",
                    "metadata": {
                        "name": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "chart": {
                            "spec": {
                                "chart": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                                "sourceRef": {
                                    "kind": "HelmRepository",
                                    "name": "atmosphere",
                                    "namespace": constants.NAMESPACE_OPENSTACK,
                                },
                                "version": constants.HELM_RELEASE_INGRESS_NGINX_VERSION,
                            }
                        },
                        "install": {"crds": "CreateReplace", "disableWait": True},
                        "interval": "60s",
                        "upgrade": {"crds": "CreateReplace", "disableWait": True},
                        "values": constants.HELM_RELEASE_INGRESS_NGINX_VALUES,
                        "valuesFrom": [],
                    },
                },
            ],
            id="default",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [ingress_nginx.overrides]
                foo = "bar"
                """
            ),
            [
                {
                    "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                    "kind": "HelmRelease",
                    "metadata": {
                        "name": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "chart": {
                            "spec": {
                                "chart": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                                "sourceRef": {
                                    "kind": "HelmRepository",
                                    "name": "atmosphere",
                                    "namespace": constants.NAMESPACE_OPENSTACK,
                                },
                                "version": constants.HELM_RELEASE_INGRESS_NGINX_VERSION,
                            }
                        },
                        "install": {"crds": "CreateReplace", "disableWait": True},
                        "interval": "60s",
                        "upgrade": {"crds": "CreateReplace", "disableWait": True},
                        "values": {
                            **constants.HELM_RELEASE_INGRESS_NGINX_VALUES,
                            "foo": "bar",
                        },
                        "valuesFrom": [],
                    },
                },
            ],
            id="overrides",
        ),
        pytest.param(
            textwrap.dedent(
                """\
                [ingress_nginx]
                enabled = false
                """
            ),
            [],
            id="disabled",
        ),
    ],
)
def test_ingress_nginx_tasks_from_config(pykube, cfg_data, expected):
    cfg = config.Config.from_string(cfg_data, validate=False)
    cfg.ingress_nginx.validate()
    api_task = tasks.BuildApiClient()
    api = api_task.execute()
    namespace_task = tasks.ApplyNamespaceTask(constants.NAMESPACE_OPENSTACK)
    namespace = namespace_task.generate_object(api, constants.NAMESPACE_OPENSTACK)
    helm_repository = tasks.ApplyHelmRepositoryTask(
        inject={
            "repository_name": "atmosphere",
            "url": "http://atmosphere.openstack/charts/",
            "namespace": namespace,
        },
    )
    assert [
        t.generate_object(
            api=api,
            namespace=namespace,
            release_name=constants.HELM_RELEASE_INGRESS_NGINX_NAME,
            helm_repository=helm_repository.generate_object(
                api,
                repository_name="atmosphere",
                url="http://atmosphere.openstack/charts/",
                namespace=namespace,
            ),
            chart_name=constants.HELM_RELEASE_INGRESS_NGINX_NAME,
            chart_version=constants.HELM_RELEASE_INGRESS_NGINX_VERSION,
            values=mergedeep.merge(
                constants.HELM_RELEASE_INGRESS_NGINX_VALUES,
                cfg.ingress_nginx.overrides,
            ),
            spec={},
            values_from=[],
        ).obj
        for t in openstack_helm.ingress_nginx_tasks_from_config(cfg.ingress_nginx)
    ] == expected
