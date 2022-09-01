# syntax=docker/dockerfile:1.4

FROM python:3

# Install binary dependencies
RUN <<EOF
  apt-get update
  apt-get install -y --no-install-recommends \
    ethtool
  apt-get clean
  rm -rfv /var/lib/apt/lists/*
EOF

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache <<EOF
  pip install prometheus-client==0.14.1
EOF

# Install exporter
ARG PROJECT_REF
ADD --chmod=755 \
  https://raw.githubusercontent.com/Showmax/prometheus-ethtool-exporter/${PROJECT_REF}/ethtool-exporter.py \
  /usr/local/bin/ethtool-exporter

# Set annotations
ENTRYPOINT ["/usr/local/bin/ethtool-exporter"]
