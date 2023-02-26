# Quickstart

In this quickstart guide, we will walk you through installing Vector with Helm
for a variety of common platforms and tools.

_NOTE: The instructions here assume the use of Helm v3, and Bash._

## Getting started with Datadog

### Prerequisites

Verify you have `helm` and `kubectl` installed locally to proceed. `helm` should
be `v3.0+`.

```bash
helm version
```

Ensure you have both the Datadog and Vector charts, and they are up-to-date.

```bash
helm repo add datadog https://helm.datadoghq.com
helm repo add vector https://helm.vector.dev
helm repo update
```

Access to a pre-existing Kubernetes cluster, or start a new cluster locally
with `minikube`.

```bash
minikube start
minikube addons enable metrics-server
minikube status
```

Clone this repository locally to have access to the quickstart values files.

```bash
git clone https://github.com/vectordotdev/helm-charts.git && \
	cd helm-charts/charts/vector
```

### Installing

Export your Datadog API key into your local environment.

```bash
export DATADOG_API_KEY="<REPLACE_ME>"
```

Then install Vector into its own namespace, providing your API key as an
environment variable.

```bash
helm install vector vector/vector --namespace vector --create-namespace \
	--values examples/datadog-values.yaml  --set secrets.generic.datadog_api_key="${DATADOG_API_KEY}"
```

Run the next command to confirm Vector has been configured properly and can
connect to your Datadog account.

```bash
kubectl logs statefulset/vector --namespace vector --follow
```

Running the above will tail Vector's logs and allow to confirm your API key
is correct. In the logs you should only see INFO messages, and the following
logs (one for each configured sink):

```json lines
{"timestamp":"2022-03-30T20:25:48.016522Z","level":"INFO","message":"Healthcheck: Passed.","target":"vector::topology::builder"}
{"timestamp":"2022-03-30T20:25:48.024391Z","level":"INFO","message":"Healthcheck: Passed.","target":"vector::topology::builder"}
```

Once Vector has been installed and configured, you can install your Datadog Agents.
By default, the Agents will forward their logs and metrics directly to Datadog's
hosted intake, we'll create a values file to override that behavior to forward to
your new Vector Aggregators.

For Datadog Agents version `7.35`/`6.35` or greater:

```bash
cat <<-'VALUES' > dd-agent.yaml
---
datadog:
  logs:
    enabled: true
    containerCollectAll: true
agents:
  useConfigMap: true
  customAgentConfig:
    # NOTE: If you're using a quickstart environment like `minikube`,
    # uncomment the line below; otherwise, we recommend leaving it with the
    # default setting of `true`.
    # kubelet_tls_verify: false
    vector:
      logs:
        enabled: true
	# Use https if SSL is enabled in Vector source configuration
        url: http://vector-haproxy.vector:8282
      metrics:
        enabled: true
	# Use https if SSL is enabled in Vector source configuration
        url: http://vector-haproxy.vector:8282
VALUES
```

For Datadog Agents version `7.34`/`6.34` and older:

_NOTE: Metrics will not be routed through Vector for Datadog Agent versions older
than `7.35`/`6.35`._

```bash
cat <<-'VALUES' > dd-agent.yaml
---
datadog:
  logs:
    enabled: true
    containerCollectAll: true
agents:
  useConfigMap: true
  customAgentConfig:
    # NOTE: If you're using a quickstart environment like `minikube`,
    # uncomment the line below; otherwise, we recommend leaving it with the
    # default setting of `true`.
    # kubelet_tls_verify: false
    logs_config:
      logs_dd_url: vector-haproxy.vector:8282
      # Set to false if SSL is enabled in Vector source configuration
      logs_no_ssl: true
      use_http: true
VALUES
```

_NOTE: When you have the `datadog_agent` source configured, a `helm install` or
`helm upgrade` will output the appropriate values to provide to the datadog helm
chart._

```bash
helm install datadog datadog/datadog --namespace datadog --create-namespace \
	--values dd-agent.yaml --set datadog.apiKey="${DATADOG_API_KEY}"
```

Once the Datadog Agents are running you should be able to see your logs in
Datadog's [Live Tail](https://app.datadoghq.com/logs/livetail?query=sender%3Avector) view,
by filtering for `sender:vector`. You can also use `vector top` to view Vector's
topology and related metrics:

```bash
kubectl --namespace vector exec --stdin --tty statefulset/vector -- vector top
```

### Troubleshooting

To diagnose problems the following commands may prove useful:

For Datadog Agents:

```bash
kubectl --namespace datadog exec --stdin --tty daemonset/datadog -- agent status
```

For the HAProxy:

```bash
kubectl --namespace vector logs --follow deployment/vector-haproxy
```

For the Vector Aggregators:

```bash
kubectl --namespace vector exec --stdin --tty statefulset/vector -- vector tap internal_logs
```

