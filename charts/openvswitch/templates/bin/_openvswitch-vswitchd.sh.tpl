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
COMMAND="${@:-start}"

DPDK_ENABLED=false
OVS_CONFIG=""
OVS_CONFIG_FILE=/tmp/ovs.conf
OVS_PID=/run/openvswitch/ovs-vswitchd.pid
OVS_SOCKET=/run/openvswitch/db.sock
if [ -f ${OVS_CONFIG_FILE} ]; then
  OVS_CONFIG=$(cat ${OVS_CONFIG_FILE})
else
  echo "Cannot find ${OVS_CONFIG_FILE}" 1>&2
  exit
fi

function get_ovs_config_value {
  values=${@:1:$#-1}
  filter=${!#}
  value=$(echo ${values} | jq -r ${filter})
  if [[ "${value}" == "null" ]]; then
    echo ""
  else
    echo "${value}"
  fi
}

NOVA_UID=$(get_ovs_config_value ${OVS_CONFIG} '.user.nova.uid')

function start () {
  t=0
  while [ ! -e "${OVS_SOCKET}" ] ; do
      echo "waiting for ovs socket $sock"
      sleep 1
      t=$(($t+1))
      if [ $t -ge 10 ] ; then
          echo "no ovs socket, giving up"
          exit 1
      fi
  done

  # aligning this with neutron init scripts referencing config from file instead of writing
  # config to script directly
  if [[ $(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.enabled') == "true" ]]; then
    DPDK_ENABLED=true
    HUGEPAGE_DIR=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.hugepages_mountpath')
    SOCKET_MEMORY=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.socket_memory')
    VHOST_SOCK_DIR=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.vhostuser_socket_dir')

    # Create vhostuser directory and grant nova user (default UID 42424) access
    # permissions.
    mkdir -p /run/openvswitch/${VHOST_SOCK_DIR}
    chown ${NOVA_UID}.${NOVA_UID} /run/openvswitch/${VHOST_SOCK_DIR}

    ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:dpdk-hugepage-dir=${HUGEPAGE_DIR}
    ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:dpdk-socket-mem=${SOCKET_MEMORY}
    ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:vhost-sock-dir=${VHOST_SOCK_DIR}

    MEM_CHANNELS=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.mem_channels')
    if [[ -n ${MEM_CHANNELS} ]]; then
      ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:dpdk-mem-channels=${MEM_CHANNELS}
    fi

    PMD_CPU_MASK=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.pmd_cpu_mask')
    if [[ -n ${PMD_CPU_MASK} ]]; then
      ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:pmd-cpu-mask=${PMD_CPU_MASK}
    fi

    LCORE_MASK=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.lcore_mask')
    if [[ -n ${LCORE_MASK} ]]; then
      ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:dpdk-lcore-mask=${LCORE_MASK}
    fi

    VHOST_IOMMU_SUPPORT=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.vhost_iommu_support')
    if [[ -n ${VHOST_IOMMU_SUPPORT} ]]; then
      ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:vhost-iommu-support=${VHOST_IOMMU_SUPPORT}
    fi

    USERSPACE_TSO_ENABLE=$(get_ovs_config_value ${OVS_CONFIG} '.ovs_dpdk.userspace_tso_enable')
    if [[ -n ${USERSPACE_TSO_ENABLE} ]]; then
      ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:userspace-tso-enable=${USERSPACE_TSO_ENABLE}
    fi

    ovs-vsctl --db=unix:${OVS_SOCKET} --no-wait set Open_vSwitch . other_config:dpdk-init=true
  fi

  # No need to create the cgroup if lcore_mask or pmd_cpu_mask is not set.
  if [[ -n ${PMD_CPU_MASK} || -n ${LCORE_MASK} ]]; then
      if [ "$(stat -fc %T /sys/fs/cgroup/)" = "cgroup2fs" ]; then
          # Setup Cgroups to use when breaking out of Kubernetes defined groups
          mkdir -p /sys/fs/cgroup/osh-openvswitch
          target_mems="/sys/fs/cgroup/osh-openvswitch/cpuset.mems"
          target_cpus="/sys/fs/cgroup/osh-openvswitch/cpuset.cpus"
          touch $target_mems
          touch $target_cpus

          # Ensure the write target for the for cpuset.mem for the pod exists
          if [[ -f "$target_mems" && -f "$target_cpus" ]]; then
            # Write cpuset.mem and cpuset.cpus for new cgroup and add current task to new cgroup
            cat /sys/fs/cgroup/cpuset.mems.effective > "$target_mems"
            cat /sys/fs/cgroup/cpuset.cpus.effective > "$target_cpus"
            echo $$ > /sys/fs/cgroup/osh-openvswitch/cgroup.procs
          else
            echo "ERROR: Could not find write target for either cpuset.mems: $target_mems or cpuset.cpus: $target_cpus"
          fi
      else
          # Setup Cgroups to use when breaking out of Kubernetes defined groups
          mkdir -p /sys/fs/cgroup/cpuset/osh-openvswitch
          target_mems="/sys/fs/cgroup/cpuset/osh-openvswitch/cpuset.mems"
          target_cpus="/sys/fs/cgroup/cpuset/osh-openvswitch/cpuset.cpus"

          # Ensure the write target for the for cpuset.mem for the pod exists
          if [[ -f "$target_mems" && -f "$target_cpus" ]]; then
            # Write cpuset.mem and cpuset.cpus for new cgroup and add current task to new cgroup
            cat /sys/fs/cgroup/cpuset/cpuset.mems > "$target_mems"
            cat /sys/fs/cgroup/cpuset/cpuset.cpus > "$target_cpus"
            echo $$ > /sys/fs/cgroup/cpuset/osh-openvswitch/tasks
          else
            echo "ERROR: Could not find write target for either cpuset.mems: $target_mems or cpuset.cpus: $target_cpus"
          fi
      fi
  fi

  exec /usr/sbin/ovs-vswitchd unix:${OVS_SOCKET} \
          -vconsole:emer \
          -vconsole:err \
          -vconsole:info \
          --pidfile=${OVS_PID} \
          --mlockall
}

function stop () {
  PID=$(cat $OVS_PID)
  ovs-appctl -T1 -t /run/openvswitch/ovs-vswitchd.${PID}.ctl exit
}

find_latest_ctl_file() {
    latest_file=""
    latest_file=$(ls -lt /run/openvswitch/*.ctl | awk 'NR==1 {if ($3 == "$(get_ovs_config_value ${OVS_CONFIG} '.poststart.rootUser')") print $NF}')

    echo "${latest_file}"
}

function poststart () {
  # This enables the usage of 'ovs-appctl' from neutron-ovs-agent pod.

  # Wait for potential new ctl file before continuing
  timeout=$(get_ovs_config_value ${OVS_CONFIG} '.poststart.timeout')
  start_time=$(date +%s)
  while true; do
      latest_ctl_file=$(find_latest_ctl_file)
      if [ -n "$latest_ctl_file" ]; then
          break
      fi
      current_time=$(date +%s)
      if (( current_time - start_time >= timeout )); then
          break
      fi
      sleep 1
  done

  until [ -f $OVS_PID ]
  do
      echo "Waiting for file $OVS_PID"
      sleep 1
  done

  PID=$(cat ${OVS_PID})
  OVS_CTL=/run/openvswitch/ovs-vswitchd.${PID}.ctl

  until [ -S ${OVS_CTL} ]
  do
      echo "Waiting for file ${OVS_CTL}"
      sleep 1
  done
  chown ${NOVA_UID}.${NOVA_UID} ${OVS_CTL}

<<<<<<< HEAD
  2>&1 /tmp/openvswitch-nic-init.sh > /var/tmp/openvswitch-nic-init.log
=======
  /tmp/openvswitch-nic-init.sh > /var/tmp/${POD_NAME}-vswitchd-nic-init.log 2>&1
>>>>>>> cd87f018 (convert script to reference configmap instead of config written into script)

  POSTSTART=$(get_ovs_config_value ${OVS_CONFIG} '.poststart.extraCommand')
  if [[ -n ${POSTSTART} ]]; then
    bash -c ${POSTSTART}
  fi

}

$COMMAND
