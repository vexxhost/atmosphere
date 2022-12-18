import textwrap

import mergedeep
import pytest

from atmosphere.models import config
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
                                    "namespace": "openstack",
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
                                    "namespace": "openstack",
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
                                    "namespace": "openstack",
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

    assert [
        t.generate_object().obj
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
                                    "namespace": "openstack",
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
                                    "namespace": "openstack",
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

    assert [
        t.generate_object().obj
        for t in openstack_helm.ingress_nginx_tasks_from_config(cfg.ingress_nginx)
    ] == expected
