# pxс-operator: A chart for installing Percona Kubernetes Operator for Percona XtraDB Cluster

This chart implements the Percona XtraDB Cluster Operator deployment. [Percona XtraDB Cluster](https://www.percona.com/doc/percona-xtradb-cluster/LATEST/index.html) is a database clustering solution for MySQL. The Operator itself can be found here:
* <https://github.com/percona/percona-xtradb-cluster-operator>

## Pre-requisites
* Kubernetes 1.17+
* PV support on the underlying infrastructure - only if you are provisioning persistent volume(s).
* Helm v3

## Deployment Details
* <https://kubernetes.io/docs/concepts/workloads/controllers/deployment/>

## Chart Details
This chart will:
* deploy a PXC Operator Pod for the further MySQL XtraDB Cluster creation in K8S.

### Installing the Chart
To install the chart with the `pxc` release name using a dedicated namespace (recommended):

```sh
helm repo add percona https://percona.github.io/percona-helm-charts/
helm install my-operator percona/pxc-operator --version 1.10.0 --namespace my-namespace
```

The chart can be customized using the following configurable parameters:

| Parameter                       | Description                                                             | Default                                          |
| ------------------------------- | ------------------------------------------------------------------------| -------------------------------------------------|
| `image`                         | PXC Operator Container image full path                                  | `percona/percona-xtradb-cluster-operator:1.10.0` |
| `imagePullPolicy`               | PXC Operator Container pull policy                                      | `Always`                                         |
| `imagePullSecrets`              | PXC Operator Pod pull secret                                            | `[]`                                             |
| `replicaCount`                  | PXC Operator Pod quantity                                               | `1`                                              |
| `tolerations`                   | List of node taints to tolerate                                         | `[]`                                             |
| `resources`                     | Resource requests and limits                                            | `{}`                                             |
| `nodeSelector`                  | Labels for Pod assignment                                               | `{}`                                             |

Specify parameters using `--set key=value[,key=value]` argument to `helm install`

Alternatively a YAML file that specifies the values for the parameters can be provided like this:

```sh
helm install pxc-operator -f values.yaml percona/pxc-operator
```
