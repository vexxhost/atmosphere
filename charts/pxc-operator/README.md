# Percona Operator For MySQL

[Percona XtraDB Cluster (PXC)](https://www.percona.com/doc/percona-xtradb-cluster/LATEST/index.html) is a database clustering solution for MySQL. Percona Operator For MySQL allows users to deploy and manage Percona XtraDB Clusters on Kubernetes.

Useful links
* [Operator Github repository](https://github.com/percona/percona-xtradb-cluster-operator)
* [Operator Documentation](https://www.percona.com/doc/kubernetes-operator-for-pxc/index.html)

## Pre-requisites
* Kubernetes 1.30+
* Helm v3

# Installation

This chart will deploy the Operator Pod for the further Percona XtraDB Cluster creation in Kubernetes.

## Installing the Chart
To install the chart with the `pxc` release name using a dedicated namespace (recommended):

```sh
helm repo add percona https://percona.github.io/percona-helm-charts/
helm install my-operator percona/pxc-operator --version 1.20.0 --namespace my-namespace
```

The chart can be customized using the following configurable parameters:

| Parameter                       | Description                                                                                    | Default                                          |
| ------------------------------- | -----------------------------------------------------------------------------------------------| -------------------------------------------------|
| `image`                         | PXC Operator Container image full path                                                         | `percona/percona-xtradb-cluster-operator:1.20.0` |
| `imagePullPolicy`               | PXC Operator Container pull policy                                                             | `IfNotPresent`                                   |
| `containerSecurityContext`      | PXC Operator Container securityContext                                                         | `{}`                                             |
| `imagePullSecrets`              | PXC Operator Pod pull secret                                                                   | `[]`                                             |
| `replicaCount`                  | PXC Operator Pod quantity                                                                      | `1`                                              |
| `tolerations`                   | List of node taints to tolerate                                                                | `[]`                                             |
| `podAnnotations`                | Operator Pod user-defined annotations                                                          | `{}`                                             |
| `resources`                     | Resource requests and limits                                                                   | `{}`                                             |
| `nodeSelector`                  | Labels for Pod assignment                                                                      | `{}`                                             |
| `logStructured`                 | Force PXC operator to print JSON-wrapped log messages                                          | `false`                                          |
| `logLevel`                      | PXC Operator logging level                                                                     | `INFO`                                           |
| `disableTelemetry`              | Disable sending PXC Operator telemetry data to Percona                                         | `false`                                          |
| `maxConcurrentReconciles`       | Limits the number of parallel cluster reconciles                                               | `1`                                              |
| `s3WorkersLimit`                | Adjusts the maximum number of parallel workers used for S3 client                              | `10`                                             |
| `watchAllNamespaces`            | Watch all namespaces (Install cluster-wide)                                                    | `false`                                          |
| `watchNamespace`                | Comma separated list of namespace(s) to watch when different from release namespace            | `""`                                             |
| `createNamespace`               | Create the watched namespace(s)                                                                | `false`                                          |
| `rbac.create`                   | If false RBAC will not be created. RBAC resources will need to be created manually             | `true`                                           |
| `serviceAccount.create`         | If false the ServiceAccounts will not be created. The ServiceAccounts must be created manually | `true`                                           |
| `extraEnvVars`                  | Custom pod environment variables                                                               | `[]`                                             |
| `featureGates.xtrabackupSidecar`| Enable the Xtrabackup Sidecar feature                                                          | `false`                                          |
| `leaderElectionEnabled`         | Enable leader election for the operator (ensures only one active instance)                     | `true`                                           |
| `leaseName`                     | Custom lease name for leader election (must be a valid DNS subdomain); uses operator name if empty | `""`                                         |
| `leaseDuration`                 | Duration that non-leader candidates wait before forcing leader acquisition                     | `60s`                                            |
| `renewDeadline`                 | Duration the acting leader retries refreshing its leadership before giving up                  | `40s`                                            |
| `retryPeriod`                   | Duration clients should wait between attempts to acquire or renew the leader lease             | `10s`                                            |

Specify parameters using `--set key=value[,key=value]` argument to `helm install`

Alternatively a YAML file that specifies the values for the parameters can be provided like this:

```sh
helm install pxc-operator -f values.yaml percona/pxc-operator
```

## Unit Tests

Helm unit tests for operator charts use the `helm-unittest` plugin.

Install the plugin from the repository root:

```sh
make helm-unittest
```

Unit tests for this chart live under `charts/pxc-operator/tests/` and validate
the rendered operator manifests. Prefer focused tests: start with the default
rendered structure, then add one test per optional or conditional value to
verify that setting the value in `values.yaml` renders the expected field.

Run this chart's unit tests with:

```sh
make test-pxc-operator
```

The `HELM` variable can be overridden when a different Helm binary is needed:

```sh
make HELM=/path/to/helm test-pxc-operator
```

## Deploy the database

To deploy Percona XtraDB Cluster run the following command:

```sh
helm install my-db percona/pxc-db
```

See more about Percona XtraDB Cluster in its chart [here](https://github.com/percona/percona-helm-charts/blob/main/charts/pxc-db) or in the [Helm chart installation guide](https://www.percona.com/doc/kubernetes-operator-for-pxc/helm.html).

# Need help?

**Commercial Support**  | **Community Support** |
:-: | :-: |
| <br/>Enterprise-grade assistance for your mission-critical database deployments in containers and Kubernetes. Get expert guidance for complex tasks like multi-cloud replication, database migration and building platforms.<br/><br/>  | <br/>Connect with our engineers and fellow users for general questions, troubleshooting, and sharing feedback and ideas.<br/><br/>  | 
| **[Get Percona Support](https://hubs.ly/Q02ZTH8Q0)** | **[Visit our Forum](https://forums.percona.com/)** |
