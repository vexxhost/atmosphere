#!/bin/bash

{{/*
Copyright (c) 2023 VEXXHOST, Inc.

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

cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ${POD_NAME}-${TYPE}
  namespace: ${POD_NAMESPACE}
  ownerReferences:
    - apiVersion: v1
      kind: Pod
      name: ${POD_NAME}
      uid: ${POD_UID}
spec:
  secretName: ${POD_NAME}-${TYPE}
  commonName: ${POD_IP}
  usages:
  - client auth
  - server auth
  dnsNames:
  - ${HOSTNAME}
  ipAddresses:
  - ${POD_IP}
  issuerRef:
    kind: Issuer
    name: libvirt-${TYPE}
EOF

kubectl -n ${POD_NAMESPACE} wait --for=condition=Ready --timeout=300s \
  certificate/${POD_NAME}-${TYPE}

# NOTE(mnaser): cert-manager does not clean-up the secrets when the certificate
#               is deleted, so we should add an owner reference to the secret
#               to ensure that it is cleaned up when the pod is deleted.
kubectl -n ${POD_NAMESPACE} patch secret ${POD_NAME}-${TYPE} \
  --type=json -p='[{"op": "add", "path": "/metadata/ownerReferences", "value": [{"apiVersion": "v1", "kind": "Pod", "name": "'${POD_NAME}'", "uid": "'${POD_UID}'"}]}]'

kubectl -n ${POD_NAMESPACE} get secret ${POD_NAME}-${TYPE} -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/${TYPE}.crt
kubectl -n ${POD_NAMESPACE} get secret ${POD_NAME}-${TYPE} -o jsonpath='{.data.tls\.key}' | base64 -d > /tmp/${TYPE}.key
kubectl -n ${POD_NAMESPACE} get secret ${POD_NAME}-${TYPE} -o jsonpath='{.data.ca\.crt}' | base64 -d > /tmp/${TYPE}-ca.crt
