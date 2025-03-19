#!/bin/bash

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

set -ex

if [ ! -f /etc/tempest/test-blacklist ]; then
  touch /etc/tempest/test-blacklist
fi

if [ ! -f /etc/tempest/test-whitelist ]; then
  touch /etc/tempest/test-whitelist
fi

{{ if .Values.conf.cleanup.previous_run }}
tempest cleanup --prefix {{ .Values.conf.cleanup.prefix_name }}
{{ end }}

{{ if .Values.conf.cleanup.enabled }}
mkdir -p /var/lib/tempest/saved_state
pushd /var/lib/tempest/saved_state
tempest cleanup --init-saved-state

if [ "true" == "{{- .Values.conf.cleanup.force -}}" ]; then
trap "tempest cleanup; exit" 1 ERR
fi
popd
{{- end }}

{{ if .Values.conf.subunit_output }}
tempest run --include-list /etc/tempest/test-whitelist --exclude-list /etc/tempest/test-blacklist --config-file /etc/tempest/tempest.conf -w 4 --smoke --subunit > /var/lib/tempest/data/results.subunit
cat /var/lib/tempest/data/results.subunit | subunit2junitxml -o /var/lib/tempest/data/results.junit || echo converted subunit file
{{ else }}
{{ .Values.conf.script }}
{{- end }}

{{ if and .Values.conf.cleanup.enabled (not .Values.conf.cleanup.previous_run) }}
mkdir -p /var/lib/tempest/saved_state
pushd /var/lib/tempest/saved_state
tempest cleanup
popd
{{- end }}
