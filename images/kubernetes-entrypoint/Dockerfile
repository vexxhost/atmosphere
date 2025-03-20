# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM golang AS build
# renovate: name=kubernetes-entrypoint repo=https://opendev.org/airship/kubernetes-entrypoint.git branch=master
ARG KUBERNETES_ENTRYPOINT_GIT_REF=4fbcf7ce324dc66e78480f73035e31434cfea1e8
ADD https://opendev.org/airship/kubernetes-entrypoint.git#${KUBERNETES_ENTRYPOINT_GIT_REF} /src
WORKDIR /src
RUN CGO_ENABLED=0 GOOS=linux go build -o /main

FROM scratch
COPY --from=build /main /kubernetes-entrypoint
USER 65534
ENTRYPOINT ["/kubernetes-entrypoint"]
