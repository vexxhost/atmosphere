IMAGE_LIST = {
    "bootstrap": "quay.io/vexxhost/heat:zed",
    "db_drop": "quay.io/vexxhost/heat:zed",
    "db_init": "quay.io/vexxhost/heat:zed",
    "dep_check": "quay.io/vexxhost/kubernetes-entrypoint:latest",
    "ks_endpoints": "quay.io/vexxhost/heat:zed",
    "ks_service": "quay.io/vexxhost/heat:zed",
    "ks_user": "quay.io/vexxhost/heat:zed",
    "barbican_api": "quay.io/vexxhost/barbican:wallaby",
    "barbican_db_sync": "quay.io/vexxhost/barbican:wallaby",
    "cinder_api": "quay.io/vexxhost/cinder:zed",
    "cinder_scheduler": "quay.io/vexxhost/cinder:zed",
    "cinder_volume": "quay.io/vexxhost/cinder:zed",
    "cinder_volume_usage_audit": "quay.io/vexxhost/cinder:zed",
    "cinder_backup": "quay.io/vexxhost/cinder:zed",
    "cinder_storage_init": "quay.io/vexxhost/cinder:zed",
    "cinder_backup_storage_init": "quay.io/vexxhost/cinder:zed",
    "glance_api": "quay.io/vexxhost/glance:zed",
    "glance_db_sync": "quay.io/vexxhost/glance:zed",
    "glance_metadefs_load": "quay.io/vexxhost/glance:zed",
    "glance_registry": "quay.io/vexxhost/glance:zed",
    "glance_storage_init": "quay.io/vexxhost/glance:zed",
    "heat_api": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "heat_cfn": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "heat_cloudwatch": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "heat_db_sync": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "heat_engine": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "heat_engine_cleaner": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "heat_purge_deleted": "us-docker.pkg.dev/vexxhost-infra/openstack/heat:wallaby",
    "horizon": "us-docker.pkg.dev/vexxhost-infra/openstack/horizon:wallaby",
    "horizon_db_sync": "us-docker.pkg.dev/vexxhost-infra/openstack/horizon:wallaby",
    "keystone_api": "quay.io/vexxhost/keystone:wallaby",
    "keystone_credential_cleanup": "quay.io/vexxhost/heat:wallaby",
    "keystone_credential_rotate": "quay.io/vexxhost/keystone:wallaby",
    "keystone_credential_setup": "quay.io/vexxhost/keystone:wallaby",
    "keystone_db_sync": "quay.io/vexxhost/keystone:wallaby",
    "keystone_domain_manage": "quay.io/vexxhost/heat:wallaby",
    "keystone_fernet_rotate": "quay.io/vexxhost/keystone:wallaby",
    "keystone_fernet_setup": "quay.io/vexxhost/keystone:wallaby",
    "neutron_bagpipe_bgp": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_db_sync": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_dhcp": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_ironic_agent": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_l2gw": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_l3": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_linuxbridge_agent": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_metadata": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_netns_cleanup_cron": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_openvswitch_agent": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_server": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_sriov_agent": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "neutron_sriov_agent_init": "us-docker.pkg.dev/vexxhost-infra/openstack/neutron:wallaby",
    "nova_api": "quay.io/vexxhost/nova:wallaby",
    "nova_archive_deleted_rows": "quay.io/vexxhost/nova:wallaby",
    "nova_cell_setup": "quay.io/vexxhost/nova:wallaby",
    "nova_cell_setup_init": "quay.io/vexxhost/heat:wallaby",
    "nova_compute": "quay.io/vexxhost/nova:wallaby",
    "nova_compute_ironic": "docker.io/kolla/ubuntu-source-nova-compute-ironic:wallaby",
    "nova_compute_ssh": "quay.io/vexxhost/nova-ssh:wallaby",
    "nova_conductor": "quay.io/vexxhost/nova:wallaby",
    "nova_consoleauth": "quay.io/vexxhost/nova:wallaby",
    "nova_db_sync": "quay.io/vexxhost/nova:wallaby",
    "nova_novncproxy": "quay.io/vexxhost/nova:wallaby",
    "nova_novncproxy_assets": "quay.io/vexxhost/nova:wallaby",
    "nova_placement": "quay.io/vexxhost/nova:wallaby",
    "nova_scheduler": "quay.io/vexxhost/nova:wallaby",
    "nova_service_cleaner": "quay.io/vexxhost/cli:latest",
    "nova_spiceproxy": "quay.io/vexxhost/nova:wallaby",
    "nova_spiceproxy_assets": "quay.io/vexxhost/nova:wallaby",
    "octavia_api": "quay.io/vexxhost/octavia:zed",
    "octavia_db_sync": "quay.io/vexxhost/octavia:zed",
    "octavia_health_manager": "quay.io/vexxhost/octavia:zed",
    "octavia_health_manager_init": "quay.io/vexxhost/heat:zed",
    "octavia_housekeeping": "quay.io/vexxhost/octavia:zed",
    "octavia_worker": "quay.io/vexxhost/octavia:zed",
    "placement": "quay.io/vexxhost/placement:wallaby",
    "placement_db_sync": "quay.io/vexxhost/placement:wallaby",
    "senlin_api": "us-docker.pkg.dev/vexxhost-infra/openstack/senlin:wallaby",
    "senlin_conductor": "us-docker.pkg.dev/vexxhost-infra/openstack/senlin:wallaby",
    "senlin_db_sync": "us-docker.pkg.dev/vexxhost-infra/openstack/senlin:wallaby",
    "senlin_engine": "us-docker.pkg.dev/vexxhost-infra/openstack/senlin:wallaby",
    "senlin_engine_cleaner": "us-docker.pkg.dev/vexxhost-infra/openstack/senlin:wallaby",
    "senlin_health_manager": "us-docker.pkg.dev/vexxhost-infra/openstack/senlin:wallaby",
    "ceph_bootstrap": "docker.io/openstackhelm/ceph-daemon:change_770201_ubuntu_bionic-20210113",
    "ceph_cephfs_provisioner": "docker.io/openstackhelm/ceph-cephfs-provisioner:ubuntu_bionic-20200521",
    "ceph_config_helper": "docker.io/openstackhelm/ceph-config-helper:change_770201_ubuntu_bionic-20210113",
    "ceph_rbd_provisioner": "docker.io/openstackhelm/ceph-rbd-provisioner:change_770201_ubuntu_bionic-20210113",
    "csi_provisioner": "k8s.gcr.io/sig-storage/csi-provisioner:v3.1.0",
    "csi_snapshotter": "k8s.gcr.io/sig-storage/csi-snapshotter:v6.0.0",
    "csi_attacher": "k8s.gcr.io/sig-storage/csi-attacher:v3.4.0",
    "csi_resizer": "k8s.gcr.io/sig-storage/csi-resizer:v1.4.0",
    "csi_registrar": "k8s.gcr.io/sig-storage/csi-node-driver-registrar:v2.5.0",
    "cephcsi": "quay.io/cephcsi/cephcsi:v3.6.2",
    "image_repo_sync": "docker.io/library/docker:17.07.0",
    "libvirt": "docker.io/openstackhelm/libvirt:latest-ubuntu_focal",
    "libvirt_exporter": "vexxhost/libvirtd-exporter:latest",
    "memcached": "docker.io/library/memcached:1.5.5",
    "prometheus_memcached_exporter": "docker.io/prom/memcached-exporter:v0.4.1",
    "openvswitch_db_server": "quay.io/vexxhost/openvswitch:2.17.3",
    "openvswitch_vswitchd": "quay.io/vexxhost/openvswitch:2.17.3",
    "magnum_api": "quay.io/vexxhost/magnum@sha256:46e7c910780864f4532ecc85574f159a36794f37aac6be65e4b48c46040ced17",  # noqa
    "magnum_conductor": "quay.io/vexxhost/magnum@sha256:46e7c910780864f4532ecc85574f159a36794f37aac6be65e4b48c46040ced17",  # noqa
    "magnum_db_sync": "quay.io/vexxhost/magnum@sha256:46e7c910780864f4532ecc85574f159a36794f37aac6be65e4b48c46040ced17",  # noqa
    "memcached": "docker.io/library/memcached:1.6.17",
    "mysqld_exporter": "quay.io/prometheus/mysqld-exporter:v0.14.0",
    "percona_xtradb_cluster_haproxy": "docker.io/percona/percona-xtradb-cluster-operator:1.10.0-haproxy",
    "percona_xtradb_cluster": "docker.io/percona/percona-xtradb-cluster:5.7.39-31.61",
    "prometheus_memcached_exporter": "quay.io/prometheus/memcached-exporter:v0.10.0",
    "rabbit_init": "docker.io/library/rabbitmq:3.8.23-management",
}

