# Release notes

## 2025.1.0-51

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

## 2025.1.0

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 Setup libvirt SSL
- 0.1.3 Create override for external ceph cinder backend
- 0.1.4 Set unix socket auth method as none
- 0.1.5 Use full image ref for docker official images
- 0.1.6 Enhancement to enable probes override from values.yaml
- 0.1.7 Add libvirt overrides for Victoria and Wallaby
- 0.1.8 Update htk requirements
- 0.1.9 Exec libvirt instead of forking from bash
- 0.1.10 Enable taint toleration for Openstack services jobs
- 0.1.11 Remove unused overrides and update default image
- 0.1.12 Add libvirt exporter as a sidecar
- 0.1.13 Added OCI registry authentication
- 0.1.14 Remove use of exec in libvirt.sh
- 0.1.15 Add support for libvirt to connect to external ceph without any local ceph present
- 0.1.16 Update all Ceph images to Focal
- 0.1.17 Add ovn.yaml values_override, remove dependency from neutron-ovs-agent module
- 0.1.18 Replace node-role.kubernetes.io/master with control-plane
- 0.1.19 Set kubernetes cgroup value equal kubepods.slice to fit systemd cgroup driver
- 0.1.20 Update Ceph to 17.2.6
- 0.1.21 Disable libvirt cgroup functionality for cgroup-v2
- 0.1.22 Set targeted dependency of libvirt with ovn networking backend
- 0.1.23 Add support for enabling vencrypt
- 0.1.24 Include HOSTNAME_FQDN for certificates
- 0.1.25 Add 2023.2 Ubuntu Jammy overrides
- 0.1.26 Update Rook to 1.12.5 and Ceph to 18.2.0
- 0.1.27 Add watch verb to vencrypt cert-manager Role
- 0.1.28 Update Ceph images to Jammy and Reef 18.2.1
- 0.1.29 Update Ceph images to patched 18.2.2 and restore debian-reef repo
- 0.1.30 Add 2024.1 overrides
- 0.1.31 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.1.32 Enable a flag to parse Libvirt Nova metadata in libvirt exporter
- 0.1.33 Handle cgroupv2 correctly
- 0.1.34 Remove hugepages creation test
- 0.1.35 Allow to initialize virtualization modules
- 0.1.36 Allow to generate dynamic config options
- 0.1.37 Make readiness probes more tiny
- 0.1.38 Implement daemonset overrides for libvirt
- 0.1.39 Add 2023.1 overrides for Ubuntu Focal and Jammy
- 0.1.40 Add 2024.2 overrides
- 0.1.41 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.
