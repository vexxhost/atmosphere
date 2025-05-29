variable "REGISTRY" {
    default = "harbor.atmosphere.dev/library"
}

variable "TAG" {
    default = "main"
}

target "cluster-api-provider-openstack-source" {
    context = "images/source-patch"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "git" = "https://github.com/kubernetes-sigs/cluster-api-provider-openstack.git#v0.11.6"
        "patches" = "patches/kubernetes-sigs/cluster-api-provider-openstack"
    }
}

target "cluster-api-provider-openstack" {
    context = "images/cluster-api-provider-openstack"
    platforms = ["linux/amd64", "linux/arm64"]

    contexts = {
        "source" = "target:cluster-api-provider-openstack-source"
    }

    tags = [
        "${REGISTRY}/capi-openstack-controller:${TAG}"
    ]
}

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
        "rust" = "docker-image://docker.io/library/rust:1.86-bullseye"
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
        "golang" = "docker-image://docker.io/library/golang:1.24"
        "ubuntu" = "target:ubuntu"
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

    contexts = {
        "openstack-venv-builder" = "target:openstack-venv-builder"
        "python-base" = "target:python-base"
    }

    tags = [
        "${REGISTRY}/python-openstackclient:${TAG}"
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
            "neutron",
            "nova",
            "octavia",
            "placement",
            "staffeln",
            "tempest",
        ]
    }

    context = "images/${service}"
    platforms = ["linux/amd64", "linux/arm64"]

    args = {
        PROJECT = "${service}"
    }

    contexts = {
        "openstack-python-runtime" = "target:openstack-python-runtime"
        "openstack-venv-builder" = "target:openstack-venv-builder"
        "ovsinit" = "target:ovsinit"
    }

    tags = [
        "${REGISTRY}/${service}:${TAG}"
    ]
}

group "default" {
    targets = [
        "cluster-api-provider-openstack",
        "keepalived",
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
