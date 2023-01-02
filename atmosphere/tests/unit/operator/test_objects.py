import pytest
import responses
from hypothesis import given
from hypothesis import strategies as st

from atmosphere.operator.api import objects, types


class TestOpenstackHelmRabbitmqCluster:
    @given(st.builds(objects.OpenstackHelmRabbitmqCluster))
    def test_property(self, instance):
        assert isinstance(instance, objects.OpenstackHelmRabbitmqCluster)
        assert isinstance(instance.metadata, types.ObjectMeta)
        assert isinstance(instance.spec, types.OpenstackHelmRabbitmqClusterSpec)

    def test_apply(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.ObjectMeta(
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
                f"https://localhost:9443/apis/{objects.OpenstackHelmIngress.version}/namespaces/{instance.metadata.namespace}/openstackhelmrabbitmqclusters/{instance.metadata.name}?fieldManager=atmosphere-operator&force=True",  # noqa
                json={
                    "apiVersion": objects.OpenstackHelmIngress.version,
                    "kind": objects.OpenstackHelmIngress.kind,
                    "metadata": {
                        "name": instance.metadata.name,
                        "namespace": instance.metadata.namespace,
                        "labels": instance.metadata.labels,
                        "annotations": instance.metadata.annotations,
                    },
                    "spec": instance.spec.dict(),
                },
            )

            resource = instance.apply()

            assert len(rsps.calls) == 1

            assert resource.obj["metadata"]["name"] == instance.metadata.name
            assert resource.obj["metadata"]["namespace"] == instance.metadata.namespace
            assert (
                resource.obj["metadata"]["annotations"] == instance.metadata.annotations
            )
            assert resource.obj["metadata"]["labels"] == instance.metadata.labels
            assert resource.obj["spec"] == instance.spec.dict()

    def test_apply_rabbitmq_cluster(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.ObjectMeta(
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
                f"https://localhost:9443/apis/{objects.RabbitmqCluster.version}/namespaces/{instance.metadata.namespace}/rabbitmqclusters/rabbitmq-{instance.metadata.name}?fieldManager=atmosphere-operator&force=True",  # noqa
                json={
                    "apiVersion": objects.RabbitmqCluster.version,
                    "kind": objects.RabbitmqCluster.kind,
                    "metadata": {
                        "name": f"rabbitmq-{instance.metadata.name}",
                        "namespace": instance.metadata.namespace,
                        "labels": instance.metadata.labels,
                        "annotations": instance.metadata.annotations,
                    },
                    "spec": {
                        "image": instance.spec.image,
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
                },
            )

            rabbitmq_cluster = instance.apply_rabbitmq_cluster()

            assert len(rsps.calls) == 1

            assert (
                rabbitmq_cluster.obj["metadata"]["name"]
                == f"rabbitmq-{instance.metadata.name}"
            )
            assert (
                rabbitmq_cluster.obj["metadata"]["namespace"]
                == instance.metadata.namespace
            )
            assert (
                rabbitmq_cluster.obj["metadata"]["annotations"]
                == instance.metadata.annotations
            )
            assert (
                rabbitmq_cluster.obj["metadata"]["labels"] == instance.metadata.labels
            )
            assert rabbitmq_cluster.obj["spec"]["image"] == instance.spec.image

    def test_delete_ingress(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.ObjectMeta(
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
                f"https://localhost:9443/apis/{objects.RabbitmqCluster.version}/namespaces/{instance.metadata.namespace}/rabbitmqclusters/rabbitmq-{instance.metadata.name}",  # noqa
                json={
                    "apiVersion": objects.RabbitmqCluster.version,
                    "kind": objects.RabbitmqCluster.kind,
                    "metadata": {
                        "name": f"rabbitmq-{instance.metadata.name}",
                        "namespace": instance.metadata.namespace,
                    },
                },
            )
            rsps.add(
                responses.DELETE,
                f"https://localhost:9443/apis/{objects.RabbitmqCluster.version}/namespaces/{instance.metadata.namespace}/rabbitmqclusters/rabbitmq-{instance.metadata.name}",  # noqa
            )

            instance.delete_rabbitmq_cluster()
            assert len(rsps.calls) == 2

    def test_delete_missing_rabbitmq_cluster(self, api, requests_mock):
        instance = objects.OpenstackHelmRabbitmqCluster(
            api=api,
            metadata=types.ObjectMeta(
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
                f"https://localhost:9443/apis/{objects.RabbitmqCluster.version}/namespaces/{instance.metadata.namespace}/rabbitmqclusters/rabbitmq-{instance.metadata.name}",  # noqa
                status=404,
            )

            instance.delete_rabbitmq_cluster()
            assert len(rsps.calls) == 1


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
                f"https://localhost:9443/apis/{objects.OpenstackHelmIngress.version}/namespaces/{instance.metadata.namespace}/openstackhelmingresses/{instance.metadata.name}?fieldManager=atmosphere-operator&force=True",  # noqa
                json={
                    "apiVersion": objects.OpenstackHelmIngress.version,
                    "kind": objects.OpenstackHelmIngress.kind,
                    "metadata": {
                        "name": instance.metadata.name,
                        "namespace": instance.metadata.namespace,
                        "labels": instance.metadata.labels,
                        "annotations": instance.metadata.annotations,
                    },
                    "spec": instance.spec.dict(),
                },
            )

            resource = instance.apply()

            assert len(rsps.calls) == 1

            assert resource.obj["metadata"]["name"] == instance.metadata.name
            assert resource.obj["metadata"]["namespace"] == instance.metadata.namespace
            assert (
                resource.obj["metadata"]["annotations"] == instance.metadata.annotations
            )
            assert resource.obj["metadata"]["labels"] == instance.metadata.labels
            assert resource.obj["spec"] == instance.spec.dict()

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
                f"https://localhost:9443/apis/{objects.Ingress.version}/namespaces/{instance.metadata.namespace}/ingresses/{instance.metadata.name}?fieldManager=atmosphere-operator&force=True",  # noqa
                json={
                    "apiVersion": objects.Ingress.version,
                    "kind": objects.Ingress.kind,
                    "metadata": {
                        "name": instance.metadata.name,
                        "namespace": instance.metadata.namespace,
                        "labels": instance.metadata.labels,
                        "annotations": {
                            **instance.metadata.annotations,
                            "cert-manager.io/cluster-issuer": instance.spec.clusterIssuer,
                        },
                    },
                    "spec": {
                        "ingressClassName": instance.spec.ingressClassName,
                        "rules": [
                            {
                                "host": instance.spec.host,
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
                                "hosts": [instance.spec.host],
                            }
                        ],
                    },
                },
            )

            ingress = instance.apply_ingress()

            assert len(rsps.calls) == 1

            assert ingress.metadata["name"] == instance.metadata.name
            assert ingress.metadata["namespace"] == instance.metadata.namespace
            assert ingress.metadata["annotations"] == {
                **instance.metadata.annotations,
                "cert-manager.io/cluster-issuer": instance.spec.clusterIssuer,
            }
            assert ingress.metadata["labels"] == instance.metadata.labels
            assert (
                ingress.obj["spec"]["ingressClassName"]
                == instance.spec.ingressClassName
            )
            assert ingress.obj["spec"]["rules"][0]["host"] == instance.spec.host
            assert (
                ingress.obj["spec"]["rules"][0]["http"]["paths"][0]["backend"][
                    "service"
                ]
                == instance.service.dict()
            )
            assert (
                ingress.obj["spec"]["tls"][0]["secretName"]
                == f"{instance.service.name}-certs"
            )
            assert ingress.obj["spec"]["tls"][0]["hosts"] == [instance.spec.host]

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
                f"https://localhost:9443/apis/{objects.Ingress.version}/namespaces/{instance.metadata.namespace}/ingresses/{instance.metadata.name}",  # noqa
                json={
                    "apiVersion": objects.Ingress.version,
                    "kind": objects.Ingress.kind,
                    "metadata": {
                        "name": instance.metadata.name,
                        "namespace": instance.metadata.namespace,
                    },
                },
            )
            rsps.add(
                responses.DELETE,
                f"https://localhost:9443/apis/{objects.Ingress.version}/namespaces/{instance.metadata.namespace}/ingresses/{instance.metadata.name}",  # noqa
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
                f"https://localhost:9443/apis/{objects.Ingress.version}/namespaces/{instance.metadata.namespace}/ingresses/{instance.metadata.name}",  # noqa
                status=404,
            )

            instance.delete_ingress()
            assert len(rsps.calls) == 1
