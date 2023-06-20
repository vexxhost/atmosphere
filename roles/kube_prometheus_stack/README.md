# `kube_prometheus_stack`

There is a Grafana deployemnt with a few dashboards that are created by default
and a Prometheus deployment that is used to collect metrics from the cluster
which sends alerts to AlertManager.  In addition, Loki is deployed to collect
logs from the cluster using Vector.

## Viewing data

By default, an `Ingress` is created for Grafana using the `kube_prometheus_stack_grafana_host`
variable.  The default login is `admin` and the password is the value of
`kube_prometheus_stack_grafana_admin_password`.

You can view the existing dashboards by going to _Manage_ > _Dashboards_.  You
can also check any alerts that are currently firing by going to _Alerting_ >
_Alerts_.

## Integrations

### OpsGenie

Atmosphere can be integrated with OpsGenie in order to send all alerts to it,
this is useful if you want to have a single place to manage all your alerts.

In order to get started, you will need to complete the following steps inside
OpsGenie:

1. Create an integration inside OpsGenie, you can do this by going to
   _Settings_ > _Integrations_ > _Add Integration_ and selecting _Prometheus_.
2. Copy the API key that is generated for you and setup correct assignment
   rules inside OpsGenie.
3. Create a new heartbeat inside OpsGenie, you can do this by going to
   _Settings_ > _Heartbeats_ > _Create Heartbeat_.  Set the interval to 1 minute.

Afterwards, you can configure the following options for the Atmosphere config:

```yaml
kube_prometheus_stack_helm_values:
  alertmanager:
    config:
      route:
        group_by:
          - alertname
          - severity
        receiver: opsgenie
        routes:
          - receiver: "null"
            matchers:
              - alertname = "InfoInhibitor"
          - receiver: heartbeat
            group_wait: 0s
            group_interval: 30s
            repeat_interval: 15s
            matchers:
              - alertname = "Watchdog"
      receivers:
        - name: "null"
        - name: opsgenie
          opsgenie_configs:
            - api_key: API_KEY
              message: >-
                {% raw -%}
                {{ .GroupLabels.alertname }}
                {%- endraw %}
              priority: >-
                {% raw -%}
                {{ if eq .GroupLabels.severity "critical" -}}
                P1
                {{- else if eq .GroupLabels.severity "warning" -}}
                P3
                {{- else if eq .GroupLabels.severity "info" -}}
                P5
                {{- else -}}
                P3
                {{- end -}}
                {%- endraw %}
              description: |-
                {% raw -%}
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
                {%- endraw %}
        - name: heartbeat
          webhook_configs:
            - url: https://api.opsgenie.com/v2/heartbeats/HEARTBEAT_NAME/ping
              send_resolved: false
              http_config:
                basic_auth:
                  password: API_KEY
```

Once this is done and deployed, you'll start to see alerts inside OpsGenie and
you can also verify that the heartbeat is listed as _ACTIVE_.

## Alerts

### Network

#### `NodeNetworkMulticast`

This alert is triggered when a node is receiving large volumes of multicast
traffic which can be a sign of a misconfigured network or a malicious actor.

This can result in high CPU usage on the node and can cause the node to become
unresponsive.  Also, it can be the cause of a very high amount of software
interrupts on the node.

In order to find the root cause of this issue, you can use the following
commands:

```console
iftop -ni $DEV -f 'multicast and not broadcast'
```

With the command above, you're able to see which IP addresses are sending the
multicast traffic.  Once you have the IP address, you can use the following
command to find the server behind it:

```console
openstack server list --all-projects --long -n --ip $IP
```

### etcd

#### `etcdDatabaseHighFragmentationRatio`

```console
kubectl -n kube-system exec svc/kube-prometheus-stack-kube-etcd -- \
  etcdctl defrag \
  --cluster \
  --cacert /etc/kubernetes/pki/etcd/ca.crt \
  --key /etc/kubernetes/pki/etcd/server.key \
  --cert /etc/kubernetes/pki/etcd/server.crt
```
