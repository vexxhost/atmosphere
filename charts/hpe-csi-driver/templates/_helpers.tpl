{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "hpe-csi-storage.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "hpe-csi-storage.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "hpe-csi-storage.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
CHAP secret validation
*/}}
{{- define "hpe-csi-storage.chapSecretValidation" -}}
{{- if not (empty .Values.iscsi.chapSecretName) }}
  {{- $secret := lookup "v1" "Secret" .Release.Namespace .Values.iscsi.chapSecretName }}
  {{- if not $secret }}
    {{- fail (printf "Secret %s not found in namespace %s" .Values.iscsi.chapSecretName .Release.Namespace) }}
  {{- end }}

  {{- $username := index $secret.data "chapUser" | b64dec }}
  {{- $password := index $secret.data "chapPassword" | b64dec }}

  {{- if or (empty $username) (empty $password) }}
    {{- fail "Username or password cannot be empty." }}
  {{- end }}

  {{- $chapUserValidationPattern := "^[a-zA-Z0-9][a-zA-Z0-9\\-:.]{0,63}$" }}
  {{- $chapPasswordValidationPattern := "^[a-zA-Z0-9!#$%()*+,-./:<>?@_{}|~]{12,16}$" }}

   {{- if not (regexMatch $chapUserValidationPattern $username) }}
    {{- fail (printf "Username does not match the required pattern: %s" $chapUserValidationPattern) }}
  {{- end }}

  {{- if not (regexMatch $chapPasswordValidationPattern $password) }}
    {{- fail (printf "Password does not match the required pattern: %s" $chapPasswordValidationPattern) }}
  {{- end }}

{{- end }}
{{- end -}}

{{- define "empty" -}}
{{- eq . "" -}}
{{- end -}}
