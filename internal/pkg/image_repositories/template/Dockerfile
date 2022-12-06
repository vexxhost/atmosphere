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
  set -e
  source /etc/lsb-release
  apt-get update
  apt-get install -y --no-install-recommends wget apache2
  wget --no-check-certificate \
    https://github.com/zmartzone/mod_oauth2/releases/download/v3.2.2/libapache2-mod-oauth2_3.2.2-1.${DISTRIB_CODENAME}+1_amd64.deb \
    https://github.com/zmartzone/liboauth2/releases/download/v1.4.3/liboauth2_1.4.3-1.${DISTRIB_CODENAME}+1_amd64.deb
  apt-get -y --no-install-recommends install \
    ./libapache2-mod-oauth2_3.2.2-1.${DISTRIB_CODENAME}+1_amd64.deb \
    ./liboauth2_1.4.3-1.${DISTRIB_CODENAME}+1_amd64.deb
  a2enmod oauth2
  rm -rfv \
    ./libapache2-mod-oauth2_3.2.2-1.${DISTRIB_CODENAME}+1_amd64.deb \
    ./liboauth2_1.4.3-1.${DISTRIB_CODENAME}+1_amd64.deb
  apt-get purge -y wget
  apt-get clean
  rm -rf /var/lib/apt/lists/*
EOF
{{- end }}
