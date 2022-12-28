import pkg_resources

from atmosphere import utils

NODE_SELECTOR_CONTROL_PLANE = {
    "openstack-control-plane": "enabled",
}

NAMESPACE_CERT_MANAGER = "cert-manager"
NAMESPACE_KUBE_SYSTEM = "kube-system"
NAMESPACE_MONITORING = "monitoring"
NAMESPACE_OPENSTACK = "openstack"

HELM_REPOSITORY_BITNAMI = "bitnami"
HELM_REPOSITORY_CEPH = "ceph"
HELM_REPOSITORY_COREDNS = "coredns"

HELM_REPOSITORY_INGRESS_NGINX = "ingress-nginx"
HELM_REPOSITORY_INGRESS_NGINX_URL = "https://kubernetes.github.io/ingress-nginx"

HELM_REPOSITORY_JETSTACK = "jetstack"
HELM_REPOSITORY_NODE_FEATURE_DISCOVERY = "node-feature-discovery"
HELM_REPOSITORY_OPENSTACK_HELM = "openstack-helm"
HELM_REPOSITORY_OPENSTACK_HELM_INFRA = "openstack-helm-infra"
HELM_REPOSITORY_PERCONA = "percona"

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

HELM_RELEASE_INGRESS_NGINX_NAME = "ingress-nginx"
HELM_RELEASE_INGRESS_NGINX_VERSION = "4.0.17"
HELM_RELEASE_INGRESS_NGINX_VALUES = {
    "controller": {
        "image": {
            "registry": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_controller"
            ).repository["domain"],
            "image": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_controller"
            ).repository["path"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_controller"
            )["tag"],
            "digest": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_controller"
            )["digest"],
        },
        "config": {"proxy-buffer-size": "16k"},
        "dnsPolicy": "ClusterFirstWithHostNet",
        "hostNetwork": True,
        "ingressClassResource": {"name": "openstack"},
        "ingressClass": "openstack",
        "kind": "DaemonSet",
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "service": {"type": "ClusterIP"},
        "admissionWebhooks": {
            "port": 7443,
            "patch": {
                "image": {
                    "registry": utils.get_image_ref_using_legacy_image_repository(
                        "ingress_nginx_kube_webhook_certgen"
                    ).repository["domain"],
                    "image": utils.get_image_ref_using_legacy_image_repository(
                        "ingress_nginx_kube_webhook_certgen"
                    ).repository["path"],
                    "tag": utils.get_image_ref_using_legacy_image_repository(
                        "ingress_nginx_kube_webhook_certgen"
                    )["tag"],
                    "digest": utils.get_image_ref_using_legacy_image_repository(
                        "ingress_nginx_kube_webhook_certgen"
                    )["digest"],
                }
            },
        },
    },
    "defaultBackend": {
        "enabled": True,
        "image": {
            "registry": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_default_backend"
            ).repository["domain"],
            "image": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_default_backend"
            ).repository["path"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "ingress_nginx_default_backend"
            )["tag"],
        },
    },
    "tcp": {
        "5354": "openstack/minidns:5354",
    },
    "udp": {
        "5354": "openstack/minidns:5354",
    },
}

HELM_RELEASE_CERT_MANAGER_NAME = "cert-manager"
HELM_RELEASE_CERT_MANAGER_VERSION = "v1.7.1"
HELM_RELEASE_CERT_MANAGER_VALUES = {
    "installCRDs": True,
    "featureGates": "AdditionalCertificateOutputFormats=true",
    "image": {
        "repository": utils.get_image_ref_using_legacy_image_repository(
            "cert_manager_controller"
        )["name"],
        "tag": utils.get_image_ref_using_legacy_image_repository(
            "cert_manager_controller"
        )["tag"],
    },
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
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "cert_manager_webhook"
            )["name"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "cert_manager_webhook"
            )["tag"],
        },
    },
    "cainjector": {
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "cert_manager_cainjector"
            )["name"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "cert_manager_cainjector"
            )["tag"],
        },
    },
    "startupapicheck": {
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "cert_manager_cli"
            )["name"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "cert_manager_cli"
            )["tag"],
        },
    },
}

HELM_RELEASE_NODE_FEATURE_DISCOVERY_VALUES = {
    "image": {
        "repository": utils.get_image_ref_using_legacy_image_repository(
            "node_feature_discovery"
        )["name"]
    },
    "master": {"nodeSelector": NODE_SELECTOR_CONTROL_PLANE},
}

HELM_RELEASE_RABBITMQ_OPERATOR_NAME = "rabbitmq-cluster-operator"
HELM_RELEASE_RABBITMQ_OPERATOR_VERSION = "2.6.6"
HELM_RELEASE_RABBITMQ_OPERATOR_VALUES = {
    "global": {
        "imageRegistry": utils.get_image_ref_using_legacy_image_repository(
            "rabbitmq_cluster_operator"
        ).repository["domain"],
    },
    "rabbitmqImage": {
        "repository": utils.get_image_ref_using_legacy_image_repository(
            "rabbitmq_server"
        ).repository["path"],
        "tag": utils.get_image_ref_using_legacy_image_repository("rabbitmq_server")[
            "tag"
        ],
    },
    "credentialUpdaterImage": {
        "repository": utils.get_image_ref_using_legacy_image_repository(
            "rabbitmq_credential_updater"
        ).repository["path"],
        "tag": utils.get_image_ref_using_legacy_image_repository(
            "rabbitmq_credential_updater"
        )["tag"],
    },
    "clusterOperator": {
        "fullnameOverride": "rabbitmq-cluster-operator",
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "rabbitmq_cluster_operator"
            ).repository["path"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "rabbitmq_cluster_operator"
            )["tag"],
        },
    },
    "msgTopologyOperator": {
        "fullnameOverride": "rabbitmq-messaging-topology-operator",
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "image": {
            "repository": utils.get_image_ref_using_legacy_image_repository(
                "rabbitmq_topology_operator"
            ).repository["path"],
            "tag": utils.get_image_ref_using_legacy_image_repository(
                "rabbitmq_topology_operator"
            )["tag"],
        },
    },
    "useCertManager": True,
}
HELM_RELEASE_RABBITMQ_OPERATOR_REQUIRES = set(
    [
        f"helm-release-{NAMESPACE_CERT_MANAGER}-{HELM_RELEASE_CERT_MANAGER_NAME}",
    ]
)

HELM_RELEASE_PXC_OPERATOR_NAME = "pxc-operator"
HELM_RELEASE_PXC_OPERATOR_VERSION = "1.10.0"
HELM_RELEASE_PXC_OPERATOR_VALUES = {
    "image": utils.get_image_ref_using_legacy_image_repository(
        "percona_xtradb_cluster_operator"
    ).string(),
    "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
}

HELM_RELEASE_KEYSTONE_NAME = "keystone"

HELM_RELEASE_BARBICAN_NAME = "barbican"

HELM_RELEASE_GLANCE_NAME = "glance"

HELM_RELEASE_CINDER_NAME = "cinder"

HELM_RELEASE_NEUTRON_NAME = "neutron"

HELM_RELEASE_NOVA_NAME = "nova"

HELM_RELEASE_OCTAVIA_NAME = "octavia"

HELM_RELEASE_SENLIN_NAME = "senlin"

HELM_RELEASE_DESIGNATE_NAME = "designate"

HELM_RELEASE_HEAT_NAME = "heat"
