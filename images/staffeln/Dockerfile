# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
ARG STAFFELN_GIT_REF=v2.2.3
ADD --keep-git-dir=true https://github.com/vexxhost/staffeln.git#${STAFFELN_GIT_REF} /src/staffeln
RUN git -C /src/staffeln fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/staffeln
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
