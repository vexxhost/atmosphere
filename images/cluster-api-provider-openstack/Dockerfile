# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang:1.22.12 AS builder
WORKDIR /workspace
RUN \
  --mount=type=bind,from=source,source=/,target=/workspace/src,readwrite \
  --mount=type=cache,target=/go/pkg/mod \
  --mount=type=cache,target=/root/.cache/go-build <<EOF sh -xe
make -C /workspace/src binaries
mv /workspace/src/bin /workspace/bin
EOF

FROM scratch
COPY --from=builder /workspace/bin/manager /manager
USER 65532
ENTRYPOINT ["/manager"]
