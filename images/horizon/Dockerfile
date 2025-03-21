# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://opendev.org/openstack/horizon.git branch=stable/2023.2
ARG HORIZON_GIT_REF=c873490d3fe773aa7f75521cf9a66683c0c35f6f
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://opendev.org/openstack/designate-dashboard.git branch=stable/2023.2
ARG DESIGNATE_DASHBOARD_GIT_REF=d18391bbad37aafcd58a38787ea82b2ca8b492c7
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
# renovate: name=openstack/heat-dashboard repo=https://opendev.org/openstack/heat-dashboard.git branch=stable/2023.2
ARG HEAT_DASHBOARD_GIT_REF=2bbd7e87efc7b30af296eabb846b45feb435cd34
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://opendev.org/openstack/ironic-ui.git branch=stable/2023.2
ARG IRONIC_UI_REF=98843d82b2e9483b36923f9d6c3a64d70e0f0199
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://opendev.org/openstack/magnum-ui.git branch=stable/2023.2
ARG MAGNUM_UI_REF=b764229b378762e077349cc24eba689cfc8f9200
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://opendev.org/openstack/manila-ui.git branch=stable/2023.2
ARG MANILA_UI_REF=d28c06a52551206f194aaeadcc5fb861b5c2cf53
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://opendev.org/openstack/neutron-vpnaas-dashboard.git branch=stable/2023.2
ARG NEUTRON_VPNAAS_DASHBOARD_REF=f369617faa47e202fe78cae584ac957912fd4bab
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://opendev.org/openstack/octavia-dashboard.git branch=stable/2023.2
ARG OCTAVIA_DASHBOARD_REF=734b8ea6d5c737d56425bd52f060e6af9b95f64d
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-dashboard.git#${OCTAVIA_DASHBOARD_REF} /src/octavia-dashboard
RUN git -C /src/octavia-dashboard fetch --unshallow
COPY patches/horizon /patches/horizon
RUN git -C /src/horizon apply --verbose /patches/horizon/*
COPY patches/magnum-ui /patches/magnum-ui
RUN git -C /src/magnum-ui apply --verbose /patches/magnum-ui/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
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
