# Release notes

## 2025.1.0-51

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

## 2025.1.0

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 Make stats cachedump configurable.
- 0.1.3 Remove panko residue
- 0.1.4 Use full image ref for docker official images
- 0.1.5 Update htk requirements
- 0.1.6 Switch to using sidecar for exporter
- 0.1.7 Updated naming for subchart compatibility
- 0.1.8 Enable taint toleration for Openstack services jobs
- 0.1.9 Revert naming for subchart compatibility
- 0.1.10 Updated naming for subchart compatibility
- 0.1.11 Remove gnocchi netpol override
- 0.1.12 Added OCI registry authentication
- 0.1.13 Replace node-role.kubernetes.io/master with control-plane
- 0.1.14 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.1.15 Allow to pass additional service parameters
- 0.1.16 Change deployment type to statefulset
- 0.1.17 Fix statefulset spec format
- 0.1.18 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.
