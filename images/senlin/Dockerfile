# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-02-18T16:05:54Z


FROM openstack-venv-builder AS build
ADD --keep-git-dir=true https://github.com/openstack/senlin.git#zed-eol /src/senlin
RUN git -C /src/senlin fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/senlin
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
