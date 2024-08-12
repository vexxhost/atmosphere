# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

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
