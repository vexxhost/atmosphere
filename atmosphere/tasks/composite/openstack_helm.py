import mergedeep
import pykube
import yaml
from oslo_serialization import base64

from atmosphere.models import config
from atmosphere.models.openstack_helm import values
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import base, flux, v1


class ApplyReleaseSecretTask(v1.ApplySecretTask):
    def __init__(self, config: config.Config, namespace: str, chart: str):
        vals = mergedeep.merge(
            {},
            values.Values.for_chart(chart, config).to_native(),
            getattr(config, chart).overrides,
        )
        values_yaml = yaml.dump(vals, default_flow_style=False)

        super().__init__(
            namespace=namespace,
            name=f"atmosphere-{chart}",
            data={"values.yaml": base64.encode_as_text(values_yaml)},
        )


class ApplyHelmReleaseTask(flux.ApplyHelmReleaseTask):
    def __init__(
        self,
        namespace: str,
        name: str,
        repository: str,
        version: str,
    ):
        super().__init__(
            namespace=namespace,
            name=name,
            repository=repository,
            chart=name,
            version=version,
            values_from=[
                {
                    "kind": "Secret",
                    "name": f"atmosphere-{name}",
                }
            ],
            requires=set([f"secret-{namespace}-atmosphere-{name}"]),
        )


class PerconaXtraDBCluster(pykube.objects.NamespacedAPIObject):
    version = "pxc.percona.com/v1-10-0"
    endpoint = "perconaxtradbclusters"
    kind = "PerconaXtraDBCluster"


class ApplyPerconaXtraDBClusterTask(base.ApplyKubernetesObjectTask):
    def __init__(self):
        super().__init__(
            kind=PerconaXtraDBCluster,
            namespace=constants.NAMESPACE_OPENSTACK,
            name="percona-xtradb",
            requires=[
                f"helm-release-{constants.NAMESPACE_OPENSTACK}-{constants.HELM_RELEASE_PXC_OPERATOR_NAME}",
            ],
        )

    def generate_object(self) -> PerconaXtraDBCluster:
        return PerconaXtraDBCluster(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": self._obj_name,
                    "namespace": self._obj_namespace,
                },
                "spec": {
                    "crVersion": "1.10.0",
                    "secretsName": "percona-xtradb",
                    "pxc": {
                        "size": 3,
                        "image": "percona/percona-xtradb-cluster:5.7.39-31.61",
                        "autoRecovery": True,
                        "configuration": "[mysqld]\nmax_connections=8192\n",
                        "sidecars": [
                            {
                                "name": "exporter",
                                "image": "quay.io/prometheus/mysqld-exporter:v0.14.0",
                                "ports": [{"name": "metrics", "containerPort": 9104}],
                                "livenessProbe": {
                                    "httpGet": {"path": "/", "port": 9104}
                                },
                                "env": [
                                    {
                                        "name": "MONITOR_PASSWORD",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "name": "percona-xtradb",
                                                "key": "monitor",
                                            }
                                        },
                                    },
                                    {
                                        "name": "DATA_SOURCE_NAME",
                                        "value": "monitor:$(MONITOR_PASSWORD)@(localhost:3306)/",
                                    },
                                ],
                            }
                        ],
                        "nodeSelector": constants.NODE_SELECTOR_CONTROL_PLANE,
                        "volumeSpec": {
                            "persistentVolumeClaim": {
                                "resources": {"requests": {"storage": "160Gi"}}
                            }
                        },
                    },
                    "haproxy": {
                        "enabled": True,
                        "size": 3,
                        "image": "percona/percona-xtradb-cluster-operator:1.10.0-haproxy",
                        "nodeSelector": {"openstack-control-plane": "enabled"},
                    },
                },
            },
        )


class RabbitmqCluster(pykube.objects.NamespacedAPIObject):
    version = "rabbitmq.com/v1beta1"
    endpoint = "rabbitmqclusters"
    kind = "RabbitmqCluster"


class ApplyRabbitmqClusterTask(base.ApplyKubernetesObjectTask):
    def __init__(self, name: str):
        super().__init__(
            kind=RabbitmqCluster,
            namespace=constants.NAMESPACE_OPENSTACK,
            name=name,
            requires=[
                f"helm-release-{constants.NAMESPACE_OPENSTACK}-{constants.HELM_RELEASE_RABBITMQ_OPERATOR_NAME}",
            ],
        )

    def generate_object(self) -> RabbitmqCluster:
        return RabbitmqCluster(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": f"rabbitmq-{self._obj_name}",
                    "namespace": self._obj_namespace,
                },
                "spec": {
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
