{{/*
Expand the name of the chart.
*/}}
{{- define "vector.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "vector.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "vector.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "vector.labels" -}}
helm.sh/chart: {{ include "vector.chart" . }}
{{ include "vector.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{ with .Values.commonLabels }}
{{- toYaml . -}}
{{- end }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "vector.selectorLabels" -}}
app.kubernetes.io/name: {{ include "vector.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if or (ne .Values.role "Agent") (ne .Values.role "Aggregator") (ne .Values.role "Stateless-Aggregator") }}
app.kubernetes.io/component: {{ .Values.role }}
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use.
*/}}
{{- define "vector.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "vector.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the appropriate apiVersion for PodDisruptionBudget policy APIs.
*/}}
{{- define "policy.poddisruptionbudget.apiVersion" -}}
{{- if or (.Capabilities.APIVersions.Has "policy/v1/PodDisruptionBudget") (semverCompare ">=1.21" .Capabilities.KubeVersion.Version) -}}
"policy/v1"
{{- else -}}
"policy/v1beta1"
{{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for HPA autoscaling APIs.
*/}}
{{- define "autoscaling.apiVersion" -}}
{{- if or (.Capabilities.APIVersions.Has "autoscaling/v2/HorizontalPodAutoscaler") (semverCompare ">=1.23" .Capabilities.KubeVersion.Version) -}}
"autoscaling/v2"
{{- else -}}
"autoscaling/v2beta2"
{{- end -}}
{{- end -}}

{{/*
Generate an array of ServicePorts based on `.Values.customConfig`.
*/}}
{{- define "vector.ports" -}}
  {{- range $componentKind, $components := .Values.customConfig }}
    {{- if eq $componentKind "sources" }}
      {{- tuple $components "_helper.generatePort" | include "_helper.componentIter" }}
    {{- else if eq $componentKind "sinks" }}
      {{- tuple $components "_helper.generatePort" | include "_helper.componentIter" }}
    {{- else if eq $componentKind "api" }}
      {{- if $components.enabled }}
- name: api
  port: {{ mustRegexFind "[0-9]+$" (get $components "address") }}
  protocol: TCP
  targetPort: {{ mustRegexFind "[0-9]+$" (get $components "address") }}
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}

{{/*
Iterate over the components defined in `.Values.customConfig`.
*/}}
{{- define "_helper.componentIter" -}}
{{- $components := index . 0 }}
{{- $helper := index . 1 }}
  {{- range $id, $options := $components }}
    {{- if (hasKey $options "address") }}
      {{- tuple $id $options | include $helper -}}
    {{- end }}
  {{- end }}
{{- end }}

{{/*
Generate a single ServicePort based on a component configuration.
*/}}
{{- define "_helper.generatePort" -}}
{{- $name := index . 0 | kebabcase -}}
{{- $config := index . 1 -}}
{{- $port := mustRegexFind "[0-9]+$" (get $config "address") -}}
{{- $protocol := default "TCP" (get $config "mode" | upper) }}
- name: {{ $name }}
  port: {{ $port }}
  protocol: {{ $protocol }}
  targetPort: {{ $port }}
{{- if not (mustHas $protocol (list "TCP" "UDP")) }}
{{ fail "Component's `mode` is not a supported protocol, please raise a issue at https://github.com/vectordotdev/vector" }}
{{- end }}
{{- end }}

{{/*
Generate an array of ContainerPorts based on `.Values.customConfig`.
*/}}
{{- define "vector.containerPorts" -}}
  {{- range $componentKind, $components := .Values.customConfig }}
    {{- if eq $componentKind "sources" }}
      {{- tuple $components "_helper.generateContainerPort" | include "_helper.componentIter" }}
    {{- else if eq $componentKind "sinks" }}
      {{- tuple $components "_helper.generateContainerPort" | include "_helper.componentIter" }}
    {{- else if eq $componentKind "api" }}
      {{- if $components.enabled }}
- name: api
  containerPort: {{ mustRegexFind "[0-9]+$" (get $components "address") }}
  protocol: TCP
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}

{{/*
Generate a single ContainerPort based on a component configuration.
*/}}
{{- define "_helper.generateContainerPort" -}}
{{- $name := index . 0 | kebabcase -}}
{{- $config := index . 1 -}}
{{- $port := mustRegexFind "[0-9]+$" (get $config "address") -}}
{{- $protocol := default "TCP" (get $config "mode" | upper) }}
- name: {{ $name | trunc 15 | trimSuffix "-" }}
  containerPort: {{ $port }}
  protocol: {{ $protocol }}
{{- if not (mustHas $protocol (list "TCP" "UDP")) }}
{{ fail "Component's `mode` is not a supported protocol, please raise a issue at https://github.com/vectordotdev/vector" }}
{{- end }}
{{- end }}

{{/*
Print Vector's logo.
*/}}
{{- define "_logo" -}}
{{ print "__   __  __" }}
{{ print "\\ \\ / / / /" }}
{{ print " \\ V / / /  " }}
{{ print "  \\_/  \\/  " }}
{{ print "V E C T O R" }}
{{- end }}

{{/*
Print line divider.
*/}}
{{- define "_divider" -}}
{{ print "--------------------------------------------------------------------------------" }}
{{- end }}

{{/*
Print `vector top` instructions.
*/}}
{{- define "_vector.top" -}}
  {{- if eq "true" (include "_vector.apiEnabled" $) -}}
{{ print "Vector is starting in your cluster. After a few minutes, you can use Vector's" }}
{{ println "API to view internal metrics by running:" }}
  {{- $resource := include "_vector.role" $ -}}
  {{- $url := include "_vector.url" $ }}
  $ kubectl -n {{ $.Release.Namespace }} exec -it {{ $resource }}/{{ include "vector.fullname" $ }} -- vector top {{ $url }}
  {{- else -}}
  {{- $resource := include "_vector.role" $ -}}
{{ print "Vector is starting in your cluster. After a few minutes, you can view Vector's" }}
{{ println "internal logs by running:" }}
  $ kubectl -n {{ $.Release.Namespace }} logs -f {{ $resource }}/{{ include "vector.fullname" $ }}
  {{- end }}
{{- end }}

{{/*
Return `true` if we can determine if Vector's API is enabled.
*/}}
{{- define "_vector.apiEnabled" -}}
  {{- if $.Values.existingConfigMaps -}}
false
  {{- else if $.Values.customConfig -}}
    {{- if $.Values.customConfig.api -}}
      {{- if $.Values.customConfig.api.enabled -}}
true
      {{- end }}
    {{- end }}
  {{- else -}}
true
  {{- end }}
{{- end }}

{{/*
Return Vector's Resource type based on its `.Values.role`.
*/}}
{{- define "_vector.role" -}}
  {{- if eq $.Values.role "Stateless-Aggregator" -}}
deployment
  {{- else if eq $.Values.role "Agent" -}}
daemonset
  {{- else -}}
statefulset
  {{- end -}}
{{- end }}

{{/*
Print the `url` option for the Vector command.
*/}}
{{- define "_vector.url" -}}
  {{- if $.Values.customConfig -}}
    {{- if $.Values.customConfig.api -}}
      {{- if $.Values.customConfig.api.address -}}
{{ print "\\" }}
        --url {{ printf "http://%s/graphql" $.Values.customConfig.api.address }}
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}

