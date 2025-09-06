# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://github.com/openstack/horizon.git branch=master
ARG HORIZON_GIT_REF=c7e4095f9560f2244d067a62aa2e49d3759c67f2
ADD --keep-git-dir=true https://github.com/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://github.com/openstack/designate-dashboard.git branch=master
ARG DESIGNATE_DASHBOARD_GIT_REF=8b8fffde20f2504c51052506c8f2590a45352962
ADD --keep-git-dir=true https://github.com/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
# renovate: name=openstack/heat-dashboard repo=https://github.com/openstack/heat-dashboard.git branch=master
ARG HEAT_DASHBOARD_GIT_REF=ad02530855411ea83af276cfee31848e28f1cf2f
ADD --keep-git-dir=true https://github.com/openstack/heat-dashboard.git#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://github.com/openstack/ironic-ui.git branch=master
ARG IRONIC_UI_REF=40d8f907334c113cf2fe43bd2a5bbbef6baadbab
ADD --keep-git-dir=true https://github.com/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://github.com/openstack/magnum-ui.git branch=master
ARG MAGNUM_UI_REF=c9fdb537eaded73e81ea296d893e45d753337dc7
ADD --keep-git-dir=true https://github.com/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://github.com/openstack/manila-ui.git branch=master
ARG MANILA_UI_REF=55945d56a479790e5443299fa4991e7728a6f89d
ADD --keep-git-dir=true https://github.com/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://github.com/openstack/neutron-vpnaas-dashboard.git branch=master
ARG NEUTRON_VPNAAS_DASHBOARD_REF=6207d9a20b2f3c53a50d767a364aa8c448a2c923
ADD --keep-git-dir=true https://github.com/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://github.com/openstack/octavia-dashboard.git branch=master
ARG OCTAVIA_DASHBOARD_REF=1d4b034669c819217a0f58a394dae4340661bdeb
ADD --keep-git-dir=true https://github.com/openstack/octavia-dashboard.git#${OCTAVIA_DASHBOARD_REF} /src/octavia-dashboard
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