NODE_SELECTOR_CONTROL_PLANE = {
    "openstack-control-plane": "enabled",
}

NAMESPACE_CERT_MANAGER = "cert-manager"
NAMESPACE_MONITORING = "monitoring"

HELM_RELEASE_CERT_MANAGER = {
    "alias": "certManager",
    "chart_name": "cert-manager",
    "chart_version": "v1.7.1",
    "release_name": "cert-manager",
    "values": {
        "installCRDs": True,
        "featureGates": "AdditionalCertificateOutputFormats=true",
        "volumes": [
            {
                "name": "etc-ssl-certs",
                "hostPath": {
                    "path": "/etc/ssl/certs",
                },
            }
        ],
        "volumeMounts": [
            {
                "name": "etc-ssl-certs",
                "mountPath": "/etc/ssl/certs",
                "readOnly": True,
            }
        ],
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "webhook": {
            "extraArgs": [
                "--feature-gates=AdditionalCertificateOutputFormats=true",
            ],
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        },
        "cainjector": {
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        },
        "startupapicheck": {
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        },
    },
    "values_from": [],
}

HELM_RELEASE_NODE_FEATURE_DISCOVERY = {
    "chart_name": "node-feature-discovery",
    "chart_version": "0.11.2",
    "release_name": "node-feature-discovery",
    "values": {"master": {"nodeSelector": NODE_SELECTOR_CONTROL_PLANE}},
    "values_from": [],
}

