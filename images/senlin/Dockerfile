# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z


FROM openstack-venv-builder AS build
ARG SENLIN_GIT_REF=b6ef17b0f787fb7a0609ba36dc13097882a6a3ff
ADD --keep-git-dir=true https://opendev.org/openstack/senlin.git#${SENLIN_GIT_REF} /src/senlin
RUN git -C /src/senlin fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/senlin
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
