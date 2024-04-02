variable "REGISTRY" {
    default = "registry.atmosphere.dev/library"
}

variable "CACHE_REGISTRY" {
    default = "registry.atmosphere.dev/cache"
}

variable "PUSH_TO_CACHE" {
    default = false
}

function "cache_from" {
    params = [image]
    result = ["type=registry,ref=${CACHE_REGISTRY}/${image}"]
}

function "cache_to" {
    params = [image]
    result = PUSH_TO_CACHE ? [format("%s,%s", cache_from(image)[0], "mode=max,image-manifest=true,oci-mediatypes=true,compression=zstd")] : []
}

target "ubuntu" {
    context = "./images/ubuntu"

    cache-from = cache_from("ubuntu")
    cache-to = cache_to("ubuntu")

    contexts = {
        ubuntu = "docker-image://ubuntu:jammy-20240227"
    }
}

target "git" {
    context = "./images/git"

    cache-from = cache_from("git")
    cache-to = cache_to("git")
}

target "ubuntu-cloud-archive" {
    name = "ubuntu-cloud-archive-${release.tgt}"
    context = "./images/ubuntu-cloud-archive"

    cache-from = cache_from("ubuntu-cloud-archive:${release.name}")
    cache-to = cache_to("ubuntu-cloud-archive:${release.name}")

    matrix = {
        release = [
            {
                tgt = "zed",
                name = "zed",
            },
            {
                tgt = "bobcat",
                name = "2023.2",
            }
        ]
    }

    contexts = {
        ubuntu = "target:ubuntu"
    }

    args = {
        RELEASE = release.name
    }
}

target "requirements" {
    name = "requirements-${release.tgt}"
    context = "./images/requirements"

    cache-from = cache_from("requirements:${release.name}")
    cache-to = cache_to("requirements:${release.name}")

    matrix = {
        release = [
            {
                tgt = "zed",
                name = "zed",
            },
            {
                tgt = "bobcat",
                name = "2023.2",
            }
        ]
    }

    contexts = {
        ubuntu = "target:ubuntu"
    }

    args = {
        RELEASE = release.name
    }
}

target "openstack-venv-builder" {
    name = "openstack-venv-builder-${release.tgt}"
    context = "./images/openstack-venv-builder"

    cache-from = cache_from("openstack-venv-builder:${release.name}")
    cache-to = cache_to("openstack-venv-builder:${release.name}")

    matrix = {
        release = [
            {
                tgt = "zed",
                name = "zed",
            },
            {
                tgt = "bobcat",
                name = "2023.2",
            }
        ]
    }

    contexts = {
        ubuntu-cloud-archive = "target:ubuntu-cloud-archive-${release.tgt}",
        requirements = "target:requirements-${release.tgt}",
    }

    args = {
        RELEASE = release.name
    }
}

target "openstack-runtime" {
    name = "openstack-runtime-${release.tgt}"
    context = "./images/openstack-runtime"

    cache-from = cache_from("openstack-runtime:${release.name}")
    cache-to = cache_to("openstack-runtime:${release.name}")

    matrix = {
        release = [
            {
                tgt = "zed",
                name = "zed",
            },
            {
                tgt = "bobcat",
                name = "2023.2",
            }
        ]
    }

    contexts = {
        ubuntu-cloud-archive = "target:ubuntu-cloud-archive-${release.tgt}",
    }

    args = {
        RELEASE = release.name
    }
}

target "barbican" {
    name = "barbican-${release.tgt}"
    context = "./images/barbican"

    cache-from = cache_from("barbican:${release.name}")
    cache-to = cache_to("barbican:${release.name}")

    tags = [
        "${REGISTRY}/barbican:${release.name}",
        "${REGISTRY}/barbican:${release.ref}"
    ]

    matrix = {
        release = [
            {
                tgt = "bobcat",
                name = "2023.2",
                ref = "a00fcade4138ffc52cd9c84b5999297966f019b5"
            }
        ]
    }

    contexts = {
        openstack-venv-builder = "target:openstack-venv-builder-${release.tgt}"
        openstack-runtime = "target:openstack-runtime-${release.tgt}",
        git = "target:git"
    }

    args = {
        RELEASE = release.name
        PROJECT = "barbican"
        BARBICAN_GIT_REF = release.ref
    }
}

group "default" {
    targets = [
        "barbican"
    ]
}
