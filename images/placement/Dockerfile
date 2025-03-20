# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/placement repo=https://opendev.org/openstack/placement.git branch=stable/2023.2
ARG PLACEMENT_GIT_REF=a361622d749d3b24aad638ec1b03a7d7124a87b3
ADD --keep-git-dir=true https://opendev.org/openstack/placement.git#${PLACEMENT_GIT_REF} /src/placement
RUN git -C /src/placement fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/placement
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
