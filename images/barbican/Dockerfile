# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-09-23T21:18:36Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG BARBICAN_GIT_REF=9d641cef1811180597f5bfa6066eea2e14b12b88
ADD --keep-git-dir=true https://opendev.org/openstack/barbican.git#${BARBICAN_GIT_REF} /src/barbican
RUN git -C /src/barbican fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/barbican \
        pykmip
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
COPY --from=build --link /var/lib/openstack /var/lib/openstack
