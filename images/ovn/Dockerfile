# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-10-31T12:56:04Z

ARG RELEASE
ARG FROM=harbor.atmosphere.dev/library/centos:${RELEASE}

FROM --platform=$BUILDPLATFORM ${FROM} AS installer
ARG TARGETARCH
ARG OVN_COMPONENT
RUN --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/var/cache/dnf --mount=type=cache,id=dnf-cache-${TARGETARCH},target=/target/var/cache/dnf <<EOF bash -xe
install-packages \
  firewalld-filesystem \
  hostname \
  ovn24.03-${OVN_COMPONENT} \
  procps-ng
EOF

# TODO(mnaser): Switch this to being packaged in the future
FROM harbor.atmosphere.dev/docker.io/library/golang:1.20 AS ovn-kubernetes
ARG OVN_KUBERNETES_REF=5359e7d7f872058b6e5bf884c9f19d1922451f29
ADD https://github.com/ovn-org/ovn-kubernetes.git#${OVN_KUBERNETES_REF} /src
COPY patches/ovn-kubernetes /patches/ovn-kubernetes
RUN git -C /src apply --verbose /patches/ovn-kubernetes/*
RUN <<EOF bash -xe
cd /src/go-controller
go build -o /usr/bin/ovn-kube-util ./cmd/ovn-kube-util
EOF

FROM scratch
ARG TARGETPLATFORM
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/${TARGETPLATFORM}/kubectl /usr/local/bin/kubectl
COPY --from=ovn-kubernetes --link /src/dist/images/ovndb-raft-functions.sh /root/ovndb-raft-functions.sh
COPY --from=ovn-kubernetes --link /src/dist/images/ovnkube.sh /root/ovnkube.sh
COPY --from=ovn-kubernetes --link /usr/bin/ovn-kube-util /usr/bin/ovn-kube-util
COPY --link --from=installer /target/ /
