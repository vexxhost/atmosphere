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

FROM golang:1.21 AS go-builder
COPY go.mod go.sum /src/
WORKDIR /src
RUN go mod download

FROM go-builder AS libvirt-tls-sidecar-builder
COPY cmd/ /src/cmd/
COPY internal/ /src/internal/
RUN go build -o main ./cmd/libvirt-tls-sidecar/main.go

FROM registry.atmosphere.dev/library/ubuntu:main AS libvirt-tls-sidecar
COPY --from=libvirt-tls-sidecar-builder /src/main /usr/bin/libvirt-tls-sidecar
ENTRYPOINT ["/usr/bin/libvirt-tls-sidecar"]
