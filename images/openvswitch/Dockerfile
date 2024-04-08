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

FROM quay.io/centos/centos:stream9
ARG OVS_SERIES=3.1
ARG OVS_VERSION=${OVS_SERIES}.0-65
RUN <<EOF sh -xe
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    centos-release-nfv-openvswitch.noarch
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    openvswitch${OVS_SERIES}-${OVS_VERSION}.el9s iptables
dnf -y clean all
rm -rf /var/cache/dnf
EOF
