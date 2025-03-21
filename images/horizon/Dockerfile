# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://opendev.org/openstack/horizon.git branch=unmaintained/2023.1
ARG HORIZON_GIT_REF=d205ff09bed65b08960c3578434060eac9273fba
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://opendev.org/openstack/designate-dashboard.git branch=unmaintained/2023.1
ARG DESIGNATE_DASHBOARD_GIT_REF=901c7521ac4135c155bbb8e698f87f537793868e
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
# renovate: name=openstack/heat-dashboard repo=https://opendev.org/openstack/heat-dashboard.git branch=unmaintained/2023.1
ARG HEAT_DASHBOARD_GIT_REF=007a7a5a3b338543dd6e3badd04967324e8f0e9b
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://opendev.org/openstack/ironic-ui.git branch=unmaintained/2023.1
ARG IRONIC_UI_REF=544490f9b5e2392cdd49756bf5d7a347947f251b
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://opendev.org/openstack/magnum-ui.git branch=unmaintained/2023.1
ARG MAGNUM_UI_REF=bf91ac67419cddb4953d0a04890377be618fa160
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://opendev.org/openstack/manila-ui.git branch=unmaintained/2023.1
ARG MANILA_UI_REF=e64ab732b9aa850dde7ed6d2fdc96ae1de25d4d8
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://opendev.org/openstack/neutron-vpnaas-dashboard.git branch=unmaintained/2023.1
ARG NEUTRON_VPNAAS_DASHBOARD_REF=711dfd68d6f273f6303ed7de72b2c3690a181347
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://opendev.org/openstack/octavia-dashboard.git branch=unmaintained/2023.1
ARG OCTAVIA_DASHBOARD_REF=8802dba593389d32896c82a79507640528b39702
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-dashboard.git#${OCTAVIA_DASHBOARD_REF} /src/octavia-dashboard
RUN git -C /src/octavia-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/senlin-dashboard.git#2023.1-eol /src/senlin-dashboard
RUN git -C /src/senlin-dashboard fetch --unshallow
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
        /src/senlin-dashboard \
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
