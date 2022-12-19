import textwrap

import mergedeep

from atmosphere.models import config
from atmosphere.tasks import constants
from atmosphere.tasks.kubernetes import flux


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


def kube_prometheus_stack_tasks_from_config(
    config: config.KubePrometheusStackChartConfig, opsgenie: config.OpsGenieConfig
):
    if not config.enabled:
        return []

    values = mergedeep.merge(
        {},
        constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES,
        config.overrides,
    )

    if opsgenie.enabled:
        values["alertmanager"]["config"] = generate_alertmanager_config_for_opsgenie(
            opsgenie
        )

    return [
        flux.ApplyHelmReleaseTask(
            namespace=config.namespace,
            name=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
            chart=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME,
            version=constants.HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION,
            values=values,
        ),
    ]
