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

set -x
if [ "x$STORAGE_BACKEND" == "xcinder.volume.drivers.rbd.RBDDriver" ]; then
  SECRET=$(mktemp --suffix .yaml)
  KEYRING=$(mktemp --suffix .keyring)
  function cleanup {
      rm -f ${SECRET} ${KEYRING}
  }
  trap cleanup EXIT
fi

set -ex
if [ "x$STORAGE_BACKEND" == "xcinder.volume.drivers.rbd.RBDDriver" ]; then
  ceph -s
  function ensure_pool () {
    ceph osd pool stats $1 || ceph osd pool create $1 $2
    if [[ $(ceph mgr versions | awk '/version/{print $3}' | cut -d. -f1) -ge 12 ]]; then
        ceph osd pool application enable $1 $3
    fi
    size_protection=$(ceph osd pool get $1 nosizechange | cut -f2 -d: | tr -d '[:space:]')
    ceph osd pool set $1 nosizechange 0
    ceph osd pool set $1 size ${RBD_POOL_REPLICATION} --yes-i-really-mean-it
    ceph osd pool set $1 nosizechange ${size_protection}
    ceph osd pool set $1 crush_rule "${RBD_POOL_CRUSH_RULE}"
  }

  function ensure_ec_profile () {
    local name=$1 k=$2 m=$3 device_class=$4 failure_domain=$5
    if ceph osd erasure-code-profile get $name 2>/dev/null; then
      echo "EC profile $name already exists"
    else
      ceph osd erasure-code-profile set $name \
        k=$k m=$m \
        crush-device-class=$device_class \
        crush-failure-domain=$failure_domain
    fi
  }

  function ensure_ec_data_pool () {
    local pool_name=$1 profile=$2 app_name=$3
    if ceph osd pool stats $pool_name 2>/dev/null; then
      echo "EC data pool $pool_name already exists"
    else
      # Ceph auto-creates CRUSH rule from EC profile settings
      ceph osd pool create $pool_name erasure $profile
    fi

    if [[ $(ceph mgr versions | awk '/version/{print $3}' | cut -d. -f1) -ge 12 ]]; then
      ceph osd pool application enable $pool_name $app_name
    fi

    ceph osd pool set $pool_name allow_ec_overwrites true
  }

  function ensure_ec_metadata_pool () {
    local pool_name=$1 chunk_size=$2 app_name=$3 replication=$4 crush_rule=$5

    ceph osd pool stats $pool_name || ceph osd pool create $pool_name $chunk_size

    if [[ $(ceph mgr versions | awk '/version/{print $3}' | cut -d. -f1) -ge 12 ]]; then
      ceph osd pool application enable $pool_name $app_name
    fi

    size_protection=$(ceph osd pool get $pool_name nosizechange | cut -f2 -d: | tr -d '[:space:]')
    ceph osd pool set $pool_name nosizechange 0
    ceph osd pool set $pool_name size $replication --yes-i-really-mean-it
    ceph osd pool set $pool_name nosizechange ${size_protection}
    ceph osd pool set $pool_name crush_rule "$crush_rule"
  }

  if [ "x$EC_ENABLED" == "xtrue" ]; then
    ensure_ec_profile "${EC_PROFILE_NAME}" "${EC_PROFILE_K}" "${EC_PROFILE_M}" \
      "${EC_PROFILE_DEVICE_CLASS}" "${EC_PROFILE_FAILURE_DOMAIN}"

    ensure_ec_data_pool "${EC_DATA_POOL_NAME}" "${EC_PROFILE_NAME}" "${EC_POOL_APP_NAME}"

    ensure_ec_metadata_pool "${RBD_POOL_NAME}" "${EC_METADATA_POOL_CHUNK_SIZE}" \
      "${EC_POOL_APP_NAME}" "${EC_METADATA_POOL_REPLICATION}" "${EC_METADATA_POOL_CRUSH_RULE}"
  else
    ensure_pool ${RBD_POOL_NAME} ${RBD_POOL_CHUNK_SIZE} ${RBD_POOL_APP_NAME}
  fi

  if USERINFO=$(ceph auth get client.${RBD_POOL_USER}); then
    echo "Cephx user client.${RBD_POOL_USER} already exist."
    echo "Update its cephx caps"
    ceph auth caps client.${RBD_POOL_USER} \
      mon "profile rbd" \
      osd "profile rbd"
    ceph auth get client.${RBD_POOL_USER} -o ${KEYRING}
  else
    #NOTE(JCL): Restrict Cinder permissions to what is needed. MON Read only and RBD access to Cinder pool only.
    ceph auth get-or-create client.${RBD_POOL_USER} \
      mon "profile rbd" \
      osd "profile rbd" \
      -o ${KEYRING}
  fi

  ENCODED_KEYRING=$(sed -n 's/^[[:blank:]]*key[[:blank:]]\+=[[:blank:]]\(.*\)/\1/p' ${KEYRING} | base64 -w0)
  cat > ${SECRET} <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: "${RBD_POOL_SECRET}"
type: kubernetes.io/rbd
data:
  key: $( echo ${ENCODED_KEYRING} )
EOF
  kubectl apply --namespace ${NAMESPACE} -f ${SECRET}

fi
