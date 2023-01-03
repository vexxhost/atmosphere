import textwrap

import mergedeep
import pykube
import yaml

from atmosphere import utils
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
            data={"values.yaml": values_yaml},
            provides=f"atmosphere-{chart}",
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
            repository_namespace=constants.HELM_REPOSITORY_ATMOSPHERE,
            chart=name,
            version=version,
            values_from=[
                {
                    "kind": "Secret",
                    "name": f"atmosphere-{name}",
                }
            ],
            requires=set([f"atmosphere-{name}"]),
        )


def generate_alertmanager_config_for_opsgenie(
    opsgenie: config.OpsGenieConfig,
) -> dict:
    return {
        "route": {
            "group_by": ["alertname", "severity"],
            "receiver": "opsgenie",
            "routes": [
                {"receiver": "null", "matchers": ['alertname = "InfoInhibitor"']},
                {
                    "receiver": "heartbeat",
                    "matchers": ['alertname = "Watchdog"'],
                    "group_wait": "0s",
                    "group_interval": "30s",
                    "repeat_interval": "15s",
                },
            ],
        },
        "receivers": [
            {"name": "null"},
            {
                "name": "opsgenie",
                "opsgenie_configs": [
                    {
                        "api_key": opsgenie.api_key,
                        "message": "{{ .GroupLabels.alertname }}",
                        "priority": textwrap.dedent(
                            """\
                            {{- if eq .GroupLabels.severity "critical" -}}
                            P1
                            {{- else if eq .GroupLabels.severity "warning" -}}
                            P3
                            {{- else if eq .GroupLabels.severity "info" -}}
                            P5
                            {{- else -}}
                            P3
                            {{- end -}}
                            """
                        ),
                        "description": textwrap.dedent(
                            """\
                            {{ if gt (len .Alerts.Firing) 0 -}}
                            Alerts Firing:
                            {{ range .Alerts.Firing }}
                            - Message: {{ .Annotations.message }}
                                Labels:
                            {{ range .Labels.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                            {{ end }}   Annotations:
                            {{ range .Annotations.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                            {{ end }}   Source: {{ .GeneratorURL }}
                            {{ end }}
                            {{- end }}
                            {{ if gt (len .Alerts.Resolved) 0 -}}
                            Alerts Resolved:
                            {{ range .Alerts.Resolved }}
                            - Message: {{ .Annotations.message }}
                                Labels:
                            {{ range .Labels.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                            {{ end }}   Annotations:
                            {{ range .Annotations.SortedPairs }}   - {{ .Name }} = {{ .Value }}
                            {{ end }}   Source: {{ .GeneratorURL }}
                            {{ end }}
                            {{- end }}
                            """
                        ),
                    }
                ],
            },
            {
                "name": "heartbeat",
                "webhook_configs": [
                    {
                        "url": f"https://api.opsgenie.com/v2/heartbeats/{opsgenie.heartbeat}/ping",
                        "send_resolved": False,
                        "http_config": {"basic_auth": {"password": opsgenie.api_key}},
                    }
                ],
            },
        ],
    }


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
                        "image": utils.get_image_ref_using_legacy_image_repository(
                            "percona_xtradb_cluster"
                        ).string(),
                        "autoRecovery": True,
                        "configuration": "[mysqld]\nmax_connections=8192\n",
                        "sidecars": [
                            {
                                "name": "exporter",
                                "image": utils.get_image_ref_using_legacy_image_repository(
                                    "prometheus_mysqld_exporter"
                                ).string(),
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
                        "image": utils.get_image_ref_using_legacy_image_repository(
                            "percona_xtradb_cluster_haproxy"
                        ).string(),
                        "nodeSelector": {"openstack-control-plane": "enabled"},
                    },
                },
            },
        )
