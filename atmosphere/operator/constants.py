import pkg_resources

from atmosphere.operator import utils

IMAGE_LIST = {
    "bootstrap": "quay.io/vexxhost/heat:zed",
    "db_drop": "quay.io/vexxhost/heat:zed",
    "db_init": "quay.io/vexxhost/heat:zed",
    "dep_check": "quay.io/vexxhost/kubernetes-entrypoint:latest",
    "ks_endpoints": "quay.io/vexxhost/heat:zed",
    "ks_service": "quay.io/vexxhost/heat:zed",
    "ks_user": "quay.io/vexxhost/heat:zed",
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

PROMETHEUS_MONITOR_RELABELING_SET_NODE_NAME_TO_INSTANCE = {
    "sourceLabels": ["__meta_kubernetes_pod_node_name"],
    "targetLabel": "instance",
}
PROMETHEUS_MONITOR_RELABELING_SET_POD_NAME_TO_INSTANCE = {
    "sourceLabels": ["__meta_kubernetes_pod_name"],
    "targetLabel": "instance",
}
PROMETHEUS_MONITOR_RELABELING_DROP_ALL_KUBERNETES_LABELS = {
    "action": "labeldrop",
    "regex": "^(container|endpoint|namespace|pod|node|service)$",
}

PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME = [
    PROMETHEUS_MONITOR_RELABELING_SET_POD_NAME_TO_INSTANCE,
    PROMETHEUS_MONITOR_RELABELING_DROP_ALL_KUBERNETES_LABELS,
]
PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME = [
    PROMETHEUS_MONITOR_RELABELING_SET_NODE_NAME_TO_INSTANCE,
    PROMETHEUS_MONITOR_RELABELING_DROP_ALL_KUBERNETES_LABELS,
]
PROMETHEUS_MONITOR_RELABELINGS_KUBELET = [
    {"sourceLabels": ["__metrics_path__"], "targetLabel": "metrics_path"},
    {"sourceLabels": ["node"], "targetLabel": "instance"},
    PROMETHEUS_MONITOR_RELABELING_DROP_ALL_KUBERNETES_LABELS,
]

HELM_RELEASE_CERT_MANAGER = {
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
    "chart_version": "2.5.2",
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

HELM_RELEASE_KUBE_PROMETHEUS_STACK = {
    "chart_name": "kube-prometheus-stack",
    "chart_version": "41.7.3",
    "release_name": "kube-prometheus-stack",
    "values": {
        "defaultRules": {
            "disabled": {
                # NOTE(mnaser): https://github.com/prometheus-community/helm-charts/issues/144
                #               https://github.com/openshift/cluster-monitoring-operator/issues/248
                "etcdHighNumberOfFailedGRPCRequests": True
            }
        },
        "alertmanager": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
            },
            "alertmanagerSpec": {
                "storage": {
                    "volumeClaimTemplate": {
                        "spec": {
                            "storageClassName": "general",
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "40Gi"}},
                        }
                    }
                },
                "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
            },
        },
        "grafana": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
            },
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        },
        "kubeApiServer": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME
            }
        },
        "kubelet": {
            "serviceMonitor": {
                "cAdvisorRelabelings": PROMETHEUS_MONITOR_RELABELINGS_KUBELET,
                "probesRelabelings": PROMETHEUS_MONITOR_RELABELINGS_KUBELET,
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_KUBELET,
            }
        },
        "kubeControllerManager": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME,
            }
        },
        "coreDns": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
            }
        },
        "kubeEtcd": {
            "service": {
                "port": 2379,
                "targetPort": 2379,
            },
            "serviceMonitor": {
                "scheme": "https",
                "serverName": "localhost",
                "insecureSkipVerify": False,
                "caFile": "/etc/prometheus/secrets/kube-prometheus-stack-etcd-client-cert/ca.crt",
                "certFile": "/etc/prometheus/secrets/kube-prometheus-stack-etcd-client-cert/healthcheck-client.crt",
                "keyFile": "/etc/prometheus/secrets/kube-prometheus-stack-etcd-client-cert/healthcheck-client.key",
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME,
            },
        },
        "kubeScheduler": {
            "service": {"port": 10259, "targetPort": 10259},
            "serviceMonitor": {
                "https": True,
                "insecureSkipVerify": True,
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME,
            },
        },
        "kubeProxy": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME
            }
        },
        "kube-state-metrics": {
            "prometheus": {
                "monitor": {
                    "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
                }
            },
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        },
        "prometheus": {
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
            },
            "prometheusSpec": {
                "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
                "secrets": ["kube-prometheus-stack-etcd-client-cert"],
            },
            "additionalServiceMonitors": [
                {
                    "name": "ceph",
                    "jobLabel": "application",
                    "selector": {"matchLabels": {"application": "ceph"}},
                    "namespaceSelector": {"matchNames": ["openstack"]},
                    "endpoints": [
                        {
                            "port": "metrics",
                            "honorLabels": True,
                            "relabelings": [
                                {
                                    "action": "replace",
                                    "regex": "(.*)",
                                    "replacement": "ceph",
                                    "targetLabel": "cluster",
                                },
                                PROMETHEUS_MONITOR_RELABELING_DROP_ALL_KUBERNETES_LABELS,
                            ],
                        }
                    ],
                },
                {
                    "name": "coredns",
                    "jobLabel": "app.kubernetes.io/name",
                    "namespaceSelector": {"matchNames": ["openstack"]},
                    "selector": {
                        "matchLabels": {
                            "app.kubernetes.io/name": "coredns",
                            "app.kubernetes.io/component": "metrics",
                        }
                    },
                    "endpoints": [
                        {
                            "port": "metrics",
                            "relabelings": [
                                {
                                    "sourceLabels": [
                                        "__meta_kubernetes_pod_label_application"
                                    ],
                                    "targetLabel": "application",
                                },
                            ]
                            + PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME,
                        }
                    ],
                },
                {
                    "name": "memcached",
                    "jobLabel": "application",
                    "namespaceSelector": {"matchNames": ["openstack"]},
                    "selector": {
                        "matchLabels": {"application": "memcached", "component": "server"}
                    },
                    "endpoints": [
                        {
                            "port": "metrics",
                            "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME,
                        }
                    ],
                },
                {
                    "name": "openstack-exporter",
                    "jobLabel": "jobLabel",
                    "namespaceSelector": {"matchNames": ["openstack"]},
                    "selector": {"matchLabels": {"application": "openstack-exporter"}},
                    "endpoints": [
                        {
                            "interval": "1m",
                            "scrapeTimeout": "30s",
                            "port": "metrics",
                            "relabelings": [
                                {
                                    "action": "replace",
                                    "regex": "(.*)",
                                    "replacement": "default",
                                    "targetLabel": "instance",
                                }
                            ],
                        }
                    ],
                },
            ],
            "additionalPodMonitors": [
                {
                    "name": "ethtool-exporter",
                    "jobLabel": "job",
                    "selector": {"matchLabels": {"application": "ethtool-exporter"}},
                    "podMetricsEndpoints": [
                        {
                            "port": "metrics",
                            "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME,
                        }
                    ],
                },
                {
                    "name": "ipmi-exporter",
                    "jobLabel": "job",
                    "selector": {"matchLabels": {"application": "ipmi-exporter"}},
                    "podMetricsEndpoints": [
                        {
                            "port": "metrics",
                            "interval": "60s",
                            "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME,
                        }
                    ],
                },
                {
                    "name": "percona-xtradb-pxc",
                    "jobLabel": "app.kubernetes.io/component",
                    "namespaceSelector": {"matchNames": ["openstack"]},
                    "selector": {
                        "matchLabels": {
                            "app.kubernetes.io/component": "pxc",
                            "app.kubernetes.io/instance": "percona-xtradb",
                        }
                    },
                    "podMetricsEndpoints": [
                        {
                            "port": "metrics",
                            "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME,
                        }
                    ],
                },
                {
                    "name": "rabbitmq",
                    "jobLabel": "app.kubernetes.io/component",
                    "namespaceSelector": {"matchNames": ["openstack"]},
                    "selector": {
                        "matchLabels": {"app.kubernetes.io/component": "rabbitmq"}
                    },
                    "podMetricsEndpoints": [
                        {
                            "port": "prometheus",
                            "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME,
                        }
                    ],
                },
            ],
        },
        "prometheusOperator": {
            "admissionWebhooks": {"patch": NODE_SELECTOR_CONTROL_PLANE},
            "serviceMonitor": {
                "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
            },
            "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        },
        "prometheus-node-exporter": {
            "extraArgs": [
                "--collector.diskstats.ignored-devices=^(ram|loop|nbd|fd|(h|s|v|xv)d[a-z]|nvme\\d+n\\d+p)\\d+$",
                "--collector.filesystem.fs-types-exclude=^(autofs|binfmt_misc|bpf|cgroup2?|configfs|debugfs|devpts|devtmpfs|fusectl|fuse.squashfuse_ll|hugetlbfs|iso9660|mqueue|nsfs|overlay|proc|procfs|pstore|rpc_pipefs|securityfs|selinuxfs|squashfs|sysfs|tracefs)$",  # noqa: E501
                "--collector.filesystem.mount-points-exclude=^/(dev|proc|run/credentials/.+|sys|var/lib/docker/.+|var/lib/kubelet/pods/.+|var/lib/kubelet/plugins/kubernetes.io/csi/.+|run/containerd/.+)($|/)",  # noqa: E501
                "--collector.netclass.ignored-devices=^(lxc|cilium_|qbr|qvb|qvo|tap|ovs-system|br|tbr|gre_sys).*$",
                "--collector.netdev.device-exclude=^(lxc|cilium_|qbr|qvb|qvo|tap|ovs-system|br|tbr|gre_sys).*$",
            ],
            "prometheus": {
                "monitor": {
                    "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_NODE_NAME
                }
            },
        },
        "additionalPrometheusRulesMap": utils.load_jsonnet_from_path(
            pkg_resources.resource_filename("atmosphere.jsonnet", "rules.jsonnet")
        ),
    },
    "values_from": [],
}
