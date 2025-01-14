# Copyright (c) 2024 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-only
# Atmosphere-Rebuild-Time: 2025-01-04T23:34:28Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  httpd \
  mod_auth_openidc \
  mod_wsgi \
  openstack-keystone \
  python3-ldap \
  python3-ldappool \
  python3-pip
EOF

FROM scratch
COPY --link --from=installer /target/ /
# NOTE(mnaser): auth_openidc is a little too locked down and the config it
#               ships is empty anyways, so we'll just remove it.
RUN rm -f /etc/httpd/conf.d/auth_openidc.conf
# TODO(mnaser): Remove this + "python3-pip" dependency once this is packaged
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
python3 -m pip install keystone-keycloak-backend==0.1.8
EOF
