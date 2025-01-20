# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG PLACEMENT_GIT_REPO
ARG REGISTRY
ARG RELEASE

FROM ${REGISTRY}/openstack-venv-builder:${RELEASE} AS build
ARG PLACEMENT_GIT_REF=96a9aeb3b4a6ffff5bbf247b213409395239fc7a
ADD --keep-git-dir=true ${PLACEMENT_GIT_REPO}#${PLACEMENT_GIT_REF} /src/placement
RUN git -C /src/placement fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/placement
EOF

FROM ${REGISTRY}/openstack-python-runtime:${RELEASE}
COPY --from=build --link /var/lib/openstack /var/lib/openstack
