# Release notes

## 2025.1.0-51

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

## 2025.1.0

- Use oslo.middleware healthcheck endpoint for liveness and readiness

### Bug Fixes

- Fix the number of max active fernet keys

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 UPDATE
- 0.1.2 UPDATE
- 0.1.3 UPDATE
- 0.1.4 UPDATE
- 0.1.5 Revert clusterissuer change
- 0.1.6 Fix typo in subPath entry
- 0.1.7 Move rabbit-init to dynamic dependency
- 0.1.8 Change Issuer to ClusterIssuer
- 0.1.9 Add helm.sh/hook related annotations
- 0.1.10 Update RBAC apiVersion from /v1beta1 to /v1
- 0.1.11 Remove congress residue
- 0.1.12 Add helm hook conditional
- 0.1.13 Fix Error - wrong number of args for set
- 0.1.14 Remove setup helm hooks
- 0.2.0 Remove support for releases before T
- 0.2.1 Remove paste ini config settings
- 0.2.2 Make python script PEP8 compliant
- 0.2.3 Adding rabbitmq TLS logic
- 0.2.4 Use policies in yaml format
- 0.2.5 Mount rabbitmq TLS secret
- 0.2.6 Modify default probe timings
- 0.2.7 Add Ussuri release support
- 0.2.8 Remove member bootstrap logic
- 0.2.9 Add Victoria and Wallaby releases support
- 0.2.10 Make internal TLS more robust
- 0.2.11 Add missing slash
- 0.2.12 Helm 3 - Fix Job Labels
- 0.2.13 Helm 3 - Fix more Job Labels
- 0.2.14 Update htk requirements repo
- 0.2.15 Reduce log chattiness
- 0.2.16 Remove extra fsGroup
- 0.2.17 Update default image references
- 0.2.18 Remove default policy
- 0.2.19 Revert Reduce log chattiness
- 0.2.20 Enable taint toleration for Openstack services
- 0.2.21 Updated naming for subchart compatibility
- 0.2.22 Remove older values overrides
- 0.2.23 Remove usage of six
- 0.2.24 Remove unused admin port in keystone
- 0.2.25 Migrated CronJob resource to batch/v1 API version & PodDisruptionBudget to policy/v1
- 0.2.26 Add Xena and Yoga values overrides
- 0.2.27 Use LOG.warning instead of deprecated LOG.warn
- 0.2.28 Added OCI registry authentication
- 0.2.29 Support TLS endpoints
- 0.2.30 Distinguish between port number of internal endpoint and binding port number
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Replace node-role.kubernetes.io/master with control-plane
- 0.3.2 Add Zed overrides
- 0.3.3 Add 2023.1 overrides
- 0.3.4 Add Ubuntu Jammy overrides
- 0.3.5 Add 2023.2 Ubuntu Jammy overrides
- 0.3.6 Use region option in keystone endpoint-update.py
- 0.3.7 Make keystone TLS configuration granular
- 0.3.8 Enable custom annotations for Openstack pods
- 0.3.9 Add 2024.1 overrides
- 0.3.10 Allow custom annotations on jobs
- 0.3.11 Fix custom annotations when helm3_hook is disabled
- 0.3.12 Enable custom annotations for Openstack secrets
- 0.3.13 Update images used by default
- 0.3.14 Align db scripts with sqlalchemy 2.0
- 0.3.15 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.16 Align db scripts with Sqlalchemy 2
- 0.3.17 Add 2024.2 Ubuntu Jammy overrides
- 0.3.18 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
