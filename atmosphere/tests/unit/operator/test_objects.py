import json

import pytest
import responses
from hypothesis import given
from hypothesis import provisional as prov
from hypothesis import strategies as st

from atmosphere.operator.api import objects, types


class TestNamespace:
    @given(st.builds(objects.Namespace))
    def test_property(self, instance):
        assert isinstance(instance, objects.Namespace)
        assert isinstance(instance.metadata, types.ObjectMeta)

    def test_apply(self, api, requests_mock):
        instance = objects.Namespace(
            api=api,
            metadata=types.ObjectMeta(
                name="openstack",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                "https://localhost:9443/api/v1/namespaces/openstack?fieldManager=atmosphere-operator&force=True",
                json={},
            )

            instance.apply()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": "openstack",
                    "annotations": {
                        "annotate": "this",
                    },
                    "labels": {
                        "foo": "bar",
                    },
                },
            }


class TestHelmRepository:
    @given(
        st.builds(
            objects.HelmRepository,
            spec=st.builds(types.HelmRepositorySpec, url=prov.urls()),
        )
    )
    def test_property(self, instance):
        assert isinstance(instance, objects.HelmRepository)
        assert isinstance(instance.spec, types.HelmRepositorySpec)

    def test_apply(self, api, requests_mock):
        instance = objects.HelmRepository(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name="openstack-helm",
                namespace="openstack",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.HelmRepositorySpec(
                url="https://tarballs.opendev.org/openstack/openstack-helm/",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                "https://localhost:9443/apis/source.toolkit.fluxcd.io/v1beta2/namespaces/openstack/helmrepositories/openstack-helm?fieldManager=atmosphere-operator&force=True",  # noqa E501
                json={},
            )

            instance.apply()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                "kind": "HelmRepository",
                "metadata": {
                    "name": "openstack-helm",
                    "namespace": "openstack",
                    "annotations": {
                        "annotate": "this",
                    },
                    "labels": {
                        "foo": "bar",
                    },
                },
                "spec": {
                    "interval": "60s",
                    "url": "https://tarballs.opendev.org/openstack/openstack-helm/",
                },
            }


class TestHelmRelease:
    @given(st.builds(objects.HelmRelease))
    def test_property(self, instance):
        assert isinstance(instance, objects.HelmRelease)
        assert isinstance(instance.spec, types.HelmReleaseSpec)

    def test_apply(self, api, requests_mock):
        instance = objects.HelmRelease(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name="neutron",
                namespace="openstack",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.HelmReleaseSpec(
                chart=types.HelmChartTemplate(
                    spec=types.HelmChartTemplateSpec(
                        chart="neutron",
                        version="0.1.0",
                        source_ref=types.CrossNamespaceObjectReference(
                            kind="HelmRepository",
                            name="openstack-helm",
                            namespace="openstack",
                        ),
                    )
                ),
                values={
                    "foo": "bar",
                },
                values_from=[
                    types.HelmReleaseValuesReference(
                        kind="Secret",
                        name="rabbitmq-neutron-default-user",
                        values_key="username",
                        target_path="rabbitmq.username",
                    )
                ],
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                "https://localhost:9443/apis/helm.toolkit.fluxcd.io/v2beta1/namespaces/openstack/helmreleases/neutron?fieldManager=atmosphere-operator&force=True",  # noqa E501
                json={},
            )

            instance.apply()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "helm.toolkit.fluxcd.io/v2beta1",
                "kind": "HelmRelease",
                "metadata": {
                    "name": instance.metadata.name,
                    "namespace": instance.metadata.namespace,
                    "labels": instance.metadata.labels,
                    "annotations": instance.metadata.annotations,
                },
                "spec": {
                    "chart": {
                        "spec": {
                            "chart": "neutron",
                            "version": "0.1.0",
                            "sourceRef": {
                                "kind": "HelmRepository",
                                "name": "openstack-helm",
                                "namespace": "openstack",
                            },
                        },
                    },
                    "dependsOn": [],
                    "install": {
                        "crds": "CreateReplace",
                        "disableWait": True,
                        "remediation": {
                            "retries": 3,
                        },
                    },
                    "interval": "60s",
                    "upgrade": {
                        "crds": "CreateReplace",
                        "disableWait": True,
                        "remediation": {
                            "retries": 3,
                        },
                    },
                    "values": {
                        "foo": "bar",
                    },
                    "valuesFrom": [
                        {
                            "kind": "Secret",
                            "name": "rabbitmq-neutron-default-user",
                            "valuesKey": "username",
                            "targetPath": "rabbitmq.username",
                        },
                    ],
                },
            }


