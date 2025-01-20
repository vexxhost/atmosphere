# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
ARG HORIZON_GIT_REPO
ARG HORIZON_GIT_REF
ADD --keep-git-dir=true ${HORIZON_GIT_REPO}#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
ARG DESIGNATE_DASHBOARD_GIT_REPO
ARG DESIGNATE_DASHBOARD_GIT_REF
ADD --keep-git-dir=true ${DESIGNATE_DASHBOARD_GIT_REPO}#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
ARG HEAT_DASHBOARD_GIT_REPO
ARG HEAT_DASHBOARD_GIT_REF
ADD --keep-git-dir=true ${HEAT_DASHBOARD_GIT_REPO}#${HEAT_DASHBOARD_GIT_REF} /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
ARG IRONIC_UI_GIT_REPO
ARG IRONIC_UI_GIT_REF
ADD --keep-git-dir=true ${IRONIC_UI_GIT_REPO}#${IRONIC_UI_GIT_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
ARG MAGNUM_UI_GIT_REPO
ARG MAGNUM_UI_GIT_REF
ADD --keep-git-dir=true ${MAGNUM_UI_GIT_REPO}#${MAGNUM_UI_GIT_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
ARG MANILA_UI_GIT_REPO
ARG MANILA_UI_GIT_REF
ADD --keep-git-dir=true ${MANILA_UI_GIT_REPO}#${MANILA_UI_GIT_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
ARG NEUTRON_VPNAAS_DASHBOARD_GIT_REPO
ARG NEUTRON_VPNAAS_DASHBOARD_GIT_REF
ADD --keep-git-dir=true ${NEUTRON_VPNAAS_DASHBOARD_GIT_REPO}#${NEUTRON_VPNAAS_DASHBOARD_GIT_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
ARG OCTAVIA_DASHBOARD_GIT_REPO
ARG OCTAVIA_DASHBOARD_GIT_REF
ADD --keep-git-dir=true ${OCTAVIA_DASHBOARD_GIT_REPO}#${OCTAVIA_DASHBOARD_GIT_REF} /src/octavia-dashboard
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
