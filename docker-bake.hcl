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

target "barbican" {
    name = "barbican-${release.tgt}"

    context = "."
    target = "barbican"

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

    args = {
        RELEASE = release.name
        BRANCH = format("stable/%s", release.name)
        PROJECT = "barbican"
        BARBICAN_GIT_REF = release.ref
    }
}

group "default" {
    targets = [
        "barbican"
    ]
}
