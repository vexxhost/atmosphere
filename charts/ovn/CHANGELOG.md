# Release notes

## 2025.1.0-39

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

## 2025.1.0

- Add OVN Kubernetes support
- Add OVN network logging parser
- 0.1.0 Add OVN!
- 0.1.1 Fix ovn db persistence issue
- 0.1.2 Add bridge-mapping configuration
- 0.1.3 Fix system-id reuse
- 0.1.4 Add support for OVN HA + refactor
- 0.1.5 Add ubuntu_focal and ubuntu_jammy overrides
- 0.1.6 Fix ovsdb port number
- 0.1.7 Use host network for ovn controller pods
- 0.1.8 Fix attaching interfaces to the bridge
- 0.1.9 Make ovn db file path as configurable
- 0.1.10 Fix typo in the controller init script
- 0.1.11 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.1.12 Fix oci_image_registry secret name
- 0.1.13 Allow share OVN DB NB/SB socket
- 0.1.14 Make the label for OVN controller gateway configurable
- 0.1.15 Fix resources
- 0.1.16 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle

### New Features

- Implement daemonset overrides

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.
