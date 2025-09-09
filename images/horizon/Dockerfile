# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://github.com/openstack/horizon.git branch=master
ARG HORIZON_GIT_REF=f583f32e7bc44bdecca473dbf6a885d8f5da81dd
ADD --keep-git-dir=true https://github.com/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://github.com/openstack/designate-dashboard.git branch=master
ARG DESIGNATE_DASHBOARD_GIT_REF=7ef1bf9a07c9ef13920d32316c9cb9a18b50a19e
ADD --keep-git-dir=true https://github.com/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
# renovate: name=openstack/heat-dashboard repo=https://github.com/openstack/heat-dashboard.git branch=master
ARG HEAT_DASHBOARD_GIT_REF=8457c7b04c5dd068c9f08d6a1a62efd49a421ddf
ADD --keep-git-dir=true https://github.com/openstack/heat-dashboard.git#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://github.com/openstack/ironic-ui.git branch=master
ARG IRONIC_UI_REF=abd2400a0e40fff5b50d5b3490915b4a0f3ebcbd
ADD --keep-git-dir=true https://github.com/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://github.com/openstack/magnum-ui.git branch=master
ARG MAGNUM_UI_REF=59d8a0864ef10d75baabbde1404f2386759fb2b6
ADD --keep-git-dir=true https://github.com/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://github.com/openstack/manila-ui.git branch=master
ARG MANILA_UI_REF=40a8a1075c3bd0315c5b25b8a5caf6bdb1ef3c30
ADD --keep-git-dir=true https://github.com/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://github.com/openstack/neutron-vpnaas-dashboard.git branch=master
ARG NEUTRON_VPNAAS_DASHBOARD_REF=823399e6187a8c365b1d64b9620f99fd949aadc1
ADD --keep-git-dir=true https://github.com/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://github.com/openstack/octavia-dashboard.git branch=master
ARG OCTAVIA_DASHBOARD_REF=3386566c7c98a055a4e42797f6843f5a44f9e48e
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
