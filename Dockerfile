# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T13:53:44Z

ARG RELEASE

FROM golang:1.21 AS go-builder
COPY go.mod go.sum /src/
WORKDIR /src
RUN go mod download

FROM go-builder AS libvirt-tls-sidecar-builder
COPY cmd/ /src/cmd/
COPY internal/ /src/internal/
RUN go build -o main ./cmd/libvirt-tls-sidecar/main.go

FROM registry.atmosphere.dev/library/ubuntu:${RELEASE} AS libvirt-tls-sidecar
COPY --from=libvirt-tls-sidecar-builder /src/main /usr/bin/libvirt-tls-sidecar
ENTRYPOINT ["/usr/bin/libvirt-tls-sidecar"]
