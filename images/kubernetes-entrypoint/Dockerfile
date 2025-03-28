# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang AS build
# renovate: name=airship/kubernetes-entrypoint repo=https://opendev.org/airship/kubernetes-entrypoint.git branch=master
ARG KUBERNETES_ENTRYPOINT_GIT_REF=cc2737be5285951ac08b32e76dfd375e1a0ab81f
ADD https://opendev.org/airship/kubernetes-entrypoint.git#${KUBERNETES_ENTRYPOINT_GIT_REF} /src
WORKDIR /src
RUN CGO_ENABLED=0 GOOS=linux go build -o /main

FROM scratch
COPY --from=build /main /kubernetes-entrypoint
USER 65534
ENTRYPOINT ["/kubernetes-entrypoint"]
