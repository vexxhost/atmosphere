# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://github.com/openstack/horizon.git branch=stable/2025.1
ARG HORIZON_GIT_REF=d92940b3f5c474eecbd72abf0d4e822aafe270d7
ADD --keep-git-dir=true https://github.com/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://github.com/openstack/designate-dashboard.git branch=stable/2025.1
ARG DESIGNATE_DASHBOARD_GIT_REF=349f34baca5813aebde7097318cde160f60aa061
ADD --keep-git-dir=true https://github.com/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
# renovate: name=openstack/heat-dashboard repo=https://github.com/openstack/heat-dashboard.git branch=stable/2025.1
ARG HEAT_DASHBOARD_GIT_REF=04a8d01a0c02737c1990e7187db5f0f86e8cac93
ADD --keep-git-dir=true https://github.com/openstack/heat-dashboard.git#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://github.com/openstack/ironic-ui.git branch=stable/2025.1
ARG IRONIC_UI_REF=8bd2f060bd072fd9f66e66e9afe6beaccec7d6e7
ADD --keep-git-dir=true https://github.com/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://github.com/openstack/magnum-ui.git branch=stable/2025.1
ARG MAGNUM_UI_REF=eafbf2e90258e469752b67280088285f6b2ef599
ADD --keep-git-dir=true https://github.com/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://github.com/openstack/manila-ui.git branch=stable/2025.1
ARG MANILA_UI_REF=b3e8f8fc771740a3f692e0dc3a90a27b34f40537
ADD --keep-git-dir=true https://github.com/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://github.com/openstack/neutron-vpnaas-dashboard.git branch=stable/2025.1
ARG NEUTRON_VPNAAS_DASHBOARD_REF=87155bb533cb60d8056925785a4d20041919d8cc
ADD --keep-git-dir=true https://github.com/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://github.com/openstack/octavia-dashboard.git branch=stable/2025.1
ARG OCTAVIA_DASHBOARD_REF=178f86172ac34fe444499d8151d559a6fa8d1e09
ADD --keep-git-dir=true https://github.com/openstack/octavia-dashboard.git#${OCTAVIA_DASHBOARD_REF} /src/octavia-dashboard
RUN git -C /src/octavia-dashboard fetch --unshallow
COPY patches/magnum-ui /patches/magnum-ui
RUN git -C /src/magnum-ui apply --verbose /patches/magnum-ui/*
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
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
