{{/*
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/}}

{{/*
abstract: |
  Renders kubernetes anti affinity rules, this function supports both hard
  'requiredDuringSchedulingIgnoredDuringExecution' and soft
  'preferredDuringSchedulingIgnoredDuringExecution' types.
values: |
  pod:
    affinity:
      anti:
        topologyKey:
          default: kubernetes.io/hostname
        type:
          default: requiredDuringSchedulingIgnoredDuringExecution
        weight:
          default: 10
usage: |
  {{ tuple . "appliction_x" "component_y" | include "helm-toolkit.snippets.kubernetes_pod_anti_affinity" }}
return: |
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
          - key: release_group
            operator: In
            values:
            - RELEASE-NAME
          - key: application
            operator: In
            values:
            - appliction_x
          - key: component
            operator: In
            values:
            - component_y
          topologyKey: kubernetes.io/hostname
*/}}

{{- define "helm-toolkit.snippets.kubernetes_pod_anti_affinity._match_expressions" -}}
{{- $envAll := index . "envAll" -}}
{{- $application := index . "application" -}}
{{- $component := index . "component" -}}
{{- $expressionRelease := dict "key" "release_group" "operator" "In"  "values" ( list ( $envAll.Values.release_group | default $envAll.Release.Name ) ) -}}
{{- $expressionApplication := dict "key" "application" "operator" "In"  "values" ( list $application ) -}}
{{- $expressionComponent := dict "key" "component" "operator" "In"  "values" ( list $component ) -}}
{{- list $expressionRelease $expressionApplication $expressionComponent | toYaml }}
{{- end -}}

{{- define "helm-toolkit.snippets.kubernetes_pod_anti_affinity" -}}
{{- $envAll := index . 0 -}}
{{- $application := index . 1 -}}
{{- $component := index . 2 -}}
{{- $antiAffinityType := index $envAll.Values.pod.affinity.anti.type $component | default $envAll.Values.pod.affinity.anti.type.default }}
{{- $antiAffinityKey := index $envAll.Values.pod.affinity.anti.topologyKey $component | default $envAll.Values.pod.affinity.anti.topologyKey.default }}
podAntiAffinity:
{{- $matchExpressions := include "helm-toolkit.snippets.kubernetes_pod_anti_affinity._match_expressions" ( dict "envAll" $envAll "application" $application "component" $component ) -}}
{{- if eq $antiAffinityType "preferredDuringSchedulingIgnoredDuringExecution" }}
  {{ $antiAffinityType }}:
  - podAffinityTerm:
      labelSelector:
        matchExpressions:
{{ $matchExpressions | indent 10 }}
      topologyKey: {{ $antiAffinityKey }}
{{- if  $envAll.Values.pod.affinity.anti.weight }}
    weight: {{ index $envAll.Values.pod.affinity.anti.weight $component | default $envAll.Values.pod.affinity.anti.weight.default }}
{{- else }}
    weight: 10
{{- end -}}
{{- else if eq $antiAffinityType "requiredDuringSchedulingIgnoredDuringExecution" }}
  {{ $antiAffinityType }}:
  - labelSelector:
      matchExpressions:
{{ $matchExpressions | indent 8 }}
    topologyKey: {{ $antiAffinityKey }}
{{- end -}}
{{- end -}}
