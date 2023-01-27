import pkg_resources

from atmosphere import utils

NODE_SELECTOR_CONTROL_PLANE = {
    "openstack-control-plane": "enabled",
}

NAMESPACE_CERT_MANAGER = "cert-manager"
NAMESPACE_MONITORING = "monitoring"

HELM_REPOSITORY_PROMETHEUS_COMMUINTY = "prometheus-community"
HELM_REPOSITORY_PROMETHEUS_COMMUINTY_URL = (
    "https://prometheus-community.github.io/helm-charts"
)

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

HELM_RELEASE_KUBE_PROMETHEUS_STACK_NAME = "kube-prometheus-stack"
HELM_RELEASE_KUBE_PROMETHEUS_STACK_VERSION = "41.7.3"
HELM_RELEASE_KUBE_PROMETHEUS_STACK_VALUES = {
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
            "image": {
                "repository": utils.get_image_ref_using_legacy_image_repository(
                    "alertmanager"
                )["name"],
                "tag": utils.get_image_ref_using_legacy_image_repository(
                    "alertmanager"
                )["tag"],
            },
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
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository("grafana")[
                "name"
            ],
            "tag": utils.get_image_ref_using_legacy_image_repository("grafana")["tag"],
        },
        "sidecar": {
            "image": {
                "repository": utils.get_image_ref_using_legacy_image_repository(
                    "grafana_sidecar"
                )["name"],
                "tag": utils.get_image_ref_using_legacy_image_repository(
                    "grafana_sidecar"
                )["tag"],
            }
        },
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
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "kube_state_metrics"
            )["name"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "kube_state_metrics"
            )["tag"],
        },
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
            "image": {
                "repository": utils.get_image_ref_using_legacy_image_repository(
                    "prometheus"
                )["name"],
                "tag": utils.get_image_ref_using_legacy_image_repository("prometheus")[
                    "tag"
                ],
            },
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
        "admissionWebhooks": {
            "patch": {
                "image": {
                    "repository": utils.get_image_ref_using_legacy_image_repository(
                        "prometheus_operator_kube_webhook_certgen"
                    )["name"],
                    "tag": utils.get_image_ref_using_legacy_image_repository(
                        "prometheus_operator_kube_webhook_certgen"
                    )["tag"],
                },
                "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
            }
        },
        "serviceMonitor": {
            "relabelings": PROMETHEUS_MONITOR_RELABELINGS_INSTANCE_TO_POD_NAME
        },
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "prometheus_operator"
            )["name"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "prometheus_operator"
            )["tag"],
        },
        "prometheusConfigReloader": {
            "image": {
                "repository": utils.get_image_ref_using_legacy_image_repository(
                    "prometheus_config_reloader"
                )["name"],
                "tag": utils.get_image_ref_using_legacy_image_repository(
                    "prometheus_config_reloader"
                )["tag"],
            }
        },
    },
    "prometheus-node-exporter": {
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "prometheus_node_exporter"
            )["name"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "prometheus_node_exporter"
            )["tag"],
        },
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
}
