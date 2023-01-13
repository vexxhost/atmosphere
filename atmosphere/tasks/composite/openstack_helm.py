import textwrap

import mergedeep
import yaml

from atmosphere.models import config
from atmosphere.models.openstack_helm import values
from atmosphere.tasks.kubernetes import flux, v1


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
