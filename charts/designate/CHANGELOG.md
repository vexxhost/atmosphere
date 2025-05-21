# Release notes

## 2025.1.0-15

## 2025.1.0

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 Added post-install and post-upgrade helm hooks on Jobs
- 0.2.0 Remove support for releases before T
- 0.2.1 Use policies in yaml format
- 0.2.2 Update htk requirements repo
- 0.2.3 Fix extra volume mounts
- 0.2.4 Update default image values to Wallaby
- 0.2.5 Migrated PodDisruptionBudget resource to policy/v1 API version
- 0.2.6 Added OCI registry authentication
- 0.2.7 Use HTTP probe instead of TCP probe
- 0.2.8 Remove default policy rules
- 0.2.9 Define service_type in keystone_authtoken to support application credentials with access rules
- 0.2.10 Uses uWSGI for API service
- 0.2.11 Enable custom annotations for Openstack pods
- 0.2.12 Enable custom annotations for Openstack secrets
- 0.2.13 Update images used by default
- 0.2.14 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.2.15 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
