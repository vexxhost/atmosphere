import mergedeep
import pykube
import yaml
from oslo_serialization import base64

from atmosphere.models import config
from atmosphere.models.openstack_helm import values
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import base, flux, v1


class ApplyReleaseSecretTask(v1.ApplySecretTask):
    def __init__(self, namespace: str, chart: str, *args, **kwargs):
        cfg = config.Config.load_from_file()
        vals = values.Values.for_chart(chart, cfg)

        data = values.to_native()
        overrides = getattr(cfg, chart).overrides

        vals = mergedeep.merge({}, data, overrides)
        values_yaml = yaml.dump(vals, default_flow_style=False)

        super().__init__(
            namespace,
            f"atmosphere-{chart}",
            {"values.yaml": base64.encode_as_text(values_yaml)},
            *args,
            **kwargs,
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
    def __init__(self, namespace: str):
        super().__init__(
            kind=PerconaXtraDBCluster,
            namespace=namespace,
            name="percona-xtradb",
            requires=[
                f"helm-release-{namespace}-{constants.HELM_RELEASE_PXC_OPERATOR_NAME}",
                "name",
            ],
            inject={"name": "percona-xtradb"},
        )

    def generate_object(self, namespace, name, **kwargs) -> PerconaXtraDBCluster:
        return PerconaXtraDBCluster(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": name,
                    "namespace": namespace.name,
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
                "name",
            ],
            inject={"name": name},
        )

    def generate_object(self, namespace, name, **kwargs) -> RabbitmqCluster:
        return RabbitmqCluster(
            self.api,
            {
                "apiVersion": self._obj_kind.version,
                "kind": self._obj_kind.kind,
                "metadata": {
                    "name": f"rabbitmq-{name}",
                    "namespace": namespace.name,
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
