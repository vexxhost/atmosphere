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

apiVersion: v1
kind: Secret
metadata:
  name: "ironic-console-{{ "{{ uuid }}" }}"
  namespace: {{ .Release.Namespace }}
  labels:
    app: ironic
    component: ironic-console
    conductor: "{{ "{{ conductor }}" }}"
stringData:
  app-info: '{{ "{{ app_info }}" }}'
---
apiVersion: v1
kind: Pod
metadata:
  name: "ironic-console-{{ "{{ uuid }}" }}"
  namespace: {{ .Release.Namespace }}
  labels:
    app: ironic
    component: ironic-console
    conductor: "{{ "{{ conductor }}" }}"
spec:
  containers:
    - name: x11vnc
      image: "{{ "{{ image }}" }}"
      imagePullPolicy: Always
      ports:
        - containerPort: 5900
      resources:
        requests:
          cpu: 250m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 1024Mi
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
