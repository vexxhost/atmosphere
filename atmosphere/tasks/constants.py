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
HELM_REPOSITORY_JETSTACK = "jetstack"
HELM_REPOSITORY_NODE_FEATURE_DISCOVERY = "node-feature-discovery"
HELM_REPOSITORY_OPENSTACK_HELM = "openstack-helm"
HELM_REPOSITORY_OPENSTACK_HELM_INFRA = "openstack-helm-infra"
HELM_REPOSITORY_PERCONA = "percona"
HELM_REPOSITORY_PROMETHEUS_COMMUINTY = "prometheus-community"

HELM_RELEASE_INGRESS_NGINX_NAME = "ingress-nginx"
HELM_RELEASE_INGRESS_NGINX_VERSION = "4.0.17"
HELM_RELEASE_INGRESS_NGINX_VALUES = {
    "controller": {
        "config": {"proxy-buffer-size": "16k"},
        "dnsPolicy": "ClusterFirstWithHostNet",
        "hostNetwork": True,
        "ingressClassResource": {"name": "openstack"},
        "ingressClass": "openstack",
        "extraArgs": {"default-ssl-certificate": "ingress-nginx/wildcard"},
        "kind": "DaemonSet",
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
        "service": {"type": "ClusterIP"},
        "admissionWebhooks": {"port": 7443},
    },
    "defaultBackend": {"enabled": True},
}

HELM_RELEASE_CERT_MANAGER_NAME = "cert-manager"
HELM_RELEASE_CERT_MANAGER_VERSION = "v1.7.1"
HELM_RELEASE_CERT_MANAGER_VALUES = {
    "installCRDs": True,
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
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
    },
    "cainjector": {
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
    },
    "startupapicheck": {
        "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
    },
}

HELM_RELEASE_NODE_FEATURE_DISCOVERY_VALUES = {
    "master": {"nodeSelector": NODE_SELECTOR_CONTROL_PLANE}
}

HELM_RELEASE_RABBITMQ_OPERATOR_NAME = "rabbitmq-cluster-operator"
HELM_RELEASE_RABBITMQ_OPERATOR_VERSION = "2.5.2"
HELM_RELEASE_RABBITMQ_OPERATOR_VALUES = {
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
}
HELM_RELEASE_RABBITMQ_OPERATOR_REQUIRES = set(
    [
        f"helm-release-{NAMESPACE_CERT_MANAGER}-{HELM_RELEASE_CERT_MANAGER_NAME}",
    ]
)

HELM_RELEASE_PXC_OPERATOR_NAME = "pxc-operator"
HELM_RELEASE_PXC_OPERATOR_VERSION = "1.10.0"
HELM_RELEASE_PXC_OPERATOR_VALUES = {
    "nodeSelector": NODE_SELECTOR_CONTROL_PLANE,
}

HELM_RELEASE_KEYSTONE_NAME = "keystone"

HELM_RELEASE_BARBICAN_NAME = "barbican"

HELM_RELEASE_GLANCE_NAME = "glance"

HELM_RELEASE_CINDER_NAME = "cinder"

HELM_RELEASE_NEUTRON_NAME = "neutron"

HELM_RELEASE_NOVA_NAME = "nova"

HELM_RELEASE_SENLIN_NAME = "senlin"

HELM_RELEASE_HEAT_NAME = "heat"