{{/*
Configuring Datadog Agents to forward to Vector.
This is really alpha level, and should be refactored
to be more generally usable for other components.
*/}}
{{- define "_configure.datadog" -}}
{{- $hasSourceDatadogAgent := false }}
{{- $sourceDatadogAgentPort := "" }}
{{- $hasTls := "" }}
{{- $protocol := "http" }}
{{- range $componentKind, $configs := .Values.customConfig }}
  {{- if eq $componentKind "sources" }}
    {{- range $componentId, $componentConfig := $configs }}
      {{- if eq (get $componentConfig "type") "datadog_agent" }}
	{{- $hasSourceDatadogAgent = true }}
        {{- $sourceDatadogAgentPort = mustRegexFind "[0-9]+$" (get $componentConfig "address") }}
	{{- if (hasKey $componentConfig "tls") }}
	  {{- $tlsOpts := get $componentConfig "tls" }}
	  {{- $hasTls = get $tlsOpts "enabled" }}
	  {{- if $hasTls }}{{ $protocol = "https" }}{{ end }}
	{{- end }}
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}
{{- if or (not .Values.customConfig) (and .Values.customConfig $hasSourceDatadogAgent) }}
{{- template "_divider" }}

{{ print "datadog_agent:" }}

To forward logs from Datadog Agents deployed with the "datadog" Helm chart,
include the following in the "values.yaml" for your "datadog" chart:

For Datadog Agents version "7.34"/"6.34" or lower:

datadog:
  containerExclude: "name:vector"
  logs:
    enabled: true
    containerCollectAll: true
agents:
  useConfigMap: true
  customAgentConfig:
    kubelet_tls_verify: false
    logs_config:
      {{- if .Values.haproxy.enabled }}
      logs_dd_url: "{{ include "haproxy.fullname" $ }}.{{ $.Release.Namespace }}:{{ $sourceDatadogAgentPort | default "8282" }}"
      {{- else }}
      logs_dd_url: "{{ include "vector.fullname" $ }}.{{ $.Release.Namespace }}:{{ $sourceDatadogAgentPort | default "8282" }}"
      {{- end }}
      {{- if $hasTls }}
      logs_no_ssl: false
      {{- else }}
      logs_no_ssl: true
      {{- end }}
      use_http: true
{{- end }}

For Datadog Agents version "7.35"/"6.35" or greater:

datadog:
  containerExclude: "name:vector"
  logs:
    enabled: true
    containerCollectAll: true
agents:
  useConfigMap: true
  customAgentConfig:
    kubelet_tls_verify: false
    vector:
      logs:
        enabled: true
        {{- if .Values.haproxy.enabled }}
        url: "{{ $protocol }}://{{ include "haproxy.fullname" $ }}.{{ $.Release.Namespace }}:{{ $sourceDatadogAgentPort | default "8282" }}"
        {{- else }}
        url: "{{ $protocol }}://{{ include "vector.fullname" $ }}.{{ $.Release.Namespace }}:{{ $sourceDatadogAgentPort | default "8282" }}"
        {{- end }}
      metrics:
        enabled: true
        {{- if .Values.haproxy.enabled }}
        url: "{{ $protocol }}://{{ include "haproxy.fullname" $ }}.{{ $.Release.Namespace }}:{{ $sourceDatadogAgentPort | default "8282" }}"
        {{- else }}
        url: "{{ $protocol }}://{{ include "vector.fullname" $ }}.{{ $.Release.Namespace }}:{{ $sourceDatadogAgentPort | default "8282" }}"
        {{- end }}
{{- end }}
