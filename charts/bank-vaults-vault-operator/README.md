# vault-operator

Kubernetes operator for Hashicorp Vault

**Homepage:** <https://bank-vaults.dev>

## TL;DR;

```bash
helm install --generate-name --wait oci://ghcr.io/bank-vaults/helm-charts/vault-operator
```

## Values

The following table lists the configurable parameters of the Helm chart.

| Parameter | Type | Default | Description |
| --- | ---- | ------- | ----------- |
| `replicaCount` | int | `1` | Number of replicas (pods) to launch. |
| `pdb.create` | bool | `true` | Create pod disruption budget if replicaCount > 1. |
| `pdb.minAvailable` | int | `1` | Min available for PDB. |
| `image.repository` | string | `"ghcr.io/bank-vaults/vault-operator"` | Name of the image repository to pull the container image from. |
| `image.pullPolicy` | string | `"IfNotPresent"` | [Image pull policy](https://kubernetes.io/docs/concepts/containers/images/#updating-images) for updating already existing images on a node. |
| `image.tag` | string | `""` | Image tag override for the default value (chart appVersion). |
| `image.imagePullSecrets` | list | `[]` | Reference to one or more secrets to be used when [pulling images](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#create-a-pod-that-uses-your-secret) (from private registries). (`global.imagePullSecrets` is also supported) |
| `image.bankVaultsRepository` | string | `""` | Bank-Vaults image repository **Deprecated:** use `bankVaults.image.repository` instead. |
| `image.bankVaultsTag` | string | `""` | Bank-Vaults image tag **Deprecated:** use `bankVaults.image.tag` instead. |
| `bankVaults.image.repository` | string | `"ghcr.io/bank-vaults/bank-vaults"` | Bank-Vaults image repository. |
| `bankVaults.image.tag` | string | `"v1.31.0"` | Bank-Vaults image tag (pinned to supported Bank-Vaults version). |
| `nameOverride` | string | `""` | A name in place of the chart name for `app:` labels. |
| `fullnameOverride` | string | `""` | A name to substitute for the full names of resources. |
| `watchNamespace` | string | `""` | The namespace where the operator watches for vault CR objects. If not defined all namespaces are watched. |
| `syncPeriod` | string | `"1m"` |  |
| `crdAnnotations` | object | `{}` | Annotations to be added to CRDs. |
| `labels` | object | `{}` | Labels to be added to deployments. |
| `podLabels` | object | `{}` | Labels to be added to pods. |
| `podAnnotations` | object | `{}` | Annotations to be added to pods. |
| `serviceAccount.create` | bool | `true` | Enable service account creation. |
| `serviceAccount.annotations` | object | `{}` | Annotations to be added to the service account. |
| `serviceAccount.name` | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template. |
| `service.annotations` | object | `{}` | Annotations to be added to the service. |
| `service.type` | string | `"ClusterIP"` | Kubernetes [service type](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types). |
| `service.name` | string | `""` | The name of the service to use. If not set, a name is generated using the fullname template. |
| `service.externalPort` | int | `80` |  |
| `service.internalPort` | int | `8080` |  |
| `resources` | object | `{}` | Container resource [requests and limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/). See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#resources) for details. |
| `nodeSelector` | object | `{}` | [Node selector](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector) configuration. |
| `tolerations` | list | `[]` | [Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) for node taints. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#scheduling) for details. |
| `affinity` | object | `{}` | [Affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity) configuration. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#scheduling) for details. |
| `priorityClassName` | string | `""` | Specify a priority class name to set [pod priority](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/#pod-priority). |
| `podSecurityContext` | object | `{}` | Pod [security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-the-security-context-for-a-pod). See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#security-context) for details. |
| `securityContext` | object | `{}` | Container [security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-the-security-context-for-a-container). See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/#security-context-1) for details. |
| `terminationGracePeriodSeconds` | int | `10` |  |
| `livenessProbe.initialDelaySeconds` | int | `60` |  |
| `livenessProbe.periodSeconds` | int | `10` |  |
| `livenessProbe.successThreshold` | int | `1` |  |
| `livenessProbe.timeoutSeconds` | int | `1` |  |
| `readinessProbe.periodSeconds` | int | `10` |  |
| `readinessProbe.successThreshold` | int | `1` |  |
| `readinessProbe.timeoutSeconds` | int | `1` |  |
| `psp.enabled` | bool | `false` |  |
| `psp.vaultSA` | string | `"vault"` |  |
| `monitoring.serviceMonitor.enabled` | bool | `false` | Enable Prometheus ServiceMonitor. See the [documentation](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/design.md#servicemonitor) and the [API reference](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api.md#servicemonitor) for details. |
| `monitoring.serviceMonitor.additionalLabels` | object | `{}` |  |
| `monitoring.serviceMonitor.metricRelabelings` | list | `[]` |  |
| `monitoring.serviceMonitor.relabelings` | list | `[]` |  |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`.

