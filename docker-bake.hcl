variable "REGISTRY" {
    default = "harbor.atmosphere.dev/library"
}

variable "TAG" {
    default = "main"
}

variable "REQUIREMENTS_GIT_REPO" {
  default = "https://opendev.org/openstack/requirements.git"
}

variable "REQUIREMENTS_GIT_REF" {
  default = "18098b9abacbd8d7257bebc1b302294f634441ab"
}

variable "KUBERNETES_ENTRYPOINT_GIT_REPO" {
  default = "https://opendev.org/airship/kubernetes-entrypoint.git"
}

variable "KUBERNETES_ENTRYPOINT_GIT_REF" {
  default = "4fbcf7ce324dc66e78480f73035e31434cfea1e8"
}

variable "NETOFFLOAD_GIT_REPO" {
  default = "https://github.com/vexxhost/netoffload.git"
}

variable "NETOFFLOAD_GIT_REF" {
  default = "94b8c0fdb0b83bd1b7e14b9a58077a047c78a800"
}

variable "OVN_KUBERNETES_REPO" {
  default = "https://github.com/ovn-org/ovn-kubernetes.git"
}

variable "OVN_KUBERNETES_REF" {
  default = "5359e7d7f872058b6e5bf884c9f19d1922451f29"
}

# --- OpenStack Service Variables ---
variable "BARBICAN_GIT_REPO" { default = "https://opendev.org/openstack/barbican.git" }
variable "BARBICAN_GIT_REF" { default = "ca57ef5436e20e90cf6cd6853efe3c89a9afd986" }
variable "CINDER_GIT_REPO" { default = "https://opendev.org/openstack/cinder.git" }
variable "CINDER_GIT_REF" { default = "b0f0b9015b9dfa228dff98eeee5116d8eca1c3cc" }
variable "DESIGNATE_GIT_REPO" { default = "https://opendev.org/openstack/designate.git" }
variable "DESIGNATE_GIT_REF" { default = "097ffc6df181290eba1bcd7c492b1b505bc15434" }
variable "GLANCE_GIT_REPO" { default = "https://opendev.org/openstack/glance.git" }
variable "GLANCE_GIT_REF" { default = "0bcd6cd71c09917c6734421374fd598d73e8d0cc" }
variable "GLANCE_STORE_GIT_REPO" { default = "https://opendev.org/openstack/glance_store.git" }
variable "GLANCE_STORE_GIT_REF" { default = "master" }
variable "HEAT_GIT_REPO" { default = "https://opendev.org/openstack/heat.git" }
variable "HEAT_GIT_REF" { default = "80eea85194825773d1b60ecc4386b2d5ba52a066" }
variable "HORIZON_GIT_REPO" { default = "https://opendev.org/openstack/horizon.git" }
variable "HORIZON_GIT_REF" { default = "14212342cf8f7eb987e50de112958af31063e02e" }
variable "DESIGNATE_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/designate-dashboard.git" }
variable "DESIGNATE_DASHBOARD_GIT_REF" { default = "master" }
variable "HEAT_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/heat-dashboard.git" }
variable "HEAT_DASHBOARD_GIT_REF" { default = "3070b2c8d5cc6e070df01233ec50b32ea987d92d" }
variable "IRONIC_UI_GIT_REPO" { default = "https://opendev.org/openstack/ironic-ui.git" }
variable "IRONIC_UI_GIT_REF" { default = "master" }
variable "MAGNUM_UI_GIT_REPO" { default = "https://opendev.org/openstack/magnum-ui.git" }
variable "MAGNUM_UI_GIT_REF" { default = "c9fdb537eaded73e81ea296d893e45d753337dc7" }
variable "MANILA_UI_GIT_REPO" { default = "https://opendev.org/openstack/manila-ui.git" }
variable "MANILA_UI_GIT_REF" { default = "master" }
variable "NEUTRON_VPNAAS_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/neutron-vpnaas-dashboard.git" }
variable "NEUTRON_VPNAAS_DASHBOARD_GIT_REF" { default = "master" }
variable "OCTAVIA_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/octavia-dashboard.git" }
variable "OCTAVIA_DASHBOARD_GIT_REF" { default = "master" }
variable "IRONIC_GIT_REPO" { default = "https://opendev.org/openstack/ironic.git" }
variable "IRONIC_GIT_REF" { default = "22aa29b864eecd00bfb7c67cc2075030da1eb1d0" }
variable "KEYSTONE_GIT_REPO" { default = "https://opendev.org/openstack/keystone.git" }
variable "KEYSTONE_GIT_REF" { default = "8ca73f758bb613a57815fbe4ae78e3d2afa4af49" }
variable "MAGNUM_GIT_REPO" { default = "https://opendev.org/openstack/magnum.git" }
variable "MAGNUM_GIT_REF" { default = "c613ea4e419edc0086116da07e93cf19206746e1" }
variable "MANILA_GIT_REPO" { default = "https://opendev.org/openstack/manila.git" }
variable "MANILA_GIT_REF" { default = "d8987589ae88ae9b2769fbe6f26d5b6994098038" }
variable "NEUTRON_GIT_REPO" { default = "https://opendev.org/openstack/neutron.git" }
variable "NEUTRON_GIT_REF" { default = "019294c71d94b788c14b23dc1da3c21f51bcdb0b" }
variable "NEUTRON_VPNAAS_GIT_REPO" { default = "https://opendev.org/openstack/neutron-vpnaas.git" }
variable "NEUTRON_VPNAAS_GIT_REF" { default = "7bc6d94305d34269d7522a9850c22aa42b50cdab" }
variable "NETWORKING_BAREMETAL_GIT_REPO" { default = "https://opendev.org/openstack/networking-baremetal.git" }
variable "NETWORKING_BAREMETAL_GIT_REF" { default = "8b92ad81c0bdbfde60a6f0c47ff0133c08bb617e" }
variable "POLICY_SERVER_GIT_REPO" { default = "https://github.com/vexxhost/neutron-policy-server.git" }
variable "POLICY_SERVER_GIT_REF" { default = "d87012b56741cb2ad44fa4dec9c5f24001ad60fe" }
variable "LOG_PARSER_GIT_REPO" { default = "https://github.com/vexxhost/neutron-ovn-network-logging-parser.git" }
variable "LOG_PARSER_GIT_REF" { default = "9bc923c1294864ec709c538ba5c309065ef710d5" }
variable "NOVA_GIT_REPO" { default = "https://opendev.org/openstack/nova.git" }
variable "NOVA_GIT_REF" { default = "c199becf52267ba37c5191f6f82e29bb5232b607" }
variable "SCHEDULER_FILTERS_GIT_REPO" { default = "https://github.com/vexxhost/nova-scheduler-filters.git" }
variable "SCHEDULER_FILTERS_GIT_REF" { default = "77ed1c2ca70f4166a6d0995c7d3d90822f0ca6c0" }
variable "OCTAVIA_GIT_REPO" { default = "https://opendev.org/openstack/octavia.git" }
variable "OCTAVIA_GIT_REF" { default = "824b51a1dad80292b7a8ad5d61bf3ce706b1fb29" }
variable "OVN_OCTAVIA_PROVIDER_GIT_REPO" { default = "https://opendev.org/openstack/ovn-octavia-provider.git" }
variable "OVN_OCTAVIA_PROVIDER_GIT_REF" { default = "master" }
variable "PLACEMENT_GIT_REPO" { default = "https://opendev.org/openstack/placement.git" }
variable "PLACEMENT_GIT_REF" { default = "96a9aeb3b4a6ffff5bbf247b213409395239fc7a" }
variable "STAFFELN_GIT_REPO" { default = "https://github.com/vexxhost/staffeln.git" }
variable "STAFFELN_GIT_REF" { default = "v2.2.3" }
variable "TEMPEST_GIT_REPO" { default = "https://opendev.org/openstack/tempest.git" }
variable "TEMPEST_GIT_REF" { default = "c0da6e843a74c2392c8e87e8ff36d2fea12949c4" }
variable "BARBICAN_TEMPEST_PLUGIN_GIT_REPO" { default = "https://opendev.org/openstack/barbican-tempest-plugin.git" }
variable "BARBICAN_TEMPEST_PLUGIN_GIT_REF" { default = "master" }
variable "CINDER_TEMPEST_PLUGIN_GIT_REPO" { default = "https://opendev.org/openstack/cinder-tempest-plugin.git" }
variable "CINDER_TEMPEST_PLUGIN_GIT_REF" { default = "master" }
variable "HEAT_TEMPEST_PLUGIN_GIT_REPO" { default = "https://opendev.org/openstack/heat-tempest-plugin.git" }
variable "HEAT_TEMPEST_PLUGIN_GIT_REF" { default = "master" }
variable "KEYSTONE_TEMPEST_PLUGIN_GIT_REPO" { default = "https://opendev.org/openstack/keystone-tempest-plugin.git" }
variable "KEYSTONE_TEMPEST_PLUGIN_GIT_REF" { default = "master" }
variable "NEUTRON_TEMPEST_PLUGIN_GIT_REPO" { default = "https://opendev.org/openstack/neutron-tempest-plugin.git" }
variable "NEUTRON_TEMPEST_PLUGIN_GIT_REF" { default = "master" }
variable "OCTAVIA_TEMPEST_PLUGIN_GIT_REPO" { default = "https://opendev.org/openstack/octavia-tempest-plugin.git" }
variable "OCTAVIA_TEMPEST_PLUGIN_GIT_REF" { default = "master" }

target "ubuntu" {
    context = "images/ubuntu"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "ubuntu" = "docker-image://docker.io/library/ubuntu:jammy-20240227"
    }
}

target "ubuntu-cloud-archive" {
    context = "images/ubuntu-cloud-archive"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "ubuntu" = "target:ubuntu"
    }
}

target "python-base" {
    context = "images/python-base"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "ubuntu-cloud-archive" = "target:ubuntu-cloud-archive"
    }
}

target "openstack-venv-builder" {
    context = "images/openstack-venv-builder"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "ubuntu-cloud-archive" = "target:ubuntu-cloud-archive"
        "python-base" = "target:python-base"
    }

    args = {
        "REQUIREMENTS_GIT_REPO" = "${REQUIREMENTS_GIT_REPO}"
        "REQUIREMENTS_GIT_REF" = "${REQUIREMENTS_GIT_REF}"
    }
}

target "openstack-runtime" {
    context = "images/openstack-runtime"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "base" = "target:ubuntu-cloud-archive"
    }
}

target "openstack-python-runtime" {
    context = "images/openstack-runtime"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "base" = "target:python-base"
    }
}

target "keepalived" {
    context = "images/keepalived"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "ubuntu" = "target:ubuntu"
    }

    tags = [
        "${REGISTRY}/keepalived:${TAG}"
    ]
}

target "kubernetes-entrypoint" {
    context = "images/kubernetes-entrypoint"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "golang" = "docker-image://docker.io/library/golang:1.21"
    }

    args = {
        "KUBERNETES_ENTRYPOINT_GIT_REPO" = "${KUBERNETES_ENTRYPOINT_GIT_REPO}"
        "KUBERNETES_ENTRYPOINT_GIT_REF" = "${KUBERNETES_ENTRYPOINT_GIT_REF}"
    }

    tags = [
        "${REGISTRY}/kubernetes-entrypoint:${TAG}"
    ]
}

target "libvirtd" {
    context = "images/libvirtd"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "openstack-runtime" = "target:openstack-runtime"
    }

    args = {
        PROJECT = "nova"
    }

    tags = [
        "${REGISTRY}/libvirtd:${TAG}"
    ]
}

target "netoffload" {
    context = "images/netoffload"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "golang" = "docker-image://docker.io/library/golang:1.20"
        "ubuntu" = "target:ubuntu"
    }

    args = {
        "NETOFFLOAD_GIT_REPO" = "${NETOFFLOAD_GIT_REPO}"
        "NETOFFLOAD_GIT_REF" = "${NETOFFLOAD_GIT_REF}"
    }

    tags = [
        "${REGISTRY}/netoffload:${TAG}"
    ]
}

target "nova-ssh" {
    context = "images/nova-ssh"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "openstack-runtime" = "target:openstack-runtime"
    }

    args = {
        PROJECT = "nova"
    }

    tags = [
        "${REGISTRY}/nova-ssh:${TAG}"
    ]
}

target "openvswitch" {
    context = "images/openvswitch"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "centos" = "docker-image://quay.io/centos/centos:stream9"
    }

    tags = [
        "${REGISTRY}/openvswitch:${TAG}"
    ]
}

target "ovn" {
    name = "ovn-${component}"
    matrix = {
        component = ["host", "central"]
    }

    context = "images/ovn"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "golang" = "docker-image://docker.io/library/golang:1.20"
        "openvswitch" = "target:openvswitch"
    }

    args = {
        OVN_COMPONENT = "${component}"
        OVN_KUBERNETES_REPO = "${OVN_KUBERNETES_REPO}"
        OVN_KUBERNETES_REF= "${OVN_KUBERNETES_REF}"
    }

    tags = [
        "${REGISTRY}/ovn-${component}:${TAG}"
    ]
}

target "python-openstackclient" {
    context = "images/python-openstackclient"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "openstack-venv-builder" = "target:openstack-venv-builder"
        "python-base" = "target:python-base"
    }

    tags = [
        "${REGISTRY}/python-openstackclient:${TAG}"
    ]
}

target "openstack" {
    name = "openstack-${item.service}"
    matrix = {
        item = [
            {
                service = "barbican"
                git_repo = "${BARBICAN_GIT_REPO}"
                git_ref = "${BARBICAN_GIT_REF}"
            },
            {
                service = "cinder"
                git_repo = "${CINDER_GIT_REPO}"
                git_ref = "${CINDER_GIT_REF}"
            },
            {
                service = "designate"
                git_repo = "${DESIGNATE_GIT_REPO}"
                git_ref = "${DESIGNATE_GIT_REF}"
            },
            {
                service = "glance"
                git_repo = "${GLANCE_GIT_REPO}"
                git_ref = "${GLANCE_GIT_REF}"
                extra_args = {
                    "GLANCE_STORE_GIT_REPO" = "${GLANCE_STORE_GIT_REPO}"
                    "GLANCE_STORE_GIT_REF" = "${GLANCE_STORE_GIT_REF}"
                }
            },
            {
                service = "heat"
                git_repo = "${HEAT_GIT_REPO}"
                git_ref = "${HEAT_GIT_REF}"
            },
            {
                service = "horizon"
                git_repo = "${HORIZON_GIT_REPO}"
                git_ref = "${HORIZON_GIT_REF}"
                extra_args = {
                    "DESIGNATE_DASHBOARD_GIT_REPO" = "${DESIGNATE_DASHBOARD_GIT_REPO}"
                    "DESIGNATE_DASHBOARD_GIT_REF" = "${DESIGNATE_DASHBOARD_GIT_REF}"
                    "HEAT_DASHBOARD_GIT_REPO" = "${HEAT_DASHBOARD_GIT_REPO}"
                    "HEAT_DASHBOARD_GIT_REF" = "${HEAT_DASHBOARD_GIT_REF}"
                    "IRONIC_UI_GIT_REPO" = "${IRONIC_UI_GIT_REPO}"
                    "IRONIC_UI_GIT_REF" = "${IRONIC_UI_GIT_REF}"
                    "MAGNUM_UI_GIT_REPO" = "${MAGNUM_UI_GIT_REPO}"
                    "MAGNUM_UI_GIT_REF" = "${MAGNUM_UI_GIT_REF}"
                    "MANILA_UI_GIT_REPO" = "${MANILA_UI_GIT_REPO}"
                    "MANILA_UI_GIT_REF" = "${MANILA_UI_GIT_REF}"
                    "NEUTRON_VPNAAS_DASHBOARD_GIT_REPO" = "${NEUTRON_VPNAAS_DASHBOARD_GIT_REPO}"
                    "NEUTRON_VPNAAS_DASHBOARD_GIT_REF" = "${NEUTRON_VPNAAS_DASHBOARD_GIT_REF}"
                    "OCTAVIA_DASHBOARD_GIT_REPO" = "${OCTAVIA_DASHBOARD_GIT_REPO}"
                    "OCTAVIA_DASHBOARD_GIT_REF" = "${OCTAVIA_DASHBOARD_GIT_REF}"
                }
            },
            {
                service = "ironic"
                git_repo = "${IRONIC_GIT_REPO}"
                git_ref = "${IRONIC_GIT_REF}"
            },
            {
                service = "keystone"
                git_repo = "${KEYSTONE_GIT_REPO}"
                git_ref = "${KEYSTONE_GIT_REF}"
            },
            {
                service = "magnum"
                git_repo = "${MAGNUM_GIT_REPO}"
                git_ref = "${MAGNUM_GIT_REF}"
            },
            {
                service = "manila"
                git_repo = "${MANILA_GIT_REPO}"
                git_ref = "${MANILA_GIT_REF}"
            },
            {
                service = "neutron"
                git_repo = "${NEUTRON_GIT_REPO}"
                git_ref = "${NEUTRON_GIT_REF}"
                extra_args = {
                    "NEUTRON_VPNAAS_GIT_REPO" = "${NEUTRON_VPNAAS_GIT_REPO}"
                    "NEUTRON_VPNAAS_GIT_REF" = "${NEUTRON_VPNAAS_GIT_REF}"
                    "NETWORKING_BAREMETAL_GIT_REPO" = "${NETWORKING_BAREMETAL_GIT_REPO}"
                    "NETWORKING_BAREMETAL_GIT_REF" = "${NETWORKING_BAREMETAL_GIT_REF}"
                    "POLICY_SERVER_GIT_REPO" = "${POLICY_SERVER_GIT_REPO}"
                    "POLICY_SERVER_GIT_REF" = "${POLICY_SERVER_GIT_REF}"
                    "LOG_PARSER_GIT_REPO" = "${LOG_PARSER_GIT_REPO}"
                    "LOG_PARSER_GIT_REF" = "${LOG_PARSER_GIT_REF}"
                }
            },
            {
                service = "nova"
                git_repo = "${NOVA_GIT_REPO}"
                git_ref = "${NOVA_GIT_REF}"
                extra_args = {
                    "SCHEDULER_FILTERS_GIT_REPO" = "${SCHEDULER_FILTERS_GIT_REPO}"
                    "SCHEDULER_FILTERS_GIT_REF" = "${SCHEDULER_FILTERS_GIT_REF}"
                }
            },
            {
                service = "octavia"
                git_repo = "${OCTAVIA_GIT_REPO}"
                git_ref = "${OCTAVIA_GIT_REF}"
                extra_args = {
                    "OVN_OCTAVIA_PROVIDER_GIT_REPO" = "${OVN_OCTAVIA_PROVIDER_GIT_REPO}"
                    "OVN_OCTAVIA_PROVIDER_GIT_REF" = "${OVN_OCTAVIA_PROVIDER_GIT_REF}"
                }
            },
            {
                service = "placement"
                git_repo = "${PLACEMENT_GIT_REPO}"
                git_ref = "${PLACEMENT_GIT_REF}"
            },
            {
                service = "staffeln"
                git_repo = "${STAFFELN_GIT_REPO}"
                git_ref = "${STAFFELN_GIT_REF}"
            },
            {
                service = "tempest"
                git_repo = "${TEMPEST_GIT_REPO}"
                git_ref = "${TEMPEST_GIT_REF}"
                extra_args = {
                    "BARBICAN_TEMPEST_PLUGIN_GIT_REPO" = "${BARBICAN_TEMPEST_PLUGIN_GIT_REPO}"
                    "BARBICAN_TEMPEST_PLUGIN_GIT_REF" = "${BARBICAN_TEMPEST_PLUGIN_GIT_REF}"
                    "CINDER_TEMPEST_PLUGIN_GIT_REPO" = "${CINDER_TEMPEST_PLUGIN_GIT_REPO}"
                    "CINDER_TEMPEST_PLUGIN_GIT_REF" = "${CINDER_TEMPEST_PLUGIN_GIT_REF}"
                    "HEAT_TEMPEST_PLUGIN_GIT_REPO" = "${HEAT_TEMPEST_PLUGIN_GIT_REPO}"
                    "HEAT_TEMPEST_PLUGIN_GIT_REF" = "${HEAT_TEMPEST_PLUGIN_GIT_REF}"
                    "KEYSTONE_TEMPEST_PLUGIN_GIT_REPO" = "${KEYSTONE_TEMPEST_PLUGIN_GIT_REPO}"
                    "KEYSTONE_TEMPEST_PLUGIN_GIT_REF" = "${KEYSTONE_TEMPEST_PLUGIN_GIT_REF}"
                    "NEUTRON_TEMPEST_PLUGIN_GIT_REPO" = "${NEUTRON_TEMPEST_PLUGIN_GIT_REPO}"
                    "NEUTRON_TEMPEST_PLUGIN_GIT_REF" = "${NEUTRON_TEMPEST_PLUGIN_GIT_REF}"
                    "OCTAVIA_TEMPEST_PLUGIN_GIT_REPO" = "${OCTAVIA_TEMPEST_PLUGIN_GIT_REPO}"
                    "OCTAVIA_TEMPEST_PLUGIN_GIT_REF" = "${OCTAVIA_TEMPEST_PLUGIN_GIT_REF}"
                }
            }
        ]
    }

    context = "images/${item.service}"
    platforms = ["linux/amd64", "linux/arm64"]

    args = merge(
        {
            PROJECT = "${item.service}"
            "${item.service}_GIT_REPO" = "${item.git_repo}"
            "${item.service}_GIT_REF" = "${item.git_ref}"
        },
        try(item.extra_args, {})
    )

    contexts = {
        "openstack-venv-builder" = "target:openstack-venv-builder"
        "openstack-python-runtime" = "target:openstack-python-runtime"
    }

    tags = [
        "${REGISTRY}/${item.service}:${TAG}"
    ]
}

group "default" {
    targets = [
        "keepalived",
        "kubernetes-entrypoint",
        "libvirtd",
        "netoffload",
        "nova-ssh",
        "openstack-barbican",
        "openstack-cinder",
        "openstack-designate",
        "openstack-glance",
        "openstack-heat",
        "openstack-horizon",
        "openstack-ironic",
        "openstack-keystone",
        "openstack-magnum",
        "openstack-manila",
        "openstack-neutron",
        "openstack-nova",
        "openstack-octavia",
        "openstack-placement",
        "openstack-staffeln",
        "openstack-tempest",
        "openvswitch",
        "ovn-central",
        "ovn-host",
        "python-openstackclient",
    ]
}
