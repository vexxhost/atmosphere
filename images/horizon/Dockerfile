# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  gettext \
  httpd \
  mod_wsgi \
  openstack-dashboard \
  openstack-designate-ui \
  openstack-heat-ui \
  openstack-ironic-ui \
  openstack-magnum-ui \
  openstack-manila-ui \
  openstack-octavia-ui \
  python3-pip \
  python3-pymemcache
EOF

FROM scratch
COPY --link --from=installer /target/ /
# TODO(mnaser): Remove this + "python3-pip" dependency once this is packaged
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
python3 -m pip install neutron-vpnaas-dashboard
EOF
