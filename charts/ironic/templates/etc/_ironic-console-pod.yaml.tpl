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

{{- $consoleNamespace := required "console.namespace is required when the Kubernetes console provider is enabled" .Values.console.namespace }}

apiVersion: v1
kind: Secret
metadata:
  name: "ironic-console-{{ "{{ uuid }}" }}"
  namespace: {{ $consoleNamespace }}
  labels:
    app: ironic
    component: ironic-console
    conductor: "{{ "{{ conductor }}" }}"
    app.kubernetes.io/instance: {{ .Release.Name | quote }}
    app.kubernetes.io/managed-by: ironic
stringData:
  app-info: |-
    {{ "{{ app_info }}" }}
---
apiVersion: v1
kind: Pod
metadata:
  name: "ironic-console-{{ "{{ uuid }}" }}"
  namespace: {{ $consoleNamespace }}
  labels:
    app: ironic
    component: ironic-console
    conductor: "{{ "{{ conductor }}" }}"
    app.kubernetes.io/instance: {{ .Release.Name | quote }}
    app.kubernetes.io/managed-by: ironic
{{- with .Values.console.pod.annotations }}
  annotations:
{{ toYaml . | indent 4 }}
{{- end }}
spec:
  automountServiceAccountToken: false
  enableServiceLinks: {{ .Values.console.pod.enableServiceLinks }}
{{- with .Values.console.pod.imagePullSecrets }}
  imagePullSecrets:
{{ toYaml . | indent 4 }}
{{- end }}
{{- with .Values.console.pod.nodeSelector }}
  nodeSelector:
{{ toYaml . | indent 4 }}
{{- end }}
{{- with .Values.console.pod.affinity }}
  affinity:
{{ toYaml . | indent 4 }}
{{- end }}
{{- with .Values.console.pod.tolerations }}
  tolerations:
{{ toYaml . | indent 4 }}
{{- end }}
{{- with .Values.console.pod.topologySpreadConstraints }}
  topologySpreadConstraints:
{{ toYaml . | indent 4 }}
{{- end }}
{{- with .Values.console.pod.priorityClassName }}
  priorityClassName: {{ . | quote }}
{{- end }}
{{- with .Values.console.pod.runtimeClassName }}
  runtimeClassName: {{ . | quote }}
{{- end }}
{{- with .Values.console.pod.securityContext }}
  securityContext:
{{ toYaml . | indent 4 }}
{{- end }}
  containers:
    - name: console
      image: "{{ "{{ image }}" }}"
      imagePullPolicy: {{ .Values.images.pull_policy | quote }}
{{- with .Values.console.container.ports }}
      ports:
{{ toYaml . | indent 8 }}
{{- end }}
{{- with .Values.console.container.startupProbe }}
      startupProbe:
{{ toYaml . | indent 8 }}
{{- end }}
{{- with .Values.console.container.readinessProbe }}
      readinessProbe:
{{ toYaml . | indent 8 }}
{{- end }}
{{- with .Values.console.container.livenessProbe }}
      livenessProbe:
{{ toYaml . | indent 8 }}
{{- end }}
{{- with .Values.console.container.securityContext }}
      securityContext:
{{ toYaml . | indent 8 }}
{{- end }}
      resources:
{{ toYaml .Values.console.container.resources | indent 8 }}
{{- with .Values.console.container.volumeMounts }}
      volumeMounts:
{{ toYaml . | indent 8 }}
{{- end }}
      env:
        - name: APP
          value: "{{ "{{ app }}" }}"
        - name: READ_ONLY
          value: "{{ "{{ read_only }}" }}"
        - name: APP_INFO
          valueFrom:
            secretKeyRef:
              name: "ironic-console-{{ "{{ uuid }}" }}"
              key: app-info
{{- with .Values.console.container.env }}
{{ toYaml . | indent 8 }}
{{- end }}
{{- with .Values.console.volumes }}
  volumes:
{{ toYaml . | indent 4 }}
{{- end }}
