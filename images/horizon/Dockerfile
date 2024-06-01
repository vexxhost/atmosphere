# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG HORIZON_GIT_REF=5de40f9b222608d35c5a0919117259e966217a86
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#unmaintained/zed /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#unmaintained/zed /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#unmaintained/zed /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#unmaintained/zed /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#unmaintained/zed /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#unmaintained/zed /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-dashboard.git#unmaintained/zed /src/octavia-dashboard
RUN git -C /src/octavia-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/senlin-dashboard.git#unmaintained/zed /src/senlin-dashboard
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

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    apache2 gettext libapache2-mod-wsgi-py3
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
