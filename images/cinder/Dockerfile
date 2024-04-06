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

FROM registry.atmosphere.dev/library/openstack-venv-builder:zed AS build
ARG CINDER_GIT_REF=f74e2729554bee01b0a3e631a8001bb39e540433
ADD --keep-git-dir=true https://opendev.org/openstack/cinder.git#${CINDER_GIT_REF} /src/cinder
RUN git -C /src/cinder fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/cinder \
        purestorage
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:zed
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ceph-common lsscsi nvme-cli python3-rados python3-rbd qemu-utils sysfsutils udev util-linux
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
COPY --from=build --link /var/lib/openstack /var/lib/openstack