HELM_RELEASE_PXC_OPERATOR = {
    "chart_name": "pxc-operator",
    "chart_version": "1.10.0",
    "release_name": "pxc-operator",
    "values": {
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
    },
    "values_from": [],
}

HELM_RELEASE_RABBITMQ_CLUSTER_OPERATOR = {
    "chart_name": "rabbitmq-cluster-operator",
    "chart_version": "2.6.6",
    "release_name": "rabbitmq-cluster-operator",
    "values": {
        "rabbitmqImage": {"repository": "library/rabbitmq", "tag": "3.10.2-management"},
        "credentialUpdaterImage": {
            "repository": "rabbitmqoperator/default-user-credential-updater",
            "tag": "1.0.2",
        },
        "clusterOperator": {
            "fullnameOverride": "rabbitmq-cluster-operator",
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
            "image": {
                "repository": "rabbitmqoperator/cluster-operator",
                "tag": "1.13.1",
            },
        },
        "msgTopologyOperator": {
            "fullnameOverride": "rabbitmq-messaging-topology-operator",
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
            "image": {
                "repository": "rabbitmqoperator/messaging-topology-operator",
                "tag": "1.6.0",
            },
        },
        "useCertManager": True,
    },
    "values_from": [],
}

HELM_RELEASE_INGRESS_NGINX = {
    "alias": "ingressNginx",
    "chart_name": "ingress-nginx",
    "chart_version": "4.0.17",
    "release_name": "ingress-nginx",
    "values": {
        "controller": {
            "config": {"proxy-buffer-size": "16k"},
            "dnsPolicy": "ClusterFirstWithHostNet",
            "hostNetwork": True,
            "ingressClassResource": {"name": "openstack"},
            "ingressClass": "openstack",
            "kind": "DaemonSet",
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
            "service": {"type": "ClusterIP"},
            "admissionWebhooks": {"port": 7443},
        },
        "defaultBackend": {"enabled": True},
        "tcp": {
            "5354": "openstack/minidns:5354",
        },
        "udp": {
            "5354": "openstack/minidns:5354",
        },
    },
    "values_from": [],
}
