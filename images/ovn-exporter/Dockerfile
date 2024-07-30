# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu:${RELEASE} AS helm
ARG TARGETOS
ARG TARGETARCH
ARG OVN_EXPORTER_VERSION=1.0.7
ADD https://github.com/greenpau/ovn_exporter/releases/download/v${OVN_EXPORTER_VERSION}/ovn-exporter_${OVN_EXPORTER_VERSION}_${TARGETOS}_${TARGETARCH}.tar.gz /ovn-exporter.tar.gz
RUN <<EOF bash -xe
tar -xzf /ovn-exporter.tar.gz -C /tmp
mv /tmp/ovn-exporter /usr/bin/ovn-exporter
rm -rf /ovn-exporter.tar.gz /tmp/LICENSE /tmp/README.md
EOF
ENTRYPOINT ["/usr/bin/ovn-exporter"]
