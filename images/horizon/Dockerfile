# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://opendev.org/openstack/horizon.git branch=stable/2024.1
ARG HORIZON_GIT_REF=a9267a60d18bea494ce444cde914488907def2a2
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://opendev.org/openstack/designate-dashboard.git branch=stable/2024.1
ARG DESIGNATE_DASHBOARD_GIT_REF=ae09bd6477803c271c742fbd239c75cd3b7914b2
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
# renovate: name=openstack/heat-dashboard repo=https://opendev.org/openstack/heat-dashboard.git branch=stable/2024.1
ARG HEAT_DASHBOARD_GIT_REF=0f8ddbaec6fc01733e6ac7d709e7f36761330ede
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://opendev.org/openstack/ironic-ui.git branch=stable/2024.1
ARG IRONIC_UI_REF=a50a6e491c85de91bc751a621082f9dac594dac2
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://opendev.org/openstack/magnum-ui.git branch=stable/2024.1
ARG MAGNUM_UI_REF=e79a2177c8645ba50093896832626d5663c43931
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://opendev.org/openstack/manila-ui.git branch=stable/2024.1
ARG MANILA_UI_REF=536db83eec954a28acfed7af3ac7a15a3bc208e5
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://opendev.org/openstack/neutron-vpnaas-dashboard.git branch=stable/2024.1
ARG NEUTRON_VPNAAS_DASHBOARD_REF=a3136f6f3597f291c97e9802b421048fe9286356
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://opendev.org/openstack/octavia-dashboard.git branch=stable/2024.1
ARG OCTAVIA_DASHBOARD_REF=468c619bfc27b8734698571de12c06ab6ff6241a
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
