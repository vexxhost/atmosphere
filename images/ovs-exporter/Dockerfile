# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM alpine/git:2.43.0 AS src
ARG OVS_EXPORTER_VERSION=v1.0.7
ADD https://github.com/greenpau/ovs_exporter.git#${OVS_EXPORTER_VERSION} /src
WORKDIR /src
# COPY /patches /patches
# RUN git apply /patches/*.patch

FROM golang:1.20 AS builder
COPY --from=src --link /src /src
WORKDIR /src
ARG TARGETARCH
RUN BUILD_ARCH=${TARGETARCH} BUILD_OS=linux make all

FROM gcr.io/distroless/static:nonroot
ARG TARGETARCH
COPY --from=builder /src/bin/linux-${TARGETARCH}/ovs-exporter /ovs-exporter
USER 65532
ENTRYPOINT ["/ovs-exporter"]
