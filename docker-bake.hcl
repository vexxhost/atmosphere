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
  default = "d620ff557c22c4b8c1398b6dc84772c341fb4d5a"
}

variable "KUBERNETES_ENTRYPOINT_GIT_REPO" {
  default = "https://opendev.org/airship/kubernetes-entrypoint.git"
}

variable "KUBERNETES_ENTRYPOINT_GIT_REF" {
  default = "df2f40f3dec3aca3e648f4f351ff5ccfbd659b59"
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
variable "BARBICAN_GIT_REF" { default = "b5841df387e5ab38caf173950a1d98ab37a51453" }
variable "CINDER_GIT_REPO" { default = "https://opendev.org/openstack/cinder.git" }
variable "CINDER_GIT_REF" { default = "9d1a7de850ad06e9f8e242ecfeb070da22c688c4" }
variable "DESIGNATE_GIT_REPO" { default = "https://opendev.org/openstack/designate.git" }
variable "DESIGNATE_GIT_REF" { default = "505ea9b1245e07b28e12c1be3ca5d5e86d77efaf" }
variable "GLANCE_GIT_REPO" { default = "https://opendev.org/openstack/glance.git" }
variable "GLANCE_GIT_REF" { default = "d1cc917a29c9d2e87b1bad51a33a8a2500eb69c6" }
variable "GLANCE_STORE_GIT_REPO" { default = "https://opendev.org/openstack/glance_store.git" }
variable "GLANCE_STORE_GIT_REF" { default = "stable/2024.2" }
variable "HEAT_GIT_REPO" { default = "https://opendev.org/openstack/heat.git" }
variable "HEAT_GIT_REF" { default = "64bdbb9bc66c38760989dd7bb2574ccc14069872" }
variable "HORIZON_GIT_REPO" { default = "https://opendev.org/openstack/horizon.git" }
variable "HORIZON_GIT_REF" { default = "23d0b9525f7c11288d503123e29db0bd66f9ca88" }
variable "DESIGNATE_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/designate-dashboard.git" }
variable "DESIGNATE_DASHBOARD_GIT_REF" { default = "stable/2024.2" }
variable "HEAT_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/heat-dashboard.git" }
variable "HEAT_DASHBOARD_GIT_REF" { default = "stable/2024.2" }
variable "IRONIC_UI_GIT_REPO" { default = "https://opendev.org/openstack/ironic-ui.git" }
variable "IRONIC_UI_GIT_REF" { default = "stable/2024.2" }
variable "MAGNUM_UI_GIT_REPO" { default = "https://opendev.org/openstack/magnum-ui.git" }
variable "MAGNUM_UI_GIT_REF" { default = "c9fdb537eaded73e81ea296d893e45d753337dc7" }
variable "MANILA_UI_GIT_REPO" { default = "https://opendev.org/openstack/manila-ui.git" }
variable "MANILA_UI_GIT_REF" { default = "stable/2024.2" }
variable "NEUTRON_VPNAAS_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/neutron-vpnaas-dashboard.git" }
variable "NEUTRON_VPNAAS_DASHBOARD_GIT_REF" { default = "stable/2024.2" }
variable "OCTAVIA_DASHBOARD_GIT_REPO" { default = "https://opendev.org/openstack/octavia-dashboard.git" }
variable "OCTAVIA_DASHBOARD_GIT_REF" { default = "stable/2024.2" }
variable "IRONIC_GIT_REPO" { default = "https://opendev.org/openstack/ironic.git" }
variable "IRONIC_GIT_REF" { default = "5aa51d6985d25acd6abfb161c62c66facc20a6ca" }
variable "KEYSTONE_GIT_REPO" { default = "https://opendev.org/openstack/keystone.git" }
variable "KEYSTONE_GIT_REF" { default = "47891f4ae8fd7876e5a7657f58c32c371feeddc3" }
variable "MAGNUM_GIT_REPO" { default = "https://opendev.org/openstack/magnum.git" }
variable "MAGNUM_GIT_REF" { default = "db197e08a09da93062fc4222180051dadfc0f0d8" }
variable "MANILA_GIT_REPO" { default = "https://opendev.org/openstack/manila.git" }
variable "MANILA_GIT_REF" { default = "09f3ab0a229362c00bb55f704cfeae43bccd3c8d" }
variable "NEUTRON_GIT_REPO" { default = "https://opendev.org/openstack/neutron.git" }
variable "NEUTRON_GIT_REF" { default = "804d6006e3f09c214d6de8a3f23de70c44f1d51d" }
variable "NEUTRON_VPNAAS_GIT_REPO" { default = "https://opendev.org/openstack/neutron-vpnaas.git" }
variable "NEUTRON_VPNAAS_GIT_REF" { default = "990e478b1e6db459b6cb9aec53ce808e2957bb65" }
variable "NETWORKING_BAREMETAL_GIT_REPO" { default = "https://opendev.org/openstack/networking-baremetal.git" }
variable "NETWORKING_BAREMETAL_GIT_REF" { default = "1fba63ce21619d3fe70117c6679e53629c612bc1" }
variable "POLICY_SERVER_GIT_REPO" { default = "https://github.com/vexxhost/neutron-policy-server.git" }
variable "POLICY_SERVER_GIT_REF" { default = "d87012b56741cb2ad44fa4dec9c5f24001ad60fe" }
variable "LOG_PARSER_GIT_REPO" { default = "https://github.com/vexxhost/neutron-ovn-network-logging-parser.git" }
variable "LOG_PARSER_GIT_REF" { default = "9bc923c1294864ec709c538ba5c309065ef710d5" }
variable "NOVA_GIT_REPO" { default = "https://opendev.org/openstack/nova.git" }
variable "NOVA_GIT_REF" { default = "1b28f649feaf2c9929f15214814f8af950e5c19c" }
variable "SCHEDULER_FILTERS_GIT_REPO" { default = "https://github.com/vexxhost/nova-scheduler-filters.git" }
variable "SCHEDULER_FILTERS_GIT_REF" { default = "77ed1c2ca70f4166a6d0995c7d3d90822f0ca6c0" }
variable "OCTAVIA_GIT_REPO" { default = "https://opendev.org/openstack/octavia.git" }
variable "OCTAVIA_GIT_REF" { default = "e15cb80d8f325e7474fb2175a1a8e9805a473295" }
variable "OVN_OCTAVIA_PROVIDER_GIT_REPO" { default = "https://opendev.org/openstack/ovn-octavia-provider.git" }
variable "OVN_OCTAVIA_PROVIDER_GIT_REF" { default = "stable/2024.2" }
variable "PLACEMENT_GIT_REPO" { default = "https://opendev.org/openstack/placement.git" }
variable "PLACEMENT_GIT_REF" { default = "828b2559a1b3c0b59c543e851c6ea3efb1baae20" }
variable "STAFFELN_GIT_REPO" { default = "https://github.com/vexxhost/staffeln.git" }
variable "STAFFELN_GIT_REF" { default = "v2.2.3" }
variable "TEMPEST_GIT_REPO" { default = "https://opendev.org/openstack/tempest.git" }
variable "TEMPEST_GIT_REF" { default = "338a3b7224a55e88fc46d7f80e8896a3231b910e" }
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

target "ovsinit" {
    context = "images/ovsinit"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "runtime" = "docker-image://docker.io/library/debian:bullseye-slim"
        "rust" = "docker-image://docker.io/library/rust:1.84-bullseye"
        "src" = "./crates/ovsinit"
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
        "golang" = "docker-image://docker.io/library/golang:1.23"
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
        SHELL = "/bin/bash"
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
        "ovsinit" = "target:ovsinit"
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
            "${upper(item.service)}_GIT_REPO" = "${item.git_repo}"
            "${upper(item.service)}_GIT_REF" = "${item.git_ref}"
        },
        try(item.extra_args, {})
    )

    contexts = {
        "openstack-python-runtime" = "target:openstack-python-runtime"
        "openstack-venv-builder" = "target:openstack-venv-builder"
        "ovsinit" = "target:ovsinit"
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
