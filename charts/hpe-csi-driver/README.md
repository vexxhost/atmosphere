# HPE CSI Driver for Kubernetes Helm chart

The [HPE CSI Driver for Kubernetes](https://scod.hpedev.io/csi_driver/index.html) leverages Hewlett Packard Enterprise primary storage platforms to provide scalable, persistent block and file storage for stateful and ephemeral applications. Currently supported storage platforms include HPE Alletra Storage MP B10000, HPE Alletra 5000/6000/9000, HPE Nimble Storage, HPE Primera and HPE 3PAR.

## Release highlights

The HPE CSI Driver for Kubernetes Helm chart is the primary delivery vehicle for the HPE CSI Driver.

- All resources for the HPE CSI Driver is available on [HPE Storage Container Orchestrator Documentation](https://scod.hpedev.io/) (SCOD).
- Visit [the latest release](https://scod.hpedev.io/csi_driver/index.html#latest_release) on SCOD to learn what's new in this chart.
- The release notes for the HPE CSI Driver are hosted on [GitHub](https://github.com/hpe-storage/csi-driver/tree/master/release-notes).

## Prerequisites

- Most recent Kubernetes distributions are supported
- Recent Ubuntu, SLES or RHEL (and its derives) compute nodes connected to their respective official package repositories
- Helm 3 (Version >= 3.2.0 required)

Refer to [Compatibility & Support](https://scod.hpedev.io/csi_driver/index.html#compatibility_and_support) for currently supported versions of Kubernetes and compute node operating systems.

Depending on which [Container Storage Provider](https://scod.hpedev.io/container_storage_provider/index.html) (CSP) is being used, other prerequisites and requirements may apply, such as storage platform OS and features.

- [HPE Alletra Storage MP B10000, Alletra 9000, Primera and 3PAR](https://scod.hpedev.io/container_storage_provider/hpe_alletra_storage_mp_b10000/index.html)
- [HPE Alletra Storage MP B10000 File Service](https://scod.hpedev.io/container_storage_provider/hpe_alletra_storage_mp_b10000_file_service/index.html)
- [HPE Alletra 5000/6000 and Nimble Storage](https://scod.hpedev.io/container_storage_provider/hpe_alletra_6000/index.html)

## Configuration and installation

The following table lists the configurable parameters of the chart and their default values.

| Parameter                 | Description                                                                                        | Default          |
|---------------------------|----------------------------------------------------------------------------------------------------|------------------|
| disable.nimble            | Disable HPE Nimble Storage CSP `Service`.                                                          | false            |
| disable.primera           | Disable HPE Primera (and 3PAR) CSP `Service`.                                                      | false            |
| disable.alletra6000       | Disable HPE Alletra 5000/6000 CSP `Service`.                                                       | false            |
| disable.alletra9000       | Disable HPE Alletra 9000 CSP `Service`.                                                            | false            |
| disable.alletraStorageMP  | Disable HPE Alletra Storage MP B10000 Block Storage CSP `Service`.                                                      | false            |
| disable.b10000FileService  | Disable HPE Alletra Storage MP B10000 File Service CSP `Service`.                                  | false            |
| disableNodeConformance    | Disable automatic installation of iSCSI, multipath and NFS packages.                               | false            |
| disableNodeConfiguration  | Disables node conformance and configuration.`*`                                                    | false            |
| disableNodeGetVolumeStats | Disable NodeGetVolumeStats call to CSI driver.                                                     | false            |
| disableNodeMonitor        | Disables the Node Monitor that manages stale storage resources.                                    | false            |
| disableHostDeletion       | Disables host deletion by the CSP when no volumes are associated with the host.                    | false            |
| disablePreInstallHooks    | Disable pre-install hooks when the chart is rendered outside of Kubernetes, such as CI/CD systems. | false            |
| imagePullPolicy           | Image pull policy (`Always`, `IfNotPresent`, `Never`).                                             | IfNotPresent     |
| iscsi.chapSecretName      | Secret containing chapUser and chapPassword for iSCSI                                              | ""               |
| logLevel                  | Log level. Can be one of `info`, `debug`, `trace`, `warn` and `error`.                             | info             |
| kubeletRootDir            | The kubelet root directory path.                                                                   | /var/lib/kubelet |
| controller.labels         | Additional labels for HPE CSI Driver controller Pods.                                              | {}               |
| controller.nodeSelector   | Node labels for HPE CSI Driver controller Pods assignment.                                         | {}               |
| controller.affinity       | Affinity rules for the HPE CSI Driver controller Pods.                                             | {}               |
| controller.tolerations    | Node taints to tolerate for the HPE CSI Driver controller Pods.                                    | []               |
| controller.resources      | A resource block with requests and limits for controller containers.                               | From [values.yaml](https://github.com/hpe-storage/co-deployments/blob/master/helm/values/csi-driver) |
| csp.labels                | Additional labels for CSP Pods.                                                                    | {}               |
| csp.nodeSelector          | Node labels for CSP Pods assignment.                                                               | {}               |
| csp.affinity              | Affinity rules for the CSP Pods.                                                                   | {}               |
| csp.tolerations           | Node taints to tolerate for the CSP Pods.                                                          | []               |
| csp.resources             | A resource block with requests and limits for CSP containers.                                      | From [values.yaml](https://github.com/hpe-storage/co-deployments/blob/master/helm/values/csi-driver) |
| node.labels               | Additional labels for HPE CSI Driver node Pods.                                                    | {}               |
| node.nodeSelector         | Node labels for HPE CSI Driver node Pods assignment.                                               | {}               |
| node.affinity             | Affinity rules for the HPE CSI Driver node Pods.                                                   | {}               |
| node.tolerations          | Node taints to tolerate for the HPE CSI Driver node Pods.                                          | []               |
| node.resources            | A resource block with requests and limits for node containers.                                     | From [values.yaml](https://github.com/hpe-storage/co-deployments/blob/master/helm/values/csi-driver) |
| images                    | Key/value pairs of HPE CSI Driver runtime images.                                                  | From [values.yaml](https://github.com/hpe-storage/co-deployments/blob/master/helm/values/csi-driver) |
| maxVolumesPerNode         | Maximum number of volumes the CSI controller will publish to a node.`**`                           | 100 |

`*` = Disabling node conformance and configuration may prevent the CSI driver from functioning properly. See the [manual node configuration](https://scod.hpedev.io/csi_driver/operations.html#manual_node_configuration) section on SCOD to understand the consequences.
`**` = The default value is the current well tested upper limit. Do not increase the default value unless the use case has been well tested.

It's recommended to create a [values.yaml](https://github.com/hpe-storage/co-deployments/blob/master/helm/values/csi-driver) file from the corresponding release of the chart and edit it to fit the environment the chart is being deployed to. Download and edit [a sample file](https://github.com/hpe-storage/co-deployments/blob/master/helm/values/csi-driver).

**Note:** The chart is installed with all components and features enabled using reasonable defaults if no tweaks are needed.

### Installing the chart

To install the chart with the name `my-hpe-csi-driver`:

Add HPE helm repo:

```
helm repo add hpe-storage https://hpe-storage.github.io/co-deployments/
helm repo update
```

Install the latest chart:

```
helm install --create-namespace -n hpe-storage my-hpe-csi-driver hpe-storage/hpe-csi-driver
```

**Note**: By default, the latest stable chart will be installed. If it's labeled with `prerelease` and a "beta" version tag, add `--version X.Y.Z-beta` to the command line to install a "beta" chart.

### Upgrading the chart

Due to the [helm limitation](https://helm.sh/docs/chart_best_practices/custom_resource_definitions/#some-caveats-and-explanations) to not support upgrade of CRDs between different chart versions, helm chart upgrade is not supported.
Our recommendation is to uninstall the existing chart and install the chart with the desired version. CRDs will be preserved between uninstall and install.

#### Upgrading from any version below 3.1.0

This step is only necessary for NVMe/TCP environments.

Clusters running any version prior to 3.1.0 needs to first uninstall the chart (see below) and then delete the `HPENodeInfo` CRD. The information stored in the CRD is transient and recreated at each node driver start.

```
kubectl delete crd/hpenodeinfos.storage.hpe.com
```

The CRD will be recreated at install with the new CRD containing the "nqns" field needed for NVMe/TCP.

#### Uninstalling the chart

To uninstall the `my-hpe-csi-driver` chart:

```
helm uninstall my-hpe-csi-driver -n hpe-storage
```

**Note**: Due to a limitation in Helm, CRDs are not deleted as part of the chart uninstall.

## Using persistent storage with Kubernetes

Enable dynamic provisioning of persistent storage by creating a `StorageClass` API object that references a `Secret` which maps to a supported HPE primary storage backend. Refer to the [HPE CSI Driver for Kubernetes](https://scod.hpedev.io/csi_driver/deployment.html#add_a_hpe_storage_backend) documentation on SCOD. Also, it's helpful to be familiar with [persistent storage concepts](https://kubernetes.io/docs/concepts/storage/volumes/) in Kubernetes prior to deploying stateful workloads.

## Support

The HPE CSI Driver for Kubernetes Helm chart is fully supported by HPE.

Formal support statements for each HPE supported CSP is [available on SCOD](https://scod.hpedev.io/legal/support). Use this facility for formal support of your HPE storage products, including the Helm chart.

## Community

Please file any issues, questions or feature requests you may have [here](https://github.com/hpe-storage/co-deployments/issues) (do not use this facility for support inquiries of your HPE storage product, see [SCOD](https://scod.hpedev.io/legal/support) for support). You may also join our Slack community to chat with HPE folks close to this project. We hang out in `#Alletra`, `#NimbleStorage`, `#3par-primera`, and `#Kubernetes`. Sign up at [developer.hpe.com/slack-signup/](https://developer.hpe.com/slack-signup/) and login at [hpedev.slack.com](https://hpedev.slack.com/)

## Contributing

We value all feedback and contributions. If you find any issues or want to contribute, please feel free to open an issue or file a PR. More details in [CONTRIBUTING.md](https://github.com/hpe-storage/co-deployments/blob/master/CONTRIBUTING.md)

## License

This is open source software licensed using the Apache License 2.0. Please see [LICENSE](https://github.com/hpe-storage/co-deployments/blob/master/LICENSE) for details.
