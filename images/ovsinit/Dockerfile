# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-10-14T10:18:12Z

FROM rust AS builder
WORKDIR /src
COPY --from=src / /src
RUN cargo install --path .

FROM runtime
COPY --from=builder /usr/local/cargo/bin/ovsinit /usr/local/bin/ovsinit
