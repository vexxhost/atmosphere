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

FROM alpine/git:2.43.0 AS src
ARG CAPO_VERSION=v0.9.0
ADD https://github.com/kubernetes-sigs/cluster-api-provider-openstack.git#${CAPO_VERSION} /src
WORKDIR /src
COPY /patches /patches
RUN git apply /patches/*.patch

FROM golang:1.20 AS builder
COPY --from=src --link /src /src
WORKDIR /src
ARG ARCH
RUN CGO_ENABLED=0 GOOS=linux GOARCH=${ARCH} \
    go build -ldflags "-extldflags '-static'" -o manager ${package}

FROM gcr.io/distroless/static:nonroot
COPY --from=builder /src/manager /manager
USER 65532
ENTRYPOINT ["/manager"]
