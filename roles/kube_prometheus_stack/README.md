# `kube_prometheus_stack`

## Exposing data

There are a few ways to expose both the monitoring services to view the health
and the metrics and logs of the cluster.

### Port forwarding

The easiest way to expose the monitoring services is to use port forwarding
using the built-in `kubectl` command.

#### Grafana

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80
```

Once you run the command above, you'll be able to open `http://localhost:3000`
on your local system and view the Grafana UI.  The default login is `admin` and
the password is `prom-operator`.

#### Prometheus

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090
```

Once you run the command above, you'll be able to open `http://localhost:9090`
on your local system and view the Prometheus UI.

#### AlertManager

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-alertmanager 9093
```

Once you run the command above, you'll be able to open `http://localhost:9093`
on your local system and view the AlertManager UI.

### Unprotected access

If you want to expose the monitoring services, you can use the following
overrides which will create an `Ingress` for all the services.

!!! danger

    This will expose the monitoring services without any authentication or
    authorization. This is not recommended for production environments or any
    environment where the monitoring services are exposed to the public internet.

```yaml
kube_prometheus_stack_helm_values:
  alertmanager:
    ingress:
      enabled: true
      ingressClassName: openstack
      annotations:
        cert-manager.io/cluster-issuer: atmosphere
      hosts:
        - alertmanager.example.com
      tls:
        - secretName: alertmanager-tls
          hosts:
            - alertmanager.example.com
    alertmanagerSpec:
      externalUrl: https://alertmanager.example.com
  prometheus:
    ingress:
      enabled: true
      ingressClassName: openstack
      annotations:
        cert-manager.io/cluster-issuer: atmosphere
      hosts:
        - prometheus.example.com
      tls:
        - secretName: prometheus-certs
          hosts:
            - prometheus.example.com
    prometheusSpec:
      externalUrl: https://prometheus.example.com
```

### Protected access

If you want to expose the monitoring services, you can use the following
overrides which will create an `Ingress` for all the services.

```yaml
kube_prometheus_stack_helm_values:
  alertmanager:
    ingress:
      enabled: true
      ingressClassName: openstack
      annotations:
        cert-manager.io/cluster-issuer: atmosphere
        nginx.ingress.kubernetes.io/auth-type: basic
        nginx.ingress.kubernetes.io/auth-secret: prometheus-auth
        nginx.ingress.kubernetes.io/auth-realm: Prometheus
      hosts:
        - alertmanager.example.com
      tls:
        - secretName: alertmanager-tls
          hosts:
            - alertmanager.example.com
    alertmanagerSpec:
      externalUrl: https://alertmanager.example.com
  prometheus:
    ingress:
      enabled: true
      ingressClassName: openstack
      annotations:
        cert-manager.io/cluster-issuer: atmosphere
        nginx.ingress.kubernetes.io/auth-type: basic
        nginx.ingress.kubernetes.io/auth-secret: prometheus-auth
        nginx.ingress.kubernetes.io/auth-realm: Prometheus
      hosts:
        - prometheus.example.com
      tls:
        - secretName: prometheus-certs
          hosts:
            - prometheus.example.com
    prometheusSpec:
      externalUrl: https://prometheus.example.com
```

Once you've deployed with the overrides above, you'll need to create a secret
with the username and password you want to use to access the monitoring
services.

```bash
htpasswd -c auth monitoring
```

The above will generate a file called `auth` with the username and password,
in this case the username is `monitoring`. You'll need to create a secret with
the contents of the file.

```bash
kubectl -n monitoring create secret generic prometheus-auth --from-file=auth
```

Once you're done, you'll be able to access the monitoring services using the
username and password you created.

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

### `etcdDatabaseHighFragmentationRatio`

```console
kubectl -n kube-system exec svc/kube-prometheus-stack-kube-etcd -- \
  etcdctl defrag \
  --cluster \
  --cacert /etc/kubernetes/pki/etcd/ca.crt \
  --key /etc/kubernetes/pki/etcd/server.key \
  --cert /etc/kubernetes/pki/etcd/server.crt
```
