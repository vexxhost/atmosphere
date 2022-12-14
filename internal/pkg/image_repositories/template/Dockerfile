# syntax=docker/dockerfile-upstream:master-labs

ARG BUILDER_IMAGE={{ .BuilderImage }}
ARG RUNTIME_IMAGE={{ .RuntimeImage }}

FROM {{ .BindepImage }}:{{ .BindepImageTag }} AS bindep

FROM ${BUILDER_IMAGE}:{{ .BuilderImageTag }} AS builder
COPY --from=bindep --link /runtime-pip-packages /runtime-pip-packages

FROM ${RUNTIME_IMAGE}:{{ .RuntimeImageTag }} AS runtime
COPY --from=bindep --link /runtime-dist-packages /runtime-dist-packages
COPY --from=builder --link /var/lib/openstack /var/lib/openstack

{{- if eq .Project "nova" }}
ADD https://github.com/novnc/novnc.git#v1.3.0 /usr/share/novnc
{{- else if eq .Project "keystone" }}
RUN <<EOF /bin/bash
  set -xe
  apt-get update
  apt-get install -y --no-install-recommends wget
  wget --no-check-certificate \
    https://github.com/zmartzone/mod_auth_openidc/releases/download/v2.4.12.1/libapache2-mod-auth-openidc_2.4.12.1-1.$(lsb_release -sc)_amd64.deb
  apt-get -y --no-install-recommends install \
    ./libapache2-mod-auth-openidc_2.4.12.1-1.$(lsb_release -sc)_amd64.deb
  rm -rfv \
    ./libapache2-mod-auth-openidc_2.4.12.1-1.$(lsb_release -sc)_amd64.deb
  apt-get purge -y wget
  apt-get clean
  rm -rf /var/lib/apt/lists/*
EOF
{{- end }}
