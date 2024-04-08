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

FROM registry.atmosphere.dev/library/openstack-venv-builder:main AS build
ARG BARBICAN_GIT_REF=7d6749fcb1ad16a3350de82cd8e523d5b55306f8
ADD --keep-git-dir=true https://opendev.org/openstack/barbican.git#${BARBICAN_GIT_REF} /src/barbican
RUN git -C /src/barbican fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/barbican \
        pykmip
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:main
COPY --from=build --link /var/lib/openstack /var/lib/openstack
