# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-28T12:14:26Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG PLACEMENT_GIT_REF=d7ced6bd2fc82caf458f20b5652888164b1bbb70
ADD --keep-git-dir=true https://opendev.org/openstack/placement.git#${PLACEMENT_GIT_REF} /src/placement
RUN git -C /src/placement fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/placement
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
COPY --from=build --link /var/lib/openstack /var/lib/openstack
