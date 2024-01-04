# syntax=docker/dockerfile-upstream:master-labs

ARG BUILDER_IMAGE
ARG RUNTIME_IMAGE

FROM {{ .BindepImage }}:{{ .BindepImageTag }} AS bindep

FROM ${BUILDER_IMAGE} AS builder
COPY --from=bindep --link /runtime-pip-packages /runtime-pip-packages

FROM ${RUNTIME_IMAGE} AS runtime
COPY --from=bindep --link /runtime-dist-packages /runtime-dist-packages
COPY --from=builder --link /var/lib/openstack /var/lib/openstack

{{- if eq .Project "magnum" }}
COPY --from=docker.io/alpine/helm:3.11.2 /usr/bin/helm /usr/local/bin/helm
COPY --from=gcr.io/go-containerregistry/crane /ko-app/crane /usr/local/bin/crane
{{- end }}
