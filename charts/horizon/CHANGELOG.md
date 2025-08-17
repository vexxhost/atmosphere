# Release notes

## 2025.1.0-51

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

## 2025.1.0

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 To avoid wrong version check for mysqlclient
- 0.1.3 Modify Password validator related settings in Horizon
- 0.1.4 Change Issuer to ClusterIssuer
- 0.1.5 Revert - Change Issuer to ClusterIssuer
- 0.1.6 Change Issuer to ClusterIssuer
- 0.1.7 Update glance default policy values
- 0.1.8 Implement "CSRF_COOKIE_HTTPONLY" option support in horizon
- 0.2.0 Remove support for releases before T
- 0.2.1 Make python script PEP8 compliant
- 0.2.2 Use policies in yaml format
- 0.2.3 Add openstack_enable_password_retrieve variable in value
- 0.2.4 Fix OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT value
- 0.2.5 Add Ussuri release support
- 0.2.6 Add Victoria and Wallaby releases support
- 0.2.7 Fix OPENSTACK_ENABLE_PASSWORD_RETRIEVE value
- 0.2.8 Add default polices
- 0.2.9 Removed default policy in chart in favor of default policy in code
- 0.2.10 Helm 3 - Fix Job Labels
- 0.2.11 Update htk requirements repo
- 0.2.12 Support both json and yaml RBAC Policy Format
- 0.2.13 Add container infra api version in values
- 0.2.14 Add OPENSTACK_ENDPOINT_TYPE value
- 0.2.15 Add local_settings.d
- 0.2.16 Fix container-infra value
- 0.2.17 Add custom logo
- 0.2.18 Enable taint toleration for Openstack services
- 0.2.19 Remove unsupported value overrides
- 0.2.20 Add SHOW_OPENRC_FILE value
- 0.2.21 Add helm hook annotations in db-sync and db-init jobs
- 0.2.22 Migrated PodDisruptionBudget resource to policy/v1 API version
- 0.2.23 Add Xena and Yoga value overrides
- 0.2.24 Remove blank lines in logo configmap
- 0.2.25 Added OCI registry authentication
- 0.2.26 Support SSL identity endpoint
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Fix container infra api version in values
- 0.3.2 Update mysql client version to 1.4.0
- 0.3.3 Update mysql client version in django.wsgi also
- 0.3.4 Add readiness probe timeout
- 0.3.5 Replace node-role.kubernetes.io/master with control-plane
- 0.3.6 Fix container infra api version parsing
- 0.3.7 Update the script to add extra panels
- 0.3.8 Fix horizon tolerations
- 0.3.9 Add Zed overrides
- 0.3.10 Add 2023.1 overrides
- 0.3.11 Rollout when logo configmap is changed
- 0.3.12 Add Ubuntu Jammy overrides
- 0.3.13 Make selenium v4 syntax optional
- 0.3.14 Add 2023.2 Ubuntu Jammy overrides
- 0.3.15 Update osh-selenium image used by default
- 0.3.16 Add support for custom panels
- 0.3.17 Set ingress annotation proxy-body-size=300m by default
- 0.3.18 Enable custom annotations for Openstack pods
- 0.3.19 Add 2024.1 overrides
- 0.3.20 Enable custom annotations for Openstack secrets
- 0.3.21 Update images used by default
- 0.3.22 Align with 2024.1 requirements
- 0.3.23 Use global wsgi subinterpreter
- 0.3.24 Use base64 values for custom logo
- 0.3.25 Implement "CSRF_TRUSTED_ORIGINS" option support in horizon
- 0.3.26 Fix templating of CSRF_TRUSTED_ORIGINS
- 0.3.27 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.28 Add WEBSSO_KEYSTONE_URL value
- 0.3.29 Add 2024.2 Ubuntu Jammy overrides
- 0.3.30 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
