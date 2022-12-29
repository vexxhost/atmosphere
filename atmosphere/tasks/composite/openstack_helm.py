import textwrap

import mergedeep
import yaml

from atmosphere.models import config
from atmosphere.models.openstack_helm import values
from atmosphere.operator import tasks
from atmosphere.tasks import constants


class ApplyReleaseSecretTask(tasks.ApplySecretTask):
    def __init__(self, config: config.Config, chart: str, rebind: dict = {}):
        vals = mergedeep.merge(
            {},
            values.Values.for_chart(chart, config).to_native(),
            getattr(config, chart).overrides,
        )
        values_yaml = yaml.dump(vals, default_flow_style=False)

        super().__init__(
            f"atmosphere-{chart}",
            inject={
                "data": {"values.yaml": values_yaml},
            },
            rebind=rebind,
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


def _kube_prometheus_stack_values_from_config(
    config: config.KubePrometheusStackChartConfig, opsgenie: config.OpsGenieConfig
):
    values = mergedeep.merge(
        {},
        constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
        config.overrides,
    )

    if opsgenie.enabled:
        values["alertmanager"]["config"] = generate_alertmanager_config_for_opsgenie(
            opsgenie
        )
    return values


def kube_prometheus_stack_tasks_from_config(
    config: config.KubePrometheusStackChartConfig, opsgenie: config.OpsGenieConfig
):
    if not config.enabled:
        return []

    values = _kube_prometheus_stack_values_from_config(config, opsgenie)

    return [
        tasks.ApplyHelmReleaseTask(
            config={
                "chart_name": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                "chart_version": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
                "release_name": constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
                "values": values,
                "spec": {},
                "values_from": [],
            },
            rebind={
                "namespace": "monitoring_namespace",
            },
        ),
    ]


def ingress_nginx_tasks_from_config(config: config.IngressNginxChartConfig):
    if not config.enabled:
        return []

    values = mergedeep.merge(
        {},
        constants.HELM_RELEASE_INGRESS_NGINX_VALUES,
        config.overrides,
    )

    return [
        tasks.ApplyHelmReleaseTask(
            config={
                "chart_name": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                "chart_version": constants.HELM_RELEASE_INGRESS_NGINX_VERSION,
                "release_name": constants.HELM_RELEASE_INGRESS_NGINX_NAME,
                "values": values,
                "spec": {},
                "values_from": [],
            },
        ),
    ]
