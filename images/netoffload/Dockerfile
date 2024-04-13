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

FROM golang:1.20 AS build
ARG NETOFFLOAD_GIT_REF=94b8c0fdb0b83bd1b7e14b9a58077a047c78a800
ADD https://github.com/vexxhost/netoffload.git#${NETOFFLOAD_GIT_REF} /src
WORKDIR /src
RUN go build -v -o offloadctl ./cmd/offloadctl/main.go

FROM registry.atmosphere.dev/library/ubuntu:main
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    jq mstflint
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /src/offloadctl /usr/local/bin/offloadctl
