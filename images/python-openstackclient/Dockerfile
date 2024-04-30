# Copyright (c) 2024 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        python-openstackclient \
        python-barbicanclient \
        python-designateclient \
        python-glanceclient \
        python-heatclient \
        python-magnumclient \
        python-manilaclient \
        python-neutronclient \
        python-octaviaclient \
        osc-placement \
        python-senlinclient \
        python-swiftclient
EOF

FROM registry.atmosphere.dev/library/python-base:${RELEASE}
COPY --from=build --link /var/lib/openstack /var/lib/openstack
