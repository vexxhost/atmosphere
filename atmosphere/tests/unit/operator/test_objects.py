import json

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


class TestOpenstackHelmRabbitmqCluster:
    @given(st.builds(objects.OpenstackHelmRabbitmqCluster))
    def test_property(self, instance):
        assert isinstance(instance, objects.OpenstackHelmRabbitmqCluster)
        assert isinstance(instance.metadata, types.NamespacedObjectMeta)
        assert isinstance(instance.spec, types.OpenstackHelmRabbitmqClusterSpec)

    def test_apply(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name="neutron",
                namespace="default",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.OpenstackHelmRabbitmqClusterSpec(
                image="rabbitmq:3.8.9",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                "https://localhost:9443/apis/atmosphere.vexxhost.com/v1alpha1/namespaces/default/openstackhelmrabbitmqclusters/neutron?fieldManager=atmosphere-operator&force=True",  # noqa E501
                json={},
            )

            instance.apply()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "atmosphere.vexxhost.com/v1alpha1",
                "kind": "OpenstackHelmRabbitmqCluster",
                "metadata": {
                    "name": "neutron",
                    "namespace": "default",
                    "labels": {
                        "foo": "bar",
                    },
                    "annotations": {
                        "annotate": "this",
                    },
                },
                "spec": {
                    "image": "rabbitmq:3.8.9",
                },
            }

    def test_apply_rabbitmq_cluster(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name="neutron",
                namespace="default",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.OpenstackHelmRabbitmqClusterSpec(
                image="rabbitmq:3.8.9",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.PATCH,
                "https://localhost:9443/apis/rabbitmq.com/v1beta1/namespaces/default/rabbitmqclusters/rabbitmq-neutron?fieldManager=atmosphere-operator&force=True",  # noqa E501
                json={},
            )

            instance.apply_rabbitmq_cluster()

            assert len(rsps.calls) == 1
            assert json.loads(rsps.calls[0].request.body) == {
                "apiVersion": "rabbitmq.com/v1beta1",
                "kind": "RabbitmqCluster",
                "metadata": {
                    "name": "rabbitmq-neutron",
                    "namespace": "default",
                    "annotations": {
                        "annotate": "this",
                    },
                    "labels": {
                        "foo": "bar",
                    },
                },
                "spec": {
                    "image": "rabbitmq:3.8.9",
                    "affinity": {
                        "nodeAffinity": {
                            "requiredDuringSchedulingIgnoredDuringExecution": {
                                "nodeSelectorTerms": [
                                    {
                                        "matchExpressions": [
                                            {
                                                "key": "openstack-control-plane",
                                                "operator": "In",
                                                "values": ["enabled"],
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    "rabbitmq": {
                        "additionalConfig": "vm_memory_high_watermark.relative = 0.9\n"
                    },
                    "resources": {
                        "requests": {"cpu": "500m", "memory": "1Gi"},
                        "limits": {"cpu": "1", "memory": "2Gi"},
                    },
                    "terminationGracePeriodSeconds": 15,
                },
            }

    def test_delete_rabbitmq_cluster(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name="neutron",
                namespace="default",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.OpenstackHelmRabbitmqClusterSpec(
                image="rabbitmq:3.8.9",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.GET,
                "https://localhost:9443/apis/rabbitmq.com/v1beta1/namespaces/default/rabbitmqclusters/rabbitmq-neutron",
                json={
                    "metadata": {
                        "name": "rabbitmq-neutron",
                    },
                },
            )
            rsps.add(
                responses.DELETE,
                "https://localhost:9443/apis/rabbitmq.com/v1beta1/namespaces/default/rabbitmqclusters/rabbitmq-neutron",
            )

            instance.delete_rabbitmq_cluster()
            assert len(rsps.calls) == 2

    def test_delete_missing_rabbitmq_cluster(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.NamespacedObjectMeta(
                name="neutron",
                namespace="default",
                annotations={
                    "annotate": "this",
                },
                labels={
                    "foo": "bar",
                },
            ),
            spec=types.OpenstackHelmRabbitmqClusterSpec(
                image="rabbitmq:3.8.9",
            ),
        )

        with requests_mock as rsps:
            rsps.add(
                responses.GET,
                "https://localhost:9443/apis/rabbitmq.com/v1beta1/namespaces/default/rabbitmqclusters/rabbitmq-neutron",
                status=404,
            )

            instance.delete_rabbitmq_cluster()
            assert len(rsps.calls) == 1
