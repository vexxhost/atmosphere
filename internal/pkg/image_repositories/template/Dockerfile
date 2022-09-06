# syntax=docker/dockerfile:1.4

FROM {{ .BindepImage }}:{{ .BindepImageTag }} AS bindep

FROM {{ .BuilderImage }}:{{ .BuilderImageTag }} AS builder
COPY --from=bindep --link /runtime-pip-packages /runtime-pip-packages

FROM {{ .RuntimeImage }}:{{ .RuntimeImageTag }} AS runtime
COPY --from=bindep --link /runtime-dist-packages /runtime-dist-packages
COPY --from=builder --link /var/lib/openstack /var/lib/openstack
