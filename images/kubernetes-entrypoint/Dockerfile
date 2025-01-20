# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang AS build
<<<<<<< HEAD
ARG KUBERNETES_ENTRYPOINT_GIT_REF=df2f40f3dec3aca3e648f4f351ff5ccfbd659b59
ADD https://opendev.org/airship/kubernetes-entrypoint.git#${KUBERNETES_ENTRYPOINT_GIT_REF} /src
=======
ARG KUBERNETES_ENTRYPOINT_GIT_REPO
ARG KUBERNETES_ENTRYPOINT_GIT_REF
ADD ${KUBERNETES_ENTRYPOINT_GIT_REPO}#${KUBERNETES_ENTRYPOINT_GIT_REF} /src
>>>>>>> 73c0c31d (Add PROJECT_GIT_REPO to all images)
WORKDIR /src
RUN CGO_ENABLED=0 GOOS=linux go build -o /main

FROM scratch
COPY --from=build /main /kubernetes-entrypoint
USER 65534
ENTRYPOINT ["/kubernetes-entrypoint"]
