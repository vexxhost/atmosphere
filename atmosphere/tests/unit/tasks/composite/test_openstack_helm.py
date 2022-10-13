import textwrap

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
                    "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                    "kind": "HelmRepository",
                    "metadata": {
                        "name": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "interval": "1m",
                        "url": constants.HELM_REPOSITORY_INGRESS_NGINX_URL,
                    },
                },
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
                                    "name": constants.HELM_REPOSITORY_INGRESS_NGINX,
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
                    "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                    "kind": "HelmRepository",
                    "metadata": {
                        "name": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                        "namespace": constants.NAMESPACE_OPENSTACK,
                    },
                    "spec": {
                        "interval": "1m",
                        "url": constants.HELM_REPOSITORY_INGRESS_NGINX_URL,
                    },
                },
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
                                    "name": constants.HELM_REPOSITORY_INGRESS_NGINX,
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
