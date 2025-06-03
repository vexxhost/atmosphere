# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/horizon repo=https://opendev.org/openstack/horizon.git branch=unmaintained/zed
ARG HORIZON_GIT_REF=5de40f9b222608d35c5a0919117259e966217a86
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
# renovate: name=openstack/designate-dashboard repo=https://opendev.org/openstack/designate-dashboard.git branch=unmaintained/zed
ARG DESIGNATE_DASHBOARD_GIT_REF=fde744e28936a7e4a0e9bc73137c5e67f11cd333
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#${DESIGNATE_DASHBOARD_GIT_REF} /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#zed-eol /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
# renovate: name=openstack/ironic-ui repo=https://opendev.org/openstack/ironic-ui.git branch=unmaintained/zed
ARG IRONIC_UI_REF=d471c0d6c792a32092924b6e9e6fae7597d14601
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#${IRONIC_UI_REF} /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
# renovate: name=openstack/magnum-ui repo=https://opendev.org/openstack/magnum-ui.git branch=unmaintained/zed
ARG MAGNUM_UI_REF=c4c60b779d52a713c0acb3ef4c7987aab1a42657
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#${MAGNUM_UI_REF} /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
# renovate: name=openstack/manila-ui repo=https://opendev.org/openstack/manila-ui.git branch=unmaintained/zed
ARG MANILA_UI_REF=961fc0168b0271cb6e6bee8f7abef732445b9fc7
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#${MANILA_UI_REF} /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
# renovate: name=openstack/neutron-vpnaas-dashboard repo=https://opendev.org/openstack/neutron-vpnaas-dashboard.git branch=unmaintained/zed
ARG NEUTRON_VPNAAS_DASHBOARD_REF=d07bc632d88ff7c8143e501ba15544c18381d08b
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#${NEUTRON_VPNAAS_DASHBOARD_REF} /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
# renovate: name=openstack/octavia-dashboard repo=https://opendev.org/openstack/octavia-dashboard.git branch=unmaintained/zed
ARG OCTAVIA_DASHBOARD_REF=c3cec4d27756601aff32d0fd560166e65a2e1547
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-dashboard.git#${OCTAVIA_DASHBOARD_REF} /src/octavia-dashboard
RUN git -C /src/octavia-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/senlin-dashboard.git#zed-eol /src/senlin-dashboard
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
        /src/senlin-dashboard
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
