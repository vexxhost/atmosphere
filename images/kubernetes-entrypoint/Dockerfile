# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang:1.21 AS build
ARG KUBERNETES_ENTRYPOINT_GIT_REF=4fbcf7ce324dc66e78480f73035e31434cfea1e8
ADD https://opendev.org/airship/kubernetes-entrypoint.git#${KUBERNETES_ENTRYPOINT_GIT_REF} /src
WORKDIR /src
RUN CGO_ENABLED=0 GOOS=linux go build -o /main

FROM scratch
COPY --from=build /main /kubernetes-entrypoint
USER 65534
ENTRYPOINT ["/kubernetes-entrypoint"]
