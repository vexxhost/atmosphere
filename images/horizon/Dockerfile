# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
ARG HORIZON_GIT_REF=24274d1e7f9a22a5dab9993b427cbfddaef085ab
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#master /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#master /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#master /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
ARG MAGNUM_UI_REF=c9fdb537eaded73e81ea296d893e45d753337dc7
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#master /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#master /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-dashboard.git#master /src/octavia-dashboard
RUN git -C /src/octavia-dashboard fetch --unshallow
COPY patches/magnum-ui /patches/magnum-ui
RUN git -C /src/magnum-ui apply --verbose /patches/magnum-ui/*
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/designate-dashboard \
        /src/heat-dashboard \
        /src/horizon \
        /src/ironic-ui \
        /src/magnum-ui \
        /src/manila-ui \
        /src/neutron-vpnaas-dashboard \
        /src/octavia-dashboard \
        pymemcache
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    apache2 gettext libapache2-mod-wsgi-py3
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
