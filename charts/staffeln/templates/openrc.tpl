{{/*
Defines openrc for Staffeln.
*/}}

{{- define "staffeln.templates.openrc" -}}
export OS_IDENTITY_API_VERSION=3
export OS_AUTH_TYPE=password
export OS_INTERFACE=internal
{{- if .Values.conf.clouds.clouds.envvars.auth.auth_url }}
export OS_AUTH_URL="{{ .Values.conf.clouds.clouds.envvars.auth.auth_url }}"
{{- end }}
{{- if .Values.conf.clouds.clouds.envvars.auth.project_name }}
export OS_PROJECT_NAME={{ .Values.conf.clouds.clouds.envvars.auth.project_name }}
{{- end }}
{{- if .Values.conf.clouds.clouds.envvars.auth.project_domain_name }}
export OS_PROJECT_DOMAIN_NAME={{ .Values.conf.clouds.clouds.envvars.auth.project_domain_name }}
{{- end }}
{{- if .Values.conf.clouds.clouds.envvars.region_name }}
export OS_REGION_NAME="{{ .Values.conf.clouds.clouds.envvars.region_name }}"
{{- end }}
{{- if .Values.conf.clouds.clouds.envvars.auth.user_domain_name }}
export OS_USER_DOMAIN_NAME={{ .Values.conf.clouds.clouds.envvars.auth.user_domain_name }}
{{- end }}
{{- if .Values.conf.clouds.clouds.envvars.auth.password }}
export OS_PASSWORD="{{ .Values.conf.clouds.clouds.envvars.auth.password }}"
{{- end }}
{{- if .Values.conf.clouds.clouds.envvars.auth.username }}
export OS_USERNAME="{{ .Values.conf.clouds.clouds.envvars.auth.username }}"
{{- end }}
{{- end -}}
