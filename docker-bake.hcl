variable "REGISTRY" {
    default = "harbor.atmosphere.dev/library"
}

variable "TAG" {
    default = "main"
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

group "default" {
    targets = [
        "libvirtd",
        "nova-ssh",
        "ovn-central",
        "ovn-host",
    ]
}
