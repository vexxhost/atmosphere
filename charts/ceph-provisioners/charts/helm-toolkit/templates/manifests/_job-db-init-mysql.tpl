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

# This function creates a manifest for db creation and user management.
# It can be used in charts dict created similar to the following:
# {- $dbToInitJob := dict "envAll" . "serviceName" "senlin" -}
# { $dbToInitJob | include "helm-toolkit.manifests.job_db_init_mysql" }
#
# If the service does not use oslo then the db can be managed with:
# {- $dbToInit := dict "inputType" "secret" "adminSecret" .Values.secrets.oslo_db.admin "userSecret" .Values.secrets.oslo_db.horizon -}
# {- $dbToInitJob := dict "envAll" . "serviceName" "horizon" "dbToInit" $dbToInit -}
# { $dbToInitJob | include "helm-toolkit.manifests.job_db_init_mysql" }

{{- define "helm-toolkit.manifests.job_db_init_mysql" -}}
{{- $envAll := index . "envAll" -}}
{{- $serviceName := index . "serviceName" -}}
{{- $jobAnnotations := index . "jobAnnotations" -}}
{{- $jobLabels := index . "jobLabels" -}}
{{- $nodeSelector := index . "nodeSelector" | default ( dict $envAll.Values.labels.job.node_selector_key $envAll.Values.labels.job.node_selector_value ) -}}
{{- $configMapBin := index . "configMapBin" | default (printf "%s-%s" $serviceName "bin" ) -}}
{{- $configMapEtc := index . "configMapEtc" | default (printf "%s-%s" $serviceName "etc" ) -}}
{{- $dbToInit := index . "dbToInit" | default ( dict "adminSecret" $envAll.Values.secrets.oslo_db.admin "configFile" (printf "/etc/%s/%s.conf" $serviceName $serviceName ) "logConfigFile" (printf "/etc/%s/logging.conf" $serviceName ) "configDbSection" "database" "configDbKey" "connection" ) -}}
{{- $dbsToInit := default (list $dbToInit) (index . "dbsToInit") }}
{{- $secretBin := index . "secretBin" -}}
{{- $backoffLimit := index . "backoffLimit" | default "1000" -}}
{{- $activeDeadlineSeconds := index . "activeDeadlineSeconds" -}}
{{- $serviceNamePretty := $serviceName | replace "_" "-" -}}
{{- $dbAdminTlsSecret := index . "dbAdminTlsSecret" | default "" -}}

{{- $serviceAccountName := printf "%s-%s" $serviceNamePretty "db-init" }}
{{ tuple $envAll "db_init" $serviceAccountName | include "helm-toolkit.snippets.kubernetes_pod_rbac_serviceaccount" }}
---
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ printf "%s-%s" $serviceNamePretty "db-init" | quote }}
  annotations:
{{- if $jobAnnotations }}
{{ toYaml $jobAnnotations | indent 4 }}
{{- end }}
spec:
  backoffLimit: {{ $backoffLimit }}
{{- if $activeDeadlineSeconds }}
  activeDeadlineSeconds: {{ $activeDeadlineSeconds }}
{{- end }}
  template:
    metadata:
      labels:
{{ tuple $envAll $serviceName "db-init" | include "helm-toolkit.snippets.kubernetes_metadata_labels" | indent 8 }}
{{- if $jobLabels }}
{{ toYaml $jobLabels | indent 8 }}
{{- end }}
      annotations:
{{ tuple $envAll | include "helm-toolkit.snippets.release_uuid" | indent 8 }}
    spec:
      serviceAccountName: {{ $serviceAccountName }}
      restartPolicy: OnFailure
      nodeSelector:
{{ toYaml $nodeSelector | indent 8 }}
      initContainers:
{{ tuple $envAll "db_init" list | include "helm-toolkit.snippets.kubernetes_entrypoint_init_container" | indent 8 }}
      containers:
{{- range $key1, $dbToInit := $dbsToInit }}
{{ $dbToInitType := default "oslo" $dbToInit.inputType }}
        - name: {{ printf "%s-%s-%d" $serviceNamePretty "db-init" $key1 | quote }}
          image: {{ $envAll.Values.images.tags.db_init }}
          imagePullPolicy: {{ $envAll.Values.images.pull_policy }}
{{ tuple $envAll $envAll.Values.pod.resources.jobs.db_init | include "helm-toolkit.snippets.kubernetes_resources" | indent 10 }}
          env:
            - name: ROOT_DB_CONNECTION
              valueFrom:
                secretKeyRef:
                  name: {{ $dbToInit.adminSecret | quote }}
                  key: DB_CONNECTION
{{- if eq $dbToInitType "oslo" }}
            - name: OPENSTACK_CONFIG_FILE
              value: {{ $dbToInit.configFile | quote }}
            - name: OPENSTACK_CONFIG_DB_SECTION
              value: {{ $dbToInit.configDbSection | quote }}
            - name: OPENSTACK_CONFIG_DB_KEY
              value: {{ $dbToInit.configDbKey | quote }}
{{- end }}
{{- if eq $dbToInitType "secret" }}
            - name: DB_CONNECTION
              valueFrom:
                secretKeyRef:
                  name: {{ $dbToInit.userSecret | quote }}
                  key: DB_CONNECTION
{{- end }}
{{- if $envAll.Values.manifests.certificates }}
            - name: MARIADB_X509
              value: "REQUIRE X509"
{{- end }}
          command:
            - /tmp/db-init.py
          volumeMounts:
            - name: pod-tmp
              mountPath: /tmp
            - name: db-init-sh
              mountPath: /tmp/db-init.py
              subPath: db-init.py
              readOnly: true
{{- if eq $dbToInitType "oslo" }}
            - name: etc-service
              mountPath: {{ dir $dbToInit.configFile | quote }}
            - name: db-init-conf
              mountPath: {{ $dbToInit.configFile | quote }}
              subPath: {{ base $dbToInit.configFile | quote }}
              readOnly: true
            - name: db-init-conf
              mountPath: {{ $dbToInit.logConfigFile | quote }}
              subPath: {{ base $dbToInit.logConfigFile | quote }}
              readOnly: true
{{- end }}
{{- if $envAll.Values.manifests.certificates }}
{{- dict "enabled" $envAll.Values.manifests.certificates "name" $dbAdminTlsSecret "path" "/etc/mysql/certs" | include "helm-toolkit.snippets.tls_volume_mount" | indent 12 }}
{{- end }}
{{- end }}
      volumes:
        - name: pod-tmp
          emptyDir: {}
        - name: db-init-sh
{{- if $secretBin }}
          secret:
            secretName: {{ $secretBin | quote }}
            defaultMode: 0555
{{- else }}
          configMap:
            name: {{ $configMapBin | quote }}
            defaultMode: 0555
{{- end }}
{{- if $envAll.Values.manifests.certificates }}
{{- dict "enabled" $envAll.Values.manifests.certificates "name" $dbAdminTlsSecret | include "helm-toolkit.snippets.tls_volume" | indent 8 }}
{{- end }}
{{- $local := dict "configMapBinFirst" true -}}
{{- range $key1, $dbToInit := $dbsToInit }}
{{- $dbToInitType := default "oslo" $dbToInit.inputType }}
{{- if and (eq $dbToInitType "oslo") $local.configMapBinFirst }}
{{- $_ := set $local "configMapBinFirst" false }}
        - name: etc-service
          emptyDir: {}
        - name: db-init-conf
          secret:
            secretName: {{ $configMapEtc | quote }}
            defaultMode: 0444
{{- end -}}
{{- end -}}
{{- end -}}
