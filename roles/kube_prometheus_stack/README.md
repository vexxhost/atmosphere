# `kube_prometheus_stack`

There is a Grafana deployemnt with a few dashboards that are created by default
and a Prometheus deployment that is used to collect metrics from the cluster
which sends alerts to AlertManager. In addition, Loki is deployed to collect
logs from the cluster using Vector.

## Philosophy

Atmosphere's monitoring philosophy is strongly aligned with the principles
outlined in the Google Site Reliability Engineering (SRE) book. Our approach
focuses on alerting on conditions that are symptomatic of issues which directly
impact the service or system health, rather than simply monitoring the state of
individual components.

### Severity Levels

Our alerting system classifies incidents into different severity levels based on
their impact on the system and users.

- **SEV-1** (high): This is the highest level of severity, used for incidents 
  causing a complete service disruption or significant loss of functionality 
  across the entire Atmosphere platform. Immediate response and action are 
  necessary to restore the service.

- **SEV-2** (medium): This level is for incidents that affect a smaller group 
  of users or a single system. While these incidents require attention, they do 
  not generally necessitate immediate action outside of standard business hours.

- **SEV-3** (low): This level is used for minor issues that have a minimal 
  impact on users or the system's operation. These incidents are typically 
  addressed during standard business hours.

### Alerting Philosophy

Our alerting philosophy is to ensure that the right people are alerted at the
right time. Most alerts, if they are affecting a single system, would trigger a
lower severity level (SEV-3 or SEV-4). However, if an issue is affecting the
entire control plane of a specific service, it might escalate to a SEV-2. And
if the whole service is unavailable, it becomes a SEV-1.

We believe in minimizing alert noise to ensure that alerts are meaningful and
actionable. Our goal is to have every alert provide enough information to
initiate an immediate and effective response.

We continue to refine our monitoring and alerting strategies to ensure that we
are effectively identifying and responding to incidents, with the ultimate goal
of providing a reliable and high-quality service to all our users.

## Viewing data

By default, an `Ingress` is created for Grafana using the `kube_prometheus_stack_grafana_host`
variable. The default login is `admin` and the password is the value of
`kube_prometheus_stack_grafana_admin_password`.

You can view the existing dashboards by going to _Manage_ > _Dashboards_. You
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
   _Settings_ > _Heartbeats_ > _Create Heartbeat_. Set the interval to 1 minute.

Afterwards, you can configure the following options for the Atmosphere config:

```yaml
kube_prometheus_stack_helm_values:
  alertmanager:
    config:
      receivers:
        - name: "null"
        - name: notifier
          opsgenie_configs:
            - api_key: API_KEY
              message: >-
                {% raw -%}
                {{ .GroupLabels.alertname }}
                {%- endraw %}
              priority: >-
                {% raw -%}
                {{ if hasPrefix .GroupLabels.severity "SEV-" -}}
                {{ replace .GroupLabels.severity "SEV-" "P" -1 }}
                {{ else if eq .GroupLabels.severity "critical" -}}
                P1
                {{- else if eq .GroupLabels.severity "warning" -}}
                P2
                {{- else if eq .GroupLabels.severity "info" -}}
                P3
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
unresponsive. Also, it can be the cause of a very high amount of software
interrupts on the node.

In order to find the root cause of this issue, you can use the following
commands:

```console
iftop -ni $DEV -f 'multicast and not broadcast'
```

With the command above, you're able to see which IP addresses are sending the
multicast traffic. Once you have the IP address, you can use the following
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
