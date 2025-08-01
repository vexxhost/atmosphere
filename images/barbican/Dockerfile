# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/barbican repo=https://opendev.org/openstack/barbican.git branch=master
ARG BARBICAN_GIT_REF=bfd1e72bf070a6a169882ad0abb88687f443a7da
ADD --keep-git-dir=true https://opendev.org/openstack/barbican.git#${BARBICAN_GIT_REF} /src/barbican
RUN git -C /src/barbican fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/barbican \
        pykmip
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
