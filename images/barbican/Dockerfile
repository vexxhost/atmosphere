# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-08-05T01:17:39Z

FROM openstack-venv-builder AS build
ADD https://opendev.org/openstack/barbican.git#9f1f1c66a841ab8150e8c1c1bdb529f190086c2f /src/openstack/barbican
RUN PBR_VERSION=20.0.0-dev.25 uv build --wheel /src/openstack/barbican --out-dir /wheels
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /wheels/*.whl \
        pykmip
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