class TestOpenstackHelmIngress:
    @given(st.builds(objects.OpenstackHelmIngress))
    def test_property(self, instance):
        assert isinstance(instance, objects.OpenstackHelmIngress)
        assert isinstance(instance.metadata, types.OpenstackHelmIngressObjectMeta)
        assert isinstance(instance.spec, types.OpenstackHelmIngressSpec)

    def test_endpont_to_service_mapping_order(self):
        assert [*objects.OpenstackHelmIngress.ENDPOINT_TO_SERVICE_MAPPING] == sorted(
            [*objects.OpenstackHelmIngress.ENDPOINT_TO_SERVICE_MAPPING]
        )

    @pytest.mark.parametrize("name", types.OpenstackHelmIngressObjectMetaName)
    def test_service(self, name):
        instance = objects.OpenstackHelmIngress(
            metadata=types.OpenstackHelmIngressObjectMeta(
                name=name,
                namespace="default",
            ),
            spec=types.OpenstackHelmIngressSpec(
                host=f"{name}.example.com",
            ),
        )

        assert instance.service is not None

    @pytest.mark.parametrize("name", types.OpenstackHelmIngressObjectMetaName)
    def test_apply(self, api, requests_mock, name):
        instance = objects.OpenstackHelmIngress(
            api=api,
            metadata=types.OpenstackHelmIngressObjectMeta(
                name=name,
                namespace="default",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.OpenstackHelmIngressSpec(
                host=f"{name}.example.com",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                f"https://localhost:9443/apis/atmosphere.vexxhost.com/v1alpha1/namespaces/default/openstackhelmingresses/{name}?fieldManager=atmosphere-operator&force=True",  # noqa
                json={},
            )

            instance.apply()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "atmosphere.vexxhost.com/v1alpha1",
                "kind": "OpenstackHelmIngress",
                "metadata": {
                    "name": name,
                    "namespace": "default",
                    "annotations": {
                        "annotate": "this",
                    },
                    "labels": {
                        "foo": "bar",
                    },
                },
                "spec": {
                    "host": f"{name}.example.com",
                    "clusterIssuer": "atmosphere",
                    "ingressClassName": "atmosphere",
                },
            }

    @pytest.mark.parametrize("name", types.OpenstackHelmIngressObjectMetaName)
    def test_apply_ingress(self, api, requests_mock, name):
        instance = objects.OpenstackHelmIngress(
            api=api,
            metadata=types.OpenstackHelmIngressObjectMeta(
                name=name,
                namespace="default",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.OpenstackHelmIngressSpec(
                host=f"{name}.example.com",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                f"https://localhost:9443/apis/networking.k8s.io/v1/namespaces/default/ingresses/{name}?fieldManager=atmosphere-operator&force=True",  # noqa
                json={},
            )

            instance.apply_ingress()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {
                    "name": name,
                    "namespace": "default",
                    "labels": {
                        "foo": "bar",
                    },
                    "annotations": {
                        "annotate": "this",
                        "cert-manager.io/cluster-issuer": "atmosphere",
                    },
                },
                "spec": {
                    "ingressClassName": "atmosphere",
                    "rules": [
                        {
                            "host": f"{name}.example.com",
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": instance.service.name,
                                                "port": {
                                                    "number": instance.service.port.number,
                                                },
                                            },
                                        },
                                    },
                                ],
                            },
                        },
                    ],
                    "tls": [
                        {
                            "secretName": f"{instance.service.name}-certs",
                            "hosts": [f"{name}.example.com"],
                        }
                    ],
                },
            }

    @pytest.mark.parametrize("name", types.OpenstackHelmIngressObjectMetaName)
    def test_delete_ingress(self, api, requests_mock, name):
        instance = objects.OpenstackHelmIngress(
            api=api,
            metadata=types.OpenstackHelmIngressObjectMeta(
                name=name,
                namespace="default",
            ),
            spec=types.OpenstackHelmIngressSpec(
                host=f"{name}.example.com",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.GET,
                f"https://localhost:9443/apis/networking.k8s.io/v1/namespaces/default/ingresses/{name}",  # noqa
                json={
                    "metadata": {
                        "name": instance.metadata.name,
                    },
                },
            )
            rsps.add(
                responses.DELETE,
                f"https://localhost:9443/apis/networking.k8s.io/v1/namespaces/default/ingresses/{name}",  # noqa
            )

            instance.delete_ingress()
            assert len(rsps.calls) == 2

    @pytest.mark.parametrize("name", types.OpenstackHelmIngressObjectMetaName)
    def test_delete_missing_ingress(self, api, requests_mock, name):
        instance = objects.OpenstackHelmIngress(
            api=api,
            metadata=types.OpenstackHelmIngressObjectMeta(
                name=name,
                namespace="default",
            ),
            spec=types.OpenstackHelmIngressSpec(
                host=f"{name}.example.com",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.GET,
                f"https://localhost:9443/apis/networking.k8s.io/v1/namespaces/default/ingresses/{name}",  # noqa
                status=404,
            )

            instance.delete_ingress()
            assert len(rsps.calls) == 1
