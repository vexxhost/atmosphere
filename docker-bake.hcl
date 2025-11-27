variable "REGISTRY" {
    default = "harbor.atmosphere.dev/library"
}

variable "TAG" {
    default = "main"
}

variable "UV_CACHE_ID" {
    default = "uv-${TAG}"
}

target "ovsinit" {
    context = "images/ovsinit"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "runtime" = "docker-image://docker.io/library/debian:bullseye-slim"
        "rust" = "docker-image://docker.io/library/rust:1.87-bullseye"
        "src" = "./crates/ovsinit"
    }
}

target "openstack-python-runtime" {
    context = "images/openstack-runtime"
    platforms = ["linux/amd64", "linux/arm64"]
}

target "libvirtd" {
    context = "images/libvirtd"
    platforms = ["linux/amd64", "linux/arm64"]

    tags = [
        "${REGISTRY}/libvirtd:${TAG}"
    ]
}

target "nova-ssh" {
    context = "images/nova-ssh"
    platforms = ["linux/amd64", "linux/arm64"]

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
}

target "ovn" {
    name = "ovn-${component}"
    matrix = {
        component = ["host", "central"]
    }

    context = "images/ovn"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "golang" = "docker-image://docker.io/library/golang:1.24"
        "openvswitch" = "target:openvswitch"
        "ovsinit" = "target:ovsinit"
    }

    args = {
        OVN_COMPONENT = "${component}"
    }

    tags = [
        "${REGISTRY}/ovn-${component}:${TAG}"
    ]
}

target "python-openstackclient" {
    context = "images/python-openstackclient"
    platforms = ["linux/amd64", "linux/arm64"]

    args = {
        UV_CACHE_ID = "${UV_CACHE_ID}"
    }

    tags = [
        "${REGISTRY}/python-openstackclient:${TAG}"
    ]
}

target "neutron-source" {
    context = "images/source-patch"
    target = "unshallow"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "git" = "https://github.com/openstack/neutron.git#46f4ef447537d80bff2bb64da6a61fff40e8fcc3" # renovate: branch=master
        "patches" = "patches/openstack/neutron"
    }
}

target "neutron" {
    context = "images/neutron"
    platforms = ["linux/amd64", "linux/arm64"]

    args = {
        PROJECT = "neutron"
        UV_CACHE_ID = "${UV_CACHE_ID}"
    }

    contexts = {
        "neutron-source" = "target:neutron-source"
        "openstack-python-runtime" = "target:openstack-python-runtime"
        "ovsinit" = "target:ovsinit"
    }

    tags = [
        "${REGISTRY}/neutron:${TAG}"
    ]
}

target "openstack" {
    name = "openstack-${service}"
    matrix = {
        service = [
            "barbican",
            "cinder",
            "designate",
            "glance",
            "heat",
            "horizon",
            "ironic",
            "keystone",
            "magnum",
            "manila",
            "nova",
            "octavia",
            "ovn-bgp-agent",
            "placement",
            "staffeln",
            "tempest",
        ]
    }

    context = "images/${service}"
    platforms = ["linux/amd64", "linux/arm64"]

    args = {
        PROJECT = "${service}"
        UV_CACHE_ID = "${UV_CACHE_ID}"
    }

    contexts = {
        "openstack-python-runtime" = "target:openstack-python-runtime"
        "ovsinit" = "target:ovsinit"
    }

    tags = [
        "${REGISTRY}/${service}:${TAG}"
    ]
}

group "default" {
    targets = [
        "libvirtd",
        "neutron",
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
        "openstack-nova",
        "openstack-octavia",
        "openstack-ovn-bgp-agent",
        "openstack-placement",
        "openstack-staffeln",
        "openstack-tempest",
        "ovn-central",
        "ovn-host",
        "python-openstackclient",
    ]
}
