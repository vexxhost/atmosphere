# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu:${RELEASE} AS helm
ARG TARGETOS
ARG TARGETARCH
ARG OVS_EXPORTER_VERSION=1.0.7
ADD https://github.com/greenpau/ovs_exporter/releases/download/v${OVS_EXPORTER_VERSION}/ovs-exporter_${OVS_EXPORTER_VERSION}_${TARGETOS}_${TARGETARCH}.tar.gz /ovs-exporter.tar.gz
RUN <<EOF bash -xe
tar -xzf /ovs-exporter.tar.gz -C /tmp
mv /tmp/ovs-exporter /usr/bin/ovs-exporter
rm -rf /ovs-exporter.tar.gz /tmp/LICENSE /tmp/README.md
EOF
ENTRYPOINT ["/usr/bin/ovs-exporter"]
