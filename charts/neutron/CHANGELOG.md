# Release notes

## 2025.1.0-51

- Fix neutron ironic agent fail to start with missing host information.
- Create multiple Keystone service accounts to access to
  other Openstack APIs
- Add interface name parameter for DPDK configs
- Fix OVN support in neutron DHCP.
- Fix port duplication in neutron server deployment
- Add new cron job for neutron ovn db sync that runs evey 5 mins by default.
  This could be use as log alert if any part out of sync.
  Or it can be use as automatic repair method to prevent
  OVN DB got modified and failed it's purpose.
  This cron job is default disabled.
  Set `.Values.manifests.cron_job_ovn_db_sync_repair` to
  `true` to enable the cronjob.
  The sync mode for the cronjob is default only for check sync status.
  Set `.Values.jobs.ovn_db_sync_repair.sync_mode` to `repair` for enable
  automatic repair and sync OVN DB from Neutron DB.

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

### Bug Fixes

- Since 0e7fe77f49 neutron-ironic-agent has had an invalid volumes spec. Fix the
  spec so the agent can run.

## 2025.1.0

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.

- 0.1.0 Initial Chart
- 0.1.1 Change helm-toolkit dependency version to ">= 0.1.0"
- 0.1.2 fixes tls issue
- 0.1.3 Update neutron to use Nginx apparmor profile
- 0.1.4 Pass ovs agent config to dhcp agent
- 0.1.5 Add missing flags to nginx container in neutron chart
- 0.1.6 Use HostToContainer mountPropagation
- 0.1.7 Change Issuer to ClusterIssuer
- 0.1.8 Revert Change Issuer to ClusterIssuer
- 0.1.9 Update ovs agent to support host/label overrides
- 0.1.10 Change Issuer to ClusterIssuer
- 0.1.11 Added the helm.sh/hook, helm.sh/hook-weight annotations
- 0.1.12 Removed "name" parameter from Rally tests
- 0.2.0 Remove support for releases before T
- 0.2.1 Adding rabbitmq TLS logic
- 0.2.2 Use policies in yaml format
- 0.2.3 Mount rabbitmq TLS secret
- 0.2.4 Add Ussuri release support
- 0.2.5 Use rootwrap daemon
- 0.2.6 Fix neutron agent-init script
- 0.2.7 Made dnsmasq.conf overridable in configmap-bin
- 0.2.8 Add Victoria and Wallaby releases support
- 0.2.9 Add option to disable helm.sh/hook annotations
- 0.2.10 Update htk requirements repo
- 0.2.11 Improve health probe logging
- 0.2.12 Fix infinite recursion deadlock on netns cleanup cron
- 0.2.13 Enable taint toleration for Openstack services
- 0.2.14 Migrate IP from bridge for auto_bridge_add
- 0.2.15 Remove unsupported values overrides
- 0.2.16 Remove usage of six
- 0.2.17 Migrated PodDisruptionBudget resource to policy/v1 API version
- 0.2.18 Updated naming for subchart compatibility
- 0.2.19 Added qdhcp NS host validation for deleting wrong namespaces.
- 0.2.20 Add Xena and Yoga values overrides
- 0.2.21 Fix for qdhcp NS host validation for deleting wrong namespaces.
- 0.2.22 Fix /run/xtables.lock may be a directory
- 0.2.23 Add neutron_netns_cleanup_cron release image override, so that the respective release image is used
- 0.2.24 Added OCI registry authentication
- 0.2.25 Support TLS endpoints
- 0.2.26 Use HTTP probe instead of TCP probe
- 0.2.27 Distinguish between port number of internal endpoint and binding port number
- 0.3.0 Remove support for Train and Ussuri
- 0.3.1 Remove default policy rules
- 0.3.2 Use correct labels for ovs which uses one daemonset for ovs-db and ovs-vswitchd
- 0.3.3 Add OVN Support
- 0.3.4 Replace node-role.kubernetes.io/master with control-plane
- 0.3.5 Fix health probe for OVN metadata agent
- 0.3.6 Fix the issue that ovn metadata not work in muti-node enviroment
- 0.3.7 Sync neutron db to ovn nb db when neutron-server start
- 0.3.8 Define service_type in keystone_authtoken to support application credentials with access rules
- 0.3.9 Extend neutron liveness probe with readiness probe
- 0.3.10 Configure keystone authentication credentials for placement
- 0.3.11 Add Zed overrides
- 0.3.12 Update oslo_messaging_RPCClient and get_rpc_transport
- 0.3.13 Remove duplicated argument when running a liveness check
- 0.3.14 Add 2023.1 overrides
- 0.3.15 Add asap2 support
- 0.3.16 Use service tokens
- 0.3.17 Add exec probe timeouts
- 0.3.18 Improve OVN support
- 0.3.19 Fix getting IP for interface when there are multiple IPs assigned
- 0.3.20 Add Ubuntu Jammy overrides
- 0.3.21 Run native netns cleanup
- 0.3.22 Add BGP Dragent support for running dragent agents as daemonsets
- 0.3.23 Fix start function template
- 0.3.24 Add 2023.2 Ubuntu Jammy overrides
- 0.3.25 Fix ovs member support for readiness
- 0.3.26 Fix ovs options to allow multiple options
- 0.3.27 Move old overrides from the tools directory
- 0.3.28 Fix ovn for slow enviroment
- 0.3.29 Disable DVR for OVN floating ip
- 0.3.30 Fix designate auth url
- 0.3.31 FIX ovn-metadata-agent mountPropagation overrides by parent directory
- 0.3.32 Update dpdk override
- 0.3.33 Make sure trust on command is applied to avoid race-condition with ovs-dpdk
- 0.3.34 Update metadata endpoint
- 0.3.35 Do not attach non-existing interfaces to br-ex bridge for OVS agent
- 0.3.36 Enable custom annotations for Openstack pods
- 0.3.37 Proper chown /run/openvswitch/db.sock under OVN
- 0.3.38 Add 2024.1 overrides
- 0.3.39 Ensure that the script handles cases where the PID file exists but is empty or does not contain the expected data structure.
- 0.3.40 Fix ovs bridge creation in mappings for DPDK
- 0.3.41 Enable custom annotations for Openstack secrets
- 0.3.42 Update images used by default
- 0.3.43 Switch neutron to uWSGI
- 0.3.44 Add OVN VPNaas support
- 0.3.45 Fix ironic/baremetal authentication
- 0.3.46 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.3.47 Add service role to the Neutron user
- 0.3.48 Add 2024.2 Ubuntu Jammy overrides
- 0.3.49 Add node_selector_* for OVN VPN agent
- 0.3.50 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle
