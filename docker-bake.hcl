variable "REGISTRY" {
    default = "harbor.atmosphere.dev/library"
}

variable "TAG" {
    default = "main"
}

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
        "REQUIREMENTS_GIT_REPO" = "https://opendev.org/openstack/requirements.git"
        "REQUIREMENTS_GIT_REF" = "18098b9abacbd8d7257bebc1b302294f634441ab"
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
        "KUBERNETES_ENTRYPOINT_GIT_REPO" = "https://opendev.org/airship/kubernetes-entrypoint.git"
        "KUBERNETES_ENTRYPOINT_GIT_REF" = "4fbcf7ce324dc66e78480f73035e31434cfea1e8"
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
        "NETOFFLOAD_GIT_REPO" = "https://github.com/vexxhost/netoffload.git"
        "NETOFFLOAD_GIT_REF" = "94b8c0fdb0b83bd1b7e14b9a58077a047c78a800"
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
        OVN_KUBERNETES_REPO = "https://github.com/ovn-org/ovn-kubernetes.git"
        OVN_KUBERNETES_REF= "5359e7d7f872058b6e5bf884c9f19d1922451f29"
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
                git_repo = "https://opendev.org/openstack/barbican.git"
                git_ref = "ca57ef5436e20e90cf6cd6853efe3c89a9afd986"
            },
            {
                service = "cinder"
                git_repo = "https://opendev.org/openstack/cinder.git"
                git_ref = "b0f0b9015b9dfa228dff98eeee5116d8eca1c3cc"
            },
            {
                service = "designate"
                git_repo = "https://opendev.org/openstack/designate.git"
                git_ref = "097ffc6df181290eba1bcd7c492b1b505bc15434"
            },
            {
                service = "glance"
                git_repo = "https://opendev.org/openstack/glance.git"
                git_ref = "0bcd6cd71c09917c6734421374fd598d73e8d0cc"
                extra_args = {
                    "GLANCE_STORE_GIT_REPO" = "https://opendev.org/openstack/glance_store.git"
                    "GLANCE_STORE_GIT_REF" = "master"
                }
            },
            {
                service = "heat"
                git_repo = "https://opendev.org/openstack/heat.git"
                git_ref = "80eea85194825773d1b60ecc4386b2d5ba52a066"
            },
            {
                service = "horizon"
                git_repo = "https://opendev.org/openstack/horizon.git"
                git_ref = "14212342cf8f7eb987e50de112958af31063e02e"
                extra_args = {
                    "DESIGNATE_DASHBOARD_GIT_REPO" = "https://opendev.org/openstack/designate-dashboard.git"
                    "DESIGNATE_DASHBOARD_GIT_REF" = "master"
                    "HEAT_DASHBOARD_GIT_REPO" = "https://opendev.org/openstack/heat-dashboard.git"
                    "HEAT_DASHBOARD_GIT_REF" = "3070b2c8d5cc6e070df01233ec50b32ea987d92d"
                    "IRONIC_UI_GIT_REPO" = "https://opendev.org/openstack/ironic-ui.git"
                    "IRONIC_UI_GIT_REF" = "master"
                    "MAGNUM_UI_GIT_REPO" = "https://opendev.org/openstack/magnum-ui.git"
                    "MAGNUM_UI_GIT_REF" = "c9fdb537eaded73e81ea296d893e45d753337dc7"
                    "MANILA_UI_GIT_REPO" = "https://opendev.org/openstack/manila-ui.git"
                    "MANILA_UI_GIT_REF" = "master"
                    "NEUTRON_VPNAAS_DASHBOARD_GIT_REPO" = "https://opendev.org/openstack/neutron-vpnaas-dashboard.git"
                    "NEUTRON_VPNAAS_DASHBOARD_GIT_REF" = "master"
                    "OCTAVIA_DASHBOARD_GIT_REPO" = "https://opendev.org/openstack/octavia-dashboard.git"
                    "OCTAVIA_DASHBOARD_GIT_REF" = "master"
                }
            },
            {
                service = "ironic"
                git_repo = "https://opendev.org/openstack/ironic.git"
                git_ref = "22aa29b864eecd00bfb7c67cc2075030da1eb1d0"
            },
            {
                service = "keystone"
                git_repo = "https://opendev.org/openstack/keystone.git"
                git_ref = "8ca73f758bb613a57815fbe4ae78e3d2afa4af49"
            },
            {
                service = "magnum"
                git_repo = "https://opendev.org/openstack/magnum.git"
                git_ref = "c613ea4e419edc0086116da07e93cf19206746e1"
            },
            {
                service = "manila"
                git_repo = "https://opendev.org/openstack/manila.git"
                git_ref = "d8987589ae88ae9b2769fbe6f26d5b6994098038"
            },
            {
                service = "neutron"
                git_repo = "https://opendev.org/openstack/neutron.git"
                git_ref = "019294c71d94b788c14b23dc1da3c21f51bcdb0b"
                extra_args = {
                    "NEUTRON_VPNAAS_GIT_REPO" = "https://opendev.org/openstack/neutron-vpnaas.git"
                    "NEUTRON_VPNAAS_GIT_REF" = "7bc6d94305d34269d7522a9850c22aa42b50cdab"
                    "NETWORKING_BAREMETAL_GIT_REPO" = "https://opendev.org/openstack/networking-baremetal.git"
                    "NETWORKING_BAREMETAL_GIT_REF" = "8b92ad81c0bdbfde60a6f0c47ff0133c08bb617e"
                    "POLICY_SERVER_GIT_REPO" = "https://github.com/vexxhost/neutron-policy-server.git"
                    "POLICY_SERVER_GIT_REF" = "d87012b56741cb2ad44fa4dec9c5f24001ad60fe"
                    "LOG_PASER_GIT_REPO" = "https://github.com/vexxhost/neutron-ovn-network-logging-parser.git"
                    "LOG_PASER_GIT_REF" = "9bc923c1294864ec709c538ba5c309065ef710d5"
                }
            },
            {
                service = "nova"
                git_repo = "https://opendev.org/openstack/nova.git"
                git_ref = "c199becf52267ba37c5191f6f82e29bb5232b607"
                extra_args = {
                    "SCHEDULER_FILTERS_GIT_REPO" = "https://github.com/vexxhost/nova-scheduler-filters.git"
                    "SCHEDULER_FILTERS_GIT_REF" = "77ed1c2ca70f4166a6d0995c7d3d90822f0ca6c0"
                }
            },
            {
                service = "octavia"
                git_repo = "https://opendev.org/openstack/octavia.git"
                git_ref = "824b51a1dad80292b7a8ad5d61bf3ce706b1fb29"
                extra_args = {
                    "OVN_OCTAVIA_PROVIDER_GIT_REPO" = "https://opendev.org/openstack/ovn-octavia-provider.git"
                    "OVN_OCTAVIA_PROVIDER_GIT_REF" = "master"
                }
            },
            {
                service = "placement"
                git_repo = "https://opendev.org/openstack/placement.git"
                git_ref = "96a9aeb3b4a6ffff5bbf247b213409395239fc7a"
            },
            {
                service = "staffeln"
                git_repo = "https://github.com/vexxhost/staffeln.git"
                git_ref = "v2.2.3"
            },
            {
                service = "tempest"
                git_repo = "https://opendev.org/openstack/tempest.git"
                git_ref = "c0da6e843a74c2392c8e87e8ff36d2fea12949c4"
                extra_args = {
                    "BARBICAN_TEMPEST_PLUGIN_GIT_REPO" = "https://opendev.org/openstack/barbican-tempest-plugin.git"
                    "BARBICAN_TEMPEST_PLUGIN_GIT_REF" = "master"
                    "CINDER_TEMPEST_PLUGIN_GIT_REPO" = "https://opendev.org/openstack/cinder-tempest-plugin.git"
                    "CINDER_TEMPEST_PLUGIN_GIT_REF" = "master"
                    "HEAT_TEMPEST_PLUGIN_GIT_REPO" = "https://opendev.org/openstack/heat-tempest-plugin.git"
                    "HEAT_TEMPEST_PLUGIN_GIT_REF" = "master"
                    "KEYSTONE_TEMPEST_PLUGIN_GIT_REPO" = "https://opendev.org/openstack/keystone-tempest-plugin.git"
                    "KEYSTONE_TEMPEST_PLUGIN_GIT_REF" = "master"
                    "NEUTRON_TEMPEST_PLUGIN_GIT_REPO" = "https://opendev.org/openstack/neutron-tempest-plugin.git"
                    "NEUTRON_TEMPEST_PLUGIN_GIT_REF" = "master"
                    "OCTAVIA_TEMPEST_PLUGIN_GIT_REPO" = "https://opendev.org/openstack/octavia-tempest-plugin.git"
                    "OCTAVIA_TEMPEST_PLUGIN_GIT_REF" = "master"
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
