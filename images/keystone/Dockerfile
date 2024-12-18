# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-10-29T22:19:48Z

ARG RELEASE

FROM harbor.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG KEYSTONE_GIT_REF=6433f1ae1c094e58216360d191a21d956a80f658
ADD --keep-git-dir=true https://opendev.org/openstack/keystone.git#${KEYSTONE_GIT_REF} /src/keystone
RUN git -C /src/keystone fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/keystone[ldap] \
        keystone-keycloak-backend==0.2.0
EOF

FROM harbor.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    apache2 libapache2-mod-wsgi-py3 libapache2-mod-auth-openidc
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
RUN <<EOF bash -xe
a2enmod auth_openidc
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
