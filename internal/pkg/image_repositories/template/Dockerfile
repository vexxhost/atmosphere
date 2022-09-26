# syntax=docker/dockerfile-upstream:master-labs

FROM {{ .BindepImage }}:{{ .BindepImageTag }} AS bindep

FROM {{ .BuilderImage }}:{{ .BuilderImageTag }} AS builder
COPY --from=bindep --link /runtime-pip-packages /runtime-pip-packages

FROM {{ .RuntimeImage }}:{{ .RuntimeImageTag }} AS runtime
COPY --from=bindep --link /runtime-dist-packages /runtime-dist-packages
COPY --from=builder --link /var/lib/openstack /var/lib/openstack

{{- if eq .Project "nova" }}
ADD https://github.com/novnc/novnc.git#v1.3.0 /usr/share/novnc
{{- end }}
