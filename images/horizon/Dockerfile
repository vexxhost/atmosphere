# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG HORIZON_GIT_REF=3f1f1d46e6e47a3dbe46fb023fe69ff25d6a601b
ADD --keep-git-dir=true https://opendev.org/openstack/horizon.git#${HORIZON_GIT_REF} /src/horizon
RUN git -C /src/horizon fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/designate-dashboard.git#master /src/designate-dashboard
RUN git -C /src/designate-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-dashboard.git#master /src/heat-dashboard
RUN git -C /src/heat-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/ironic-ui.git#master /src/ironic-ui
RUN git -C /src/ironic-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/magnum-ui.git#master /src/magnum-ui
RUN git -C /src/magnum-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/manila-ui.git#master /src/manila-ui
RUN git -C /src/manila-ui fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-vpnaas-dashboard.git#master /src/neutron-vpnaas-dashboard
RUN git -C /src/neutron-vpnaas-dashboard fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-dashboard.git#master /src/octavia-dashboard
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

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    apache2 gettext libapache2-mod-wsgi-py3
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
