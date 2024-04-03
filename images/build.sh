#!/bin/bash -xe

TARGET=""
PUSH=false

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        --push)
        PUSH=true
        shift
        ;;
        *)
        if [ -z "$TARGET" ]; then
            TARGET="$1"
        else
            echo "Invalid argument: $1"
            exit 1
        fi
        shift
        ;;
    esac
done

if [ -z "$TARGET" ]; then
    echo "Usage: $0 [--push] <target>"
    exit 1
fi

docker buildx create --name=atmosphere --driver=docker-container || true

if [ "$PUSH" = true ]; then
    docker buildx bake --builder=atmosphere --provenance --sbom=true --push $TARGET

    # Sign all images
    export COSIGN_PASSWORD=""
    for IMAGE in $(docker buildx bake --print ${TARGET} | jq -r '.target[].tags | select(. != null)[]'); do
        cosign sign -y --recursive --key cosign.key ${IMAGE}
    done
else
    docker buildx bake --builder=atmosphere --provenance --sbom=true $TARGET
fi
