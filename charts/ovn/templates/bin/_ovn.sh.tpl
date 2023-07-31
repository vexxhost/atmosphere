#!/bin/bash
# set -x

bracketify() { case "$1" in *:*) echo "[$1]" ;; *) echo "$1" ;; esac }

OVN_NORTH="tcp:${OVN_NB_DB_SERVICE_HOST}:${OVN_NB_DB_SERVICE_PORT_OVN_NB_DB}"
OVN_SOUTH="tcp:${OVN_SB_DB_SERVICE_HOST}:${OVN_SB_DB_SERVICE_PORT_OVN_SB_DB}"

# This script is the entrypoint to the image.
# Supports version 3 daemonsets
#    $1 is the daemon to start.
#        In version 3 each process has a separate container. Some daemons start
#        more than 1 process. Also, where possible, output is to stdout and
#        The script waits for prerquisite deamons to come up first.
# Commands ($1 values)
#    ovs-server     Runs the ovs daemons - ovsdb-server and ovs-switchd (v3)
#    run-ovn-northd Runs ovn-northd as a process does not run nb_ovsdb or sb_ovsdb (v3)
#    nb-ovsdb       Runs nb_ovsdb as a process (no detach or monitor) (v3)
#    sb-ovsdb       Runs sb_ovsdb as a process (no detach or monitor) (v3)
#    ovn-master     Runs ovnkube in master mode (v3)
#    ovn-controller Runs ovn controller (v3)
#    ovn-node       Runs ovnkube in node mode (v3)
#    cleanup-ovn-node   Runs ovnkube to cleanup the node (v3)
#    cleanup-ovs-server Cleanup ovs-server (v3)
#    display        Displays log files
#    display_env    Displays environment variables
#    ovn_debug      Displays ovn/ovs configuration and flows

# ====================
# Environment variables are used to customize operation
# K8S_APISERVER - hostname:port (URL)of the real apiserver, not the service address - v3
# OVN_NET_CIDR - the network cidr - v3
# OVN_SVC_CIDR - the cluster-service-cidr - v3
# OVN_KUBERNETES_NAMESPACE - k8s namespace - v3
# K8S_NODE - hostname of the node - v3
#
# OVN_DAEMONSET_VERSION - version match daemonset and image - v3
# K8S_TOKEN - the apiserver token. Automatically detected when running in a pod - v3
# K8S_CACERT - the apiserver CA. Automatically detected when running in a pod - v3
# OVN_CONTROLLER_OPTS - the options for ovn-ctl
# OVN_NORTHD_OPTS - the options for the ovn northbound db
# OVN_GATEWAY_MODE - the gateway mode (shared or local) - v3
# OVN_GATEWAY_OPTS - the options for the ovn gateway
# OVN_GATEWAY_ROUTER_SUBNET - the gateway router subnet (shared mode, DPU only) - v3
# OVNKUBE_LOGLEVEL - log level for ovnkube (0..5, default 4) - v3
# OVN_LOGLEVEL_NORTHD - log level (ovn-ctl default: -vconsole:emer -vsyslog:err -vfile:info) - v3
# OVN_LOGLEVEL_NB - log level (ovn-ctl default: -vconsole:off -vfile:info) - v3
# OVN_LOGLEVEL_SB - log level (ovn-ctl default: -vconsole:off -vfile:info) - v3
# OVN_LOGLEVEL_CONTROLLER - log level (ovn-ctl default: -vconsole:off -vfile:info) - v3
# OVN_LOGLEVEL_NBCTLD - log level (ovn-ctl default: -vconsole:off -vfile:info) - v3
# OVNKUBE_LOGFILE_MAXSIZE - log file max size in MB(default 100 MB)
# OVNKUBE_LOGFILE_MAXBACKUPS - log file max backups (default 5)
# OVNKUBE_LOGFILE_MAXAGE - log file max age in days (default 5 days)
# OVN_ACL_LOGGING_RATE_LIMIT - specify default ACL logging rate limit in messages per second (default: 20)
# OVN_NB_PORT - ovn north db port (default 6640)
# OVN_SB_PORT - ovn south db port (default 6640)
# OVN_NB_RAFT_PORT - ovn north db raft port (default 6643)
# OVN_SB_RAFT_PORT - ovn south db raft port (default 6644)
# OVN_NB_RAFT_ELECTION_TIMER - ovn north db election timer in ms (default 1000)
# OVN_SB_RAFT_ELECTION_TIMER - ovn south db election timer in ms (default 1000)
# OVN_SSL_ENABLE - use SSL transport to NB/SB db and northd (default: no)
# OVN_REMOTE_PROBE_INTERVAL - ovn remote probe interval in ms (default 100000)
# OVN_MONITOR_ALL - ovn-controller monitor all data in SB DB
# OVN_OFCTRL_WAIT_BEFORE_CLEAR - ovn-controller wait time in ms before clearing OpenFlow rules during start up
# OVN_ENABLE_LFLOW_CACHE - enable ovn-controller lflow-cache
# OVN_LFLOW_CACHE_LIMIT - maximum number of logical flow cache entries of ovn-controller
# OVN_LFLOW_CACHE_LIMIT_KB - maximum size of the logical flow cache of ovn-controller
# OVN_EGRESSIP_ENABLE - enable egress IP for ovn-kubernetes
# OVN_EGRESSIP_HEALTHCHECK_PORT - egress IP node check to use grpc on this port (0 ==> dial to port 9 instead)
# OVN_EGRESSFIREWALL_ENABLE - enable egressFirewall for ovn-kubernetes
# OVN_EGRESSQOS_ENABLE - enable egress QoS for ovn-kubernetes
# OVN_UNPRIVILEGED_MODE - execute CNI ovs/netns commands from host (default no)
# OVNKUBE_NODE_MODE - ovnkube node mode of operation, one of: full, dpu, dpu-host (default: full)
# OVNKUBE_NODE_MGMT_PORT_NETDEV - ovnkube node management port netdev.
# OVN_ENCAP_IP - encap IP to be used for OVN traffic on the node. mandatory in case ovnkube-node-mode=="dpu"
# OVN_HOST_NETWORK_NAMESPACE - namespace to classify host network traffic for applying network policies

# The argument to the command is the operation to be performed
# ovn-master ovn-controller ovn-node display display_env ovn_debug
# a cmd must be provided, there is no default
cmd=${1:-""}

# ovn daemon log levels
ovn_loglevel_northd=${OVN_LOGLEVEL_NORTHD:-"-vconsole:info"}
ovn_loglevel_nb=${OVN_LOGLEVEL_NB:-"-vconsole:info"}
ovn_loglevel_sb=${OVN_LOGLEVEL_SB:-"-vconsole:info"}
ovn_loglevel_controller=${OVN_LOGLEVEL_CONTROLLER:-"-vconsole:info"}

ovnkubelogdir=/var/log/ovn-kubernetes

# logfile rotation parameters
ovnkube_logfile_maxsize=${OVNKUBE_LOGFILE_MAXSIZE:-"100"}
ovnkube_logfile_maxbackups=${OVNKUBE_LOGFILE_MAXBACKUPS:-"5"}
ovnkube_logfile_maxage=${OVNKUBE_LOGFILE_MAXAGE:-"5"}

# ovnkube.sh version (update when API between daemonset and script changes - v.x.y)
ovnkube_version="3"

# The daemonset version must be compatible with this script.
# The default when OVN_DAEMONSET_VERSION is not set is version 3
ovn_daemonset_version=${OVN_DAEMONSET_VERSION:-"3"}

# hostname is the host's hostname when using host networking,
# This is useful on the master
# otherwise it is the container ID (useful for debugging).
ovn_pod_host=${K8S_NODE:-$(hostname)}

# The ovs user id, by default it is going to be root:root
ovs_user_id=${OVS_USER_ID:-""}

# ovs options
ovs_options=${OVS_OPTIONS:-""}

if [[ -f /var/run/secrets/kubernetes.io/serviceaccount/token ]]; then
  k8s_token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
else
  k8s_token=${K8S_TOKEN}
fi

# certs and private keys for k8s and OVN
K8S_CACERT=${K8S_CACERT:-/var/run/secrets/kubernetes.io/serviceaccount/ca.crt}

ovn_ca_cert=/ovn-cert/ca-cert.pem
ovn_nb_pk=/ovn-cert/ovnnb-privkey.pem
ovn_nb_cert=/ovn-cert/ovnnb-cert.pem
ovn_sb_pk=/ovn-cert/ovnsb-privkey.pem
ovn_sb_cert=/ovn-cert/ovnsb-cert.pem
ovn_northd_pk=/ovn-cert/ovnnorthd-privkey.pem
ovn_northd_cert=/ovn-cert/ovnnorthd-cert.pem
ovn_controller_pk=/ovn-cert/ovncontroller-privkey.pem
ovn_controller_cert=/ovn-cert/ovncontroller-cert.pem
ovn_controller_cname="ovncontroller"

transport="tcp"
ovndb_ctl_ssl_opts=""
if [[ "yes" == ${OVN_SSL_ENABLE} ]]; then
  transport="ssl"
  ovndb_ctl_ssl_opts="-p ${ovn_controller_pk} -c ${ovn_controller_cert} -C ${ovn_ca_cert}"
fi

# ovn-northd - /etc/sysconfig/ovn-northd
ovn_northd_opts=${OVN_NORTHD_OPTS:-""}

# ovn-controller
ovn_controller_opts=${OVN_CONTROLLER_OPTS:-""}

# set the log level for ovnkube
ovnkube_loglevel=${OVNKUBE_LOGLEVEL:-4}

# by default it is going to be a shared gateway mode, however this can be overridden to any of the other
# two gateway modes that we support using `images/daemonset.sh` tool
ovn_gateway_mode=${OVN_GATEWAY_MODE:-"shared"}
ovn_gateway_opts=${OVN_GATEWAY_OPTS:-""}
ovn_gateway_router_subnet=${OVN_GATEWAY_ROUTER_SUBNET:-""}

net_cidr=${OVN_NET_CIDR:-10.128.0.0/14/23}
svc_cidr=${OVN_SVC_CIDR:-172.30.0.0/16}
mtu=${OVN_MTU:-1400}
routable_mtu=${OVN_ROUTABLE_MTU:-}

# set metrics endpoint bind to K8S_NODE_IP.
metrics_endpoint_ip=${K8S_NODE_IP:-0.0.0.0}
metrics_endpoint_ip=$(bracketify $metrics_endpoint_ip)
ovn_kubernetes_namespace=${OVN_KUBERNETES_NAMESPACE:-ovn-kubernetes}
# namespace used for classifying host network traffic
ovn_host_network_namespace=${OVN_HOST_NETWORK_NAMESPACE:-ovn-host-network}

# host on which ovnkube-db POD is running and this POD contains both
# OVN NB and SB DB running in their own container.
ovn_db_host=$(hostname -i)

# OVN_NB_PORT - ovn north db port (default 6640)
ovn_nb_port=${OVN_NB_PORT:-6640}
# OVN_SB_PORT - ovn south db port (default 6640)
ovn_sb_port=${OVN_SB_PORT:-6640}
# OVN_NB_RAFT_PORT - ovn north db port used for raft communication (default 6643)
ovn_nb_raft_port=${OVN_NB_RAFT_PORT:-6643}
# OVN_SB_RAFT_PORT - ovn south db port used for raft communication (default 6644)
ovn_sb_raft_port=${OVN_SB_RAFT_PORT:-6644}
# OVN_ENCAP_PORT - GENEVE UDP port (default 6081)
ovn_encap_port=${OVN_ENCAP_PORT:-6081}
# OVN_NB_RAFT_ELECTION_TIMER - ovn north db election timer in ms (default 1000)
ovn_nb_raft_election_timer=${OVN_NB_RAFT_ELECTION_TIMER:-1000}
# OVN_SB_RAFT_ELECTION_TIMER - ovn south db election timer in ms (default 1000)
ovn_sb_raft_election_timer=${OVN_SB_RAFT_ELECTION_TIMER:-1000}

ovn_hybrid_overlay_enable=${OVN_HYBRID_OVERLAY_ENABLE:-}
ovn_hybrid_overlay_net_cidr=${OVN_HYBRID_OVERLAY_NET_CIDR:-}
ovn_disable_snat_multiple_gws=${OVN_DISABLE_SNAT_MULTIPLE_GWS:-}
ovn_disable_pkt_mtu_check=${OVN_DISABLE_PKT_MTU_CHECK:-}
ovn_empty_lb_events=${OVN_EMPTY_LB_EVENTS:-}
# OVN_V4_JOIN_SUBNET - v4 join subnet
ovn_v4_join_subnet=${OVN_V4_JOIN_SUBNET:-}
# OVN_V6_JOIN_SUBNET - v6 join subnet
ovn_v6_join_subnet=${OVN_V6_JOIN_SUBNET:-}
#OVN_REMOTE_PROBE_INTERVAL - ovn remote probe interval in ms (default 100000)
ovn_remote_probe_interval=${OVN_REMOTE_PROBE_INTERVAL:-100000}
#OVN_MONITOR_ALL - ovn-controller monitor all data in SB DB
ovn_monitor_all=${OVN_MONITOR_ALL:-}
#OVN_OFCTRL_WAIT_BEFORE_CLEAR - ovn-controller wait time in ms before clearing OpenFlow rules during start up
ovn_ofctrl_wait_before_clear=${OVN_OFCTRL_WAIT_BEFORE_CLEAR:-}
ovn_enable_lflow_cache=${OVN_ENABLE_LFLOW_CACHE:-}
ovn_lflow_cache_limit=${OVN_LFLOW_CACHE_LIMIT:-}
ovn_lflow_cache_limit_kb=${OVN_LFLOW_CACHE_LIMIT_KB:-}
ovn_multicast_enable=${OVN_MULTICAST_ENABLE:-}
#OVN_EGRESSIP_ENABLE - enable egress IP for ovn-kubernetes
ovn_egressip_enable=${OVN_EGRESSIP_ENABLE:-false}
#OVN_EGRESSIP_HEALTHCHECK_PORT - egress IP node check to use grpc on this port
ovn_egress_ip_healthcheck_port=${OVN_EGRESSIP_HEALTHCHECK_PORT:-9107}
#OVN_EGRESSFIREWALL_ENABLE - enable egressFirewall for ovn-kubernetes
ovn_egressfirewall_enable=${OVN_EGRESSFIREWALL_ENABLE:-false}
#OVN_EGRESSQOS_ENABLE - enable egress QoS for ovn-kubernetes
ovn_egressqos_enable=${OVN_EGRESSQOS_ENABLE:-false}
#OVN_DISABLE_OVN_IFACE_ID_VER - disable usage of the OVN iface-id-ver option
ovn_disable_ovn_iface_id_ver=${OVN_DISABLE_OVN_IFACE_ID_VER:-false}
ovn_acl_logging_rate_limit=${OVN_ACL_LOGGING_RATE_LIMIT:-"20"}
ovn_netflow_targets=${OVN_NETFLOW_TARGETS:-}
ovn_sflow_targets=${OVN_SFLOW_TARGETS:-}
ovn_ipfix_targets=${OVN_IPFIX_TARGETS:-}
ovn_ipfix_sampling=${OVN_IPFIX_SAMPLING:-} \
ovn_ipfix_cache_max_flows=${OVN_IPFIX_CACHE_MAX_FLOWS:-} \
ovn_ipfix_cache_active_timeout=${OVN_IPFIX_CACHE_ACTIVE_TIMEOUT:-} \

# OVNKUBE_NODE_MODE - is the mode which ovnkube node operates
ovnkube_node_mode=${OVNKUBE_NODE_MODE:-"full"}
# OVNKUBE_NODE_MGMT_PORT_NETDEV - is the net device to be used for management port
ovnkube_node_mgmt_port_netdev=${OVNKUBE_NODE_MGMT_PORT_NETDEV:-}
ovnkube_config_duration_enable=${OVNKUBE_CONFIG_DURATION_ENABLE:-false}
# OVN_ENCAP_IP - encap IP to be used for OVN traffic on the node
ovn_encap_ip=${OVN_ENCAP_IP:-}

ovn_ex_gw_network_interface=${OVN_EX_GW_NETWORK_INTERFACE:-}

# Determine the ovn rundir.
if [[ -f /usr/bin/ovn-appctl ]]; then
  # ovn-appctl is present. Use new ovn run dir path.
  OVN_RUNDIR=/var/run/ovn
  OVNCTL_PATH=/usr/share/ovn/scripts/ovn-ctl
  OVN_LOGDIR=/var/log/ovn
  OVN_ETCDIR=/etc/ovn
else
  # ovn-appctl is not present. Use openvswitch run dir path.
  OVN_RUNDIR=/var/run/openvswitch
  OVNCTL_PATH=/usr/share/openvswitch/scripts/ovn-ctl
  OVN_LOGDIR=/var/log/openvswitch
  OVN_ETCDIR=/etc/openvswitch
fi

OVS_RUNDIR=/var/run/openvswitch
OVS_LOGDIR=/var/log/openvswitch

# =========================================

setup_ovs_permissions() {
  if [ ${ovs_user_id:-XX} != "XX" ]; then
    chown -R ${ovs_user_id} /etc/openvswitch
    chown -R ${ovs_user_id} ${OVS_RUNDIR}
    chown -R ${ovs_user_id} ${OVS_LOGDIR}
    chown -R ${ovs_user_id} ${OVN_ETCDIR}
    chown -R ${ovs_user_id} ${OVN_RUNDIR}
    chown -R ${ovs_user_id} ${OVN_LOGDIR}
  fi
}

run_as_ovs_user_if_needed() {
  setup_ovs_permissions

  if [ ${ovs_user_id:-XX} != "XX" ]; then
    local uid=$(id -u "${ovs_user_id%:*}")
    local gid=$(id -g "${ovs_user_id%:*}")
    local groups=$(id -G "${ovs_user_id%:*}" | tr ' ' ',')

    setpriv --reuid $uid --regid $gid --groups $groups "$@"
    echo "run as: setpriv --reuid $uid --regid $gid --groups $groups $@"
  else
    "$@"
    echo "run as: $@"
  fi
}

# wait_for_event [attempts=<num>] function_to_call [arguments_to_function]
#
# Processes running inside the container should immediately start, so we
# shouldn't be making 80 attempts (default value). The "attempts=<num>"
# argument will help us in configuring that value.
wait_for_event() {
  retries=0
  sleeper=1
  attempts=80
  if [[ $1 =~ ^attempts= ]]; then
    eval $1
    shift
  fi
  while true; do
    $@
    if [[ $? != 0 ]]; then
      ((retries += 1))
      if [[ "${retries}" -gt ${attempts} ]]; then
        echo "error: $@ did not come up, exiting"
        exit 1
      fi
      echo "info: Waiting for $@ to come up, waiting ${sleeper}s ..."
      sleep ${sleeper}
      sleeper=5
    else
      if [[ "${retries}" != 0 ]]; then
        echo "$@ came up in ${retries} ${sleeper} sec tries"
      fi
      break
    fi
  done
}

# check that daemonset version is among expected versions
check_ovn_daemonset_version() {
  ok=$1
  for v in ${ok}; do
    if [[ $v == ${ovn_daemonset_version} ]]; then
      return 0
    fi
  done
  echo "VERSION MISMATCH expect ${ok}, daemonset is version ${ovn_daemonset_version}"
  exit 1
}


ovsdb_cleanup() {
  local db=${1}
  ovs-appctl -t ${OVN_RUNDIR}/ovn${db}_db.ctl exit >/dev/null 2>&1
  kill $(jobs -p) >/dev/null 2>&1
  exit 0
}

get_ovn_db_vars() {
  ovn_nbdb_str=""
  ovn_sbdb_str=""
  for i in "${ovn_db_hosts[@]}"; do
    if [ -n "$ovn_nbdb_str" ]; then
      ovn_nbdb_str=${ovn_nbdb_str}","
      ovn_sbdb_str=${ovn_sbdb_str}","
    fi
    ip=$(bracketify $i)
    ovn_nbdb_str=${ovn_nbdb_str}${transport}://${ip}:${ovn_nb_port}
    ovn_sbdb_str=${ovn_sbdb_str}${transport}://${ip}:${ovn_sb_port}
  done
  # OVN_NORTH and OVN_SOUTH override derived host
  ovn_nbdb=${OVN_NORTH:-$ovn_nbdb_str}
  ovn_sbdb=${OVN_SOUTH:-$ovn_sbdb_str}

  # ovsdb server connection method <transport>:<host_address>:<port>
  ovn_nbdb_conn=$(echo ${ovn_nbdb} | sed 's;//;;g')
  ovn_sbdb_conn=$(echo ${ovn_sbdb} | sed 's;//;;g')
}

# OVS must be up before OVN comes up.
# This checks if OVS is up and running
ovs_ready() {
  for daemon in $(echo ovsdb-server ovs-vswitchd); do
    pidfile=${OVS_RUNDIR}/${daemon}.pid
    if [[ -f ${pidfile} ]]; then
      check_health $daemon $(cat $pidfile)
      if [[ $? == 0 ]]; then
        continue
      fi
    fi
    return 1
  done
  return 0
}

# Verify that the process is running either by checking for the PID in `ps` output
# or by using `ovs-appctl` utility for the processes that support it.
# $1 is the name of the process
process_ready() {
  case ${1} in
  "ovsdb-server" | "ovs-vswitchd")
    pidfile=${OVS_RUNDIR}/${1}.pid
    ;;
  *)
    pidfile=${OVN_RUNDIR}/${1}.pid
    ;;
  esac

  if [[ -f ${pidfile} ]]; then
    check_health $1 $(cat $pidfile)
    if [[ $? == 0 ]]; then
      return 0
    fi
  fi
  return 1
}

# continuously checks if process is healthy. Exits if process terminates.
# $1 is the name of the process
# $2 is the pid of an another process to kill before exiting
process_healthy() {
  case ${1} in
  "ovsdb-server" | "ovs-vswitchd")
    pid=$(cat ${OVS_RUNDIR}/${1}.pid)
    ;;
  *)
    pid=$(cat ${OVN_RUNDIR}/${1}.pid)
    ;;
  esac

  while true; do
    check_health $1 ${pid}
    if [[ $? != 0 ]]; then
      echo "=============== pid ${pid} terminated ========== "
      # kill the tail -f
      if [[ $2 != "" ]]; then
        kill $2
      fi
      exit 6
    fi
    sleep 15
  done
}

# checks for the health of the process either using `ps` or `ovs-appctl`
# $1 is the name of the process
# $2 is the process pid
check_health() {
  ctl_file=""
  case ${1} in
  "ovnkube" | "ovnkube-master" | "ovn-dbchecker")
    # just check for presence of pid
    ;;
  "ovnnb_db" | "ovnsb_db")
    ctl_file=${OVN_RUNDIR}/${1}.ctl
    ;;
  "ovn-northd" | "ovn-controller")
    ctl_file=${OVN_RUNDIR}/${1}.${2}.ctl
    ;;
  "ovsdb-server" | "ovs-vswitchd")
    ctl_file=${OVS_RUNDIR}/${1}.${2}.ctl
    ;;
  *)
    echo "Unknown service ${1} specified. Exiting.. "
    exit 1
    ;;
  esac

  if [[ ${ctl_file} == "" ]]; then
    # no control file, so just do the PID check
    pid=${2}
    pidTest=$(ps ax | awk '{ print $1 }' | grep "^${pid:-XX}$")
    if [[ ${pid:-XX} == ${pidTest} ]]; then
      return 0
    fi
  else
    # use ovs-appctl to do the check
    ovs-appctl -t ${ctl_file} version >/dev/null
    if [[ $? == 0 ]]; then
      return 0
    fi
  fi

  return 1
}

display_file() {
  if [[ -f $3 ]]; then
    echo "====================== $1 pid "
    cat $2
    echo "====================== $1 log "
    cat $3
    echo " "
  fi
}

# pid and log file for each container
display() {
  echo "==================== display for ${ovn_pod_host}  =================== "
  date
  display_file "nb-ovsdb" ${OVN_RUNDIR}/ovnnb_db.pid ${OVN_LOGDIR}/ovsdb-server-nb.log
  display_file "sb-ovsdb" ${OVN_RUNDIR}/ovnsb_db.pid ${OVN_LOGDIR}/ovsdb-server-sb.log
  display_file "run-ovn-northd" ${OVN_RUNDIR}/ovn-northd.pid ${OVN_LOGDIR}/ovn-northd.log
  display_file "ovn-master" ${OVN_RUNDIR}/ovnkube-master.pid ${ovnkubelogdir}/ovnkube-master.log
  display_file "ovs-vswitchd" ${OVS_RUNDIR}/ovs-vswitchd.pid ${OVS_LOGDIR}/ovs-vswitchd.log
  display_file "ovsdb-server" ${OVS_RUNDIR}/ovsdb-server.pid ${OVS_LOGDIR}/ovsdb-server.log
  display_file "ovn-controller" ${OVN_RUNDIR}/ovn-controller.pid ${OVN_LOGDIR}/ovn-controller.log
  display_file "ovnkube" ${OVN_RUNDIR}/ovnkube.pid ${ovnkubelogdir}/ovnkube.log
  display_file "ovn-dbchecker" ${OVN_RUNDIR}/ovn-dbchecker.pid ${OVN_LOGDIR}/ovn-dbchecker.log
}

setup_cni() {
  cp -f /usr/libexec/cni/ovn-k8s-cni-overlay /opt/cni/bin/ovn-k8s-cni-overlay
}

display_version() {
  echo " =================== hostname: ${ovn_pod_host}"
  echo " =================== daemonset version ${ovn_daemonset_version}"
  if [[ -f /root/git_info ]]; then
    disp_ver=$(cat /root/git_info)
    echo " =================== Image built from ovn-kubernetes ${disp_ver}"
    return
  fi
}

display_env() {
  echo OVS_USER_ID ${ovs_user_id}
  echo OVS_OPTIONS ${ovs_options}
  echo OVN_NORTH ${ovn_nbdb}
  echo OVN_NORTHD_OPTS ${ovn_northd_opts}
  echo OVN_SOUTH ${ovn_sbdb}
  echo OVN_CONTROLLER_OPTS ${ovn_controller_opts}
  echo OVN_LOGLEVEL_CONTROLLER ${ovn_loglevel_controller}
  echo OVN_GATEWAY_MODE ${ovn_gateway_mode}
  echo OVN_GATEWAY_OPTS ${ovn_gateway_opts}
  echo OVN_GATEWAY_ROUTER_SUBNET ${ovn_gateway_router_subnet}
  echo OVN_NET_CIDR ${net_cidr}
  echo OVN_SVC_CIDR ${svc_cidr}
  echo OVN_NB_PORT ${ovn_nb_port}
  echo OVN_SB_PORT ${ovn_sb_port}
  echo K8S_APISERVER ${K8S_APISERVER}
  echo OVNKUBE_LOGLEVEL ${ovnkube_loglevel}
  echo OVN_DAEMONSET_VERSION ${ovn_daemonset_version}
  echo OVNKUBE_NODE_MODE ${ovnkube_node_mode}
  echo OVN_ENCAP_IP ${ovn_encap_ip}
  echo ovnkube.sh version ${ovnkube_version}
  echo OVN_HOST_NETWORK_NAMESPACE ${ovn_host_network_namespace}
}

ovn_debug() {
  echo "ovn_nbdb ${ovn_nbdb}   ovn_sbdb ${ovn_sbdb}"
  echo "ovn_nbdb_conn ${ovn_nbdb_conn}"
  echo "ovn_sbdb_conn ${ovn_sbdb_conn}"

  # get ovs/ovn info from the node for debug purposes
  echo "=========== ovn_debug   hostname: ${ovn_pod_host} ============="
  echo "=========== ovn-nbctl --db=${ovn_nbdb_conn} show ============="
  ovn-nbctl --db=${ovn_nbdb_conn} show
  echo " "
  echo "=========== ovn-nbctl list ACL ============="
  ovn-nbctl --db=${ovn_nbdb_conn} list ACL
  echo " "
  echo "=========== ovn-nbctl list address_set ============="
  ovn-nbctl --db=${ovn_nbdb_conn} list address_set
  echo " "
  echo "=========== ovs-vsctl show ============="
  ovs-vsctl show
  echo " "
  echo "=========== ovs-ofctl -O OpenFlow13 dump-ports br-int ============="
  ovs-ofctl -O OpenFlow13 dump-ports br-int
  echo " "
  echo "=========== ovs-ofctl -O OpenFlow13 dump-ports-desc br-int ============="
  ovs-ofctl -O OpenFlow13 dump-ports-desc br-int
  echo " "
  echo "=========== ovs-ofctl dump-flows br-int ============="
  ovs-ofctl dump-flows br-int
  echo " "
  echo "=========== ovn-sbctl --db=${ovn_sbdb_conn} show ============="
  ovn-sbctl --db=${ovn_sbdb_conn} show
  echo " "
  echo "=========== ovn-sbctl --db=${ovn_sbdb_conn} lflow-list ============="
  ovn-sbctl --db=${ovn_sbdb_conn} lflow-list
  echo " "
  echo "=========== ovn-sbctl --db=${ovn_sbdb_conn} list datapath ============="
  ovn-sbctl --db=${ovn_sbdb_conn} list datapath
  echo " "
  echo "=========== ovn-sbctl --db=${ovn_sbdb_conn} list port_binding ============="
  ovn-sbctl --db=${ovn_sbdb_conn} list port_binding
}

ovs-server() {
  # start ovs ovsdb-server and ovs-vswitchd
  set -euo pipefail

  # if another process is listening on the cni-server socket, wait until it exits
  trap 'kill $(jobs -p); exit 0' TERM
  retries=0
  while true; do
    if /usr/share/openvswitch/scripts/ovs-ctl status >/dev/null; then
      echo "warning: Another process is currently managing OVS, waiting 10s ..." 2>&1
      sleep 10 &
      wait
      ((retries += 1))
    else
      break
    fi
    if [[ "${retries}" -gt 60 ]]; then
      echo "error: Another process is currently managing OVS, exiting" 2>&1
      exit 1
    fi
  done
  rm -f ${OVS_RUNDIR}/ovs-vswitchd.pid
  rm -f ${OVS_RUNDIR}/ovsdb-server.pid

  # launch OVS
  function quit() {
    /usr/share/openvswitch/scripts/ovs-ctl stop
    exit 1
  }
  trap quit SIGTERM

  setup_ovs_permissions

  USER_ARGS=""
  if [ ${ovs_user_id:-XX} != "XX" ]; then
    USER_ARGS="--ovs-user=${ovs_user_id}"
  fi

  /usr/share/openvswitch/scripts/ovs-ctl start --no-ovs-vswitchd \
    --system-id=random ${ovs_options} ${USER_ARGS} "$@"

  # Restrict the number of pthreads ovs-vswitchd creates to reduce the
  # amount of RSS it uses on hosts with many cores
  # https://bugzilla.redhat.com/show_bug.cgi?id=1571379
  # https://bugzilla.redhat.com/show_bug.cgi?id=1572797
  if [[ $(nproc) -gt 12 ]]; then
    ovs-vsctl --no-wait set Open_vSwitch . other_config:n-revalidator-threads=4
    ovs-vsctl --no-wait set Open_vSwitch . other_config:n-handler-threads=10
  fi
  /usr/share/openvswitch/scripts/ovs-ctl start --no-ovsdb-server \
    --system-id=random ${ovs_options} ${USER_ARGS} "$@"

  tail --follow=name ${OVS_LOGDIR}/ovs-vswitchd.log ${OVS_LOGDIR}/ovsdb-server.log &
  ovs_tail_pid=$!
  sleep 10
  while true; do
    if ! /usr/share/openvswitch/scripts/ovs-ctl status >/dev/null; then
      echo "OVS seems to have crashed, exiting"
      kill ${ovs_tail_pid}
      quit
    fi
    sleep 15
  done
}

cleanup-ovs-server() {
  echo "=============== time: $(date +%d-%m-%H:%M:%S:%N) cleanup-ovs-server (wait for ovn-node to exit) ======="
  retries=0
  while [[ ${retries} -lt 80 ]]; do
    if [[ ! -e ${OVN_RUNDIR}/ovnkube.pid ]]; then
      break
    fi
    echo "=============== time: $(date +%d-%m-%H:%M:%S:%N) cleanup-ovs-server ovn-node still running, wait) ======="
    sleep 1
    ((retries += 1))
  done
  echo "=============== time: $(date +%d-%m-%H:%M:%S:%N) cleanup-ovs-server (ovs-ctl stop) ======="
  /usr/share/openvswitch/scripts/ovs-ctl stop
}

function memory_trim_on_compaction_supported {
  if [[ $1 == "nbdb" ]]; then
    mem_trim_check=$(ovn-appctl -t ${OVN_RUNDIR}/ovnnb_db.ctl list-commands | grep "memory-trim-on-compaction")
  elif [[ $1 == "sbdb"  ]]; then
    mem_trim_check=$(ovn-appctl -t ${OVN_RUNDIR}/ovnsb_db.ctl list-commands | grep "memory-trim-on-compaction")
  fi
  if [[ ${mem_trim_check} != "" ]]; then
    return $(/bin/true)
  else
    return $(/bin/false)
  fi
}

# v3 - run nb_ovsdb in a separate container
nb-ovsdb() {
  trap 'ovsdb_cleanup nb' TERM
  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovnnb_db.pid

  if [[ ${ovn_db_host} == "" ]]; then
    echo "The IP address of the host $(hostname) could not be determined. Exiting..."
    exit 1
  fi

  echo "=============== run nb_ovsdb ========== MASTER ONLY"
  run_as_ovs_user_if_needed \
    ${OVNCTL_PATH} run_nb_ovsdb --no-monitor \
    --ovn-nb-log="${ovn_loglevel_nb}" &

  wait_for_event attempts=3 process_ready ovnnb_db
  echo "=============== nb-ovsdb ========== RUNNING"

  # setting northd probe interval
  set_northd_probe_interval
  [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
    ovn-nbctl set-ssl ${ovn_nb_pk} ${ovn_nb_cert} ${ovn_ca_cert}
    echo "=============== nb-ovsdb ========== reconfigured for SSL"
  }
 [[ "true" == "${ENABLE_IPSEC}" ]] && {
    ovn-nbctl set nb_global . ipsec=true
    echo "=============== nb-ovsdb ========== reconfigured for ipsec"
  }
  ovn-nbctl --inactivity-probe=0 set-connection p${transport}:${ovn_nb_port}:$(bracketify ${ovn_db_host})
  if memory_trim_on_compaction_supported "nbdb"
  then
    # Enable NBDB memory trimming on DB compaction, Every 10mins DBs are compacted
    # memory on the heap is freed, when enable memory trimmming freed memory will go back to OS.
    ovn-appctl -t ${OVN_RUNDIR}/ovnnb_db.ctl ovsdb-server/memory-trim-on-compaction on
  fi
  tail --follow=name ${OVN_LOGDIR}/ovsdb-server-nb.log &
  ovn_tail_pid=$!
  process_healthy ovnnb_db ${ovn_tail_pid}
  echo "=============== run nb_ovsdb ========== terminated"
}

# v3 - run sb_ovsdb in a separate container
sb-ovsdb() {
  trap 'ovsdb_cleanup sb' TERM
  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovnsb_db.pid

  if [[ ${ovn_db_host} == "" ]]; then
    echo "The IP address of the host $(hostname) could not be determined. Exiting..."
    exit 1
  fi

  echo "=============== run sb_ovsdb ========== MASTER ONLY"
  run_as_ovs_user_if_needed \
    ${OVNCTL_PATH} run_sb_ovsdb --no-monitor \
    --ovn-sb-log="${ovn_loglevel_sb}" &

  wait_for_event attempts=3 process_ready ovnsb_db
  echo "=============== sb-ovsdb ========== RUNNING"

  [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
    ovn-sbctl set-ssl ${ovn_sb_pk} ${ovn_sb_cert} ${ovn_ca_cert}
    echo "=============== sb-ovsdb ========== reconfigured for SSL"
  }
  ovn-sbctl --inactivity-probe=0 set-connection p${transport}:${ovn_sb_port}:$(bracketify ${ovn_db_host})

  # create the ovnkube-db endpoints
  if memory_trim_on_compaction_supported "sbdb"
  then
    # Enable SBDB memory trimming on DB compaction, Every 10mins DBs are compacted
    # memory on the heap is freed, when enable memory trimmming freed memory will go back to OS.
    ovn-appctl -t ${OVN_RUNDIR}/ovnsb_db.ctl ovsdb-server/memory-trim-on-compaction on
  fi
  tail --follow=name ${OVN_LOGDIR}/ovsdb-server-sb.log &
  ovn_tail_pid=$!

  process_healthy ovnsb_db ${ovn_tail_pid}
  echo "=============== run sb_ovsdb ========== terminated"
}

# v3 - Runs ovn-dbchecker on ovnkube-db pod.
ovn-dbchecker() {
  trap 'kill $(jobs -p); exit 0' TERM
  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovn-dbchecker.pid

  echo "ovn_nbdb ${ovn_nbdb}   ovn_sbdb ${ovn_sbdb}"

  # wait for nb-ovsdb and sb-ovsdb to start
  echo "=============== ovn-dbchecker (wait for nb-ovsdb) ========== OVNKUBE_DB"
  wait_for_event attempts=15 process_ready ovnnb_db

  echo "=============== ovn-dbchecker (wait for sb-ovsdb) ========== OVNKUBE_DB"
  wait_for_event attempts=15 process_ready ovnsb_db

  local ovn_db_ssl_opts=""
  [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
    ovn_db_ssl_opts="
        --nb-client-privkey ${ovn_controller_pk}
        --nb-client-cert ${ovn_controller_cert}
        --nb-client-cacert ${ovn_ca_cert}
        --nb-cert-common-name ${ovn_controller_cname}
        --sb-client-privkey ${ovn_controller_pk}
        --sb-client-cert ${ovn_controller_cert}
        --sb-client-cacert ${ovn_ca_cert}
        --sb-cert-common-name ${ovn_controller_cname}
      "
  }

  echo "=============== ovn-dbchecker ========== OVNKUBE_DB"
  /usr/bin/ovndbchecker \
    --nb-address=${ovn_nbdb} --sb-address=${ovn_sbdb} \
    ${ovn_db_ssl_opts} \
    --loglevel=${ovnkube_loglevel} \
    --logfile-maxsize=${ovnkube_logfile_maxsize} \
    --logfile-maxbackups=${ovnkube_logfile_maxbackups} \
    --logfile-maxage=${ovnkube_logfile_maxage} \
    --pidfile ${OVN_RUNDIR}/ovn-dbchecker.pid \
    --logfile /var/log/ovn-kubernetes/ovn-dbchecker.log &

  echo "=============== ovn-dbchecker ========== running"
  wait_for_event attempts=3 process_ready ovn-dbchecker

  process_healthy ovn-dbchecker
  exit 11
}

# v3 - Runs northd on master. Does not run nb_ovsdb, and sb_ovsdb
run-ovn-northd() {
  trap 'ovs-appctl -t ovn-northd exit >/dev/null 2>&1; exit 0' TERM
  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovn-northd.pid
  rm -f ${OVN_RUNDIR}/ovn-northd.*.ctl
  mkdir -p ${OVN_RUNDIR}

  echo "=============== run_ovn_northd ========== MASTER ONLY"
  echo "ovn_nbdb ${ovn_nbdb}   ovn_sbdb ${ovn_sbdb}"
  echo "ovn_northd_opts=${ovn_northd_opts}"
  echo "ovn_loglevel_northd=${ovn_loglevel_northd}"

  # no monitor (and no detach), start northd which connects to the
  # ovnkube-db service
  local ovn_northd_ssl_opts=""
  [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
    ovn_northd_ssl_opts="
        --ovn-northd-ssl-key=${ovn_northd_pk}
        --ovn-northd-ssl-cert=${ovn_northd_cert}
        --ovn-northd-ssl-ca-cert=${ovn_ca_cert}
     "
  }

  run_as_ovs_user_if_needed \
    ${OVNCTL_PATH} start_northd \
    --ovn-northd-priority=0 \
    --no-monitor --ovn-manage-ovsdb=no \
    --ovn-northd-nb-db=${ovn_nbdb_conn} --ovn-northd-sb-db=${ovn_sbdb_conn} \
    ${ovn_northd_ssl_opts} \
    --ovn-northd-log="${ovn_loglevel_northd}" \
    ${ovn_northd_opts}

  wait_for_event attempts=3 process_ready ovn-northd
  echo "=============== run_ovn_northd ========== RUNNING"

  tail --follow=name ${OVN_LOGDIR}/ovn-northd.log &
  ovn_tail_pid=$!

  process_healthy ovn-northd ${ovn_tail_pid}
  exit 8
}

# v3 - run ovnkube --master
ovn-master() {
  trap 'kill $(jobs -p); exit 0' TERM
  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovnkube-master.pid

  echo "ovn_nbdb ${ovn_nbdb}   ovn_sbdb ${ovn_sbdb}"

  # wait for northd to start
  wait_for_event process_ready ovn-northd

  # wait for ovs-servers to start since ovn-master sets some fields in OVS DB
  echo "=============== ovn-master - (wait for ovs)"
  wait_for_event ovs_ready

  hybrid_overlay_flags=
  if [[ ${ovn_hybrid_overlay_enable} == "true" ]]; then
    hybrid_overlay_flags="--enable-hybrid-overlay"
    if [[ -n "${ovn_hybrid_overlay_net_cidr}" ]]; then
      hybrid_overlay_flags="${hybrid_overlay_flags} --hybrid-overlay-cluster-subnets=${ovn_hybrid_overlay_net_cidr}"
    fi
  fi
  disable_snat_multiple_gws_flag=
  if [[ ${ovn_disable_snat_multiple_gws} == "true" ]]; then
      disable_snat_multiple_gws_flag="--disable-snat-multiple-gws"
  fi

  disable_pkt_mtu_check_flag=
  if [[ ${ovn_disable_pkt_mtu_check} == "true" ]]; then
      disable_pkt_mtu_check_flag="--disable-pkt-mtu-check"
  fi

  empty_lb_events_flag=
  if [[ ${ovn_empty_lb_events} == "true" ]]; then
      empty_lb_events_flag="--ovn-empty-lb-events"
  fi

  ovn_v4_join_subnet_opt=
  if [[ -n ${ovn_v4_join_subnet} ]]; then
      ovn_v4_join_subnet_opt="--gateway-v4-join-subnet=${ovn_v4_join_subnet}"
  fi

  ovn_v6_join_subnet_opt=
  if [[ -n ${ovn_v6_join_subnet} ]]; then
      ovn_v6_join_subnet_opt="--gateway-v6-join-subnet=${ovn_v6_join_subnet}"
  fi

  local ovn_master_ssl_opts=""
  [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
    ovn_master_ssl_opts="
        --nb-client-privkey ${ovn_controller_pk}
        --nb-client-cert ${ovn_controller_cert}
        --nb-client-cacert ${ovn_ca_cert}
        --nb-cert-common-name ${ovn_controller_cname}
        --sb-client-privkey ${ovn_controller_pk}
        --sb-client-cert ${ovn_controller_cert}
        --sb-client-cacert ${ovn_ca_cert}
        --sb-cert-common-name ${ovn_controller_cname}
      "
  }

  ovn_acl_logging_rate_limit_flag=
  if [[ -n ${ovn_acl_logging_rate_limit} ]]; then
      ovn_acl_logging_rate_limit_flag="--acl-logging-rate-limit ${ovn_acl_logging_rate_limit}"
  fi

  multicast_enabled_flag=
  if [[ ${ovn_multicast_enable} == "true" ]]; then
      multicast_enabled_flag="--enable-multicast"
  fi

  egressip_enabled_flag=
  if [[ ${ovn_egressip_enable} == "true" ]]; then
      egressip_enabled_flag="--enable-egress-ip"
  fi

  egressip_healthcheck_port_flag=
  if [[ -n "${ovn_egress_ip_healthcheck_port}" ]]; then
      egressip_healthcheck_port_flag="--egressip-node-healthcheck-port=${ovn_egress_ip_healthcheck_port}"
  fi

  egressfirewall_enabled_flag=
  if [[ ${ovn_egressfirewall_enable} == "true" ]]; then
	  egressfirewall_enabled_flag="--enable-egress-firewall"
  fi
  echo "egressfirewall_enabled_flag=${egressfirewall_enabled_flag}"
  egressqos_enabled_flag=
  if [[ ${ovn_egressqos_enable} == "true" ]]; then
	  egressqos_enabled_flag="--enable-egress-qos"
  fi

  ovnkube_master_metrics_bind_address="${metrics_endpoint_ip}:9409"
  local ovnkube_metrics_tls_opts=""
  if [[ ${OVNKUBE_METRICS_PK} != "" && ${OVNKUBE_METRICS_CERT} != "" ]]; then
    ovnkube_metrics_tls_opts="
        --node-server-privkey ${OVNKUBE_METRICS_PK}
        --node-server-cert ${OVNKUBE_METRICS_CERT}
      "
  fi

  ovnkube_config_duration_enable_flag=
  if [[ ${ovnkube_config_duration_enable} == "true" ]]; then
    ovnkube_config_duration_enable_flag="--metrics-enable-config-duration"
  fi
  echo "ovnkube_config_duration_enable_flag: ${ovnkube_config_duration_enable_flag}"

  echo "=============== ovn-master ========== MASTER ONLY"
  /usr/bin/ovnkube \
    --init-master ${K8S_NODE} \
    --cluster-subnets ${net_cidr} --k8s-service-cidr=${svc_cidr} \
    --nb-address=${ovn_nbdb} --sb-address=${ovn_sbdb} \
    --gateway-mode=${ovn_gateway_mode} \
    --loglevel=${ovnkube_loglevel} \
    --logfile-maxsize=${ovnkube_logfile_maxsize} \
    --logfile-maxbackups=${ovnkube_logfile_maxbackups} \
    --logfile-maxage=${ovnkube_logfile_maxage} \
    ${hybrid_overlay_flags} \
    ${disable_snat_multiple_gws_flag} \
    ${empty_lb_events_flag} \
    ${ovn_v4_join_subnet_opt} \
    ${ovn_v6_join_subnet_opt} \
    --pidfile ${OVN_RUNDIR}/ovnkube-master.pid \
    --logfile /var/log/ovn-kubernetes/ovnkube-master.log \
    ${ovn_master_ssl_opts} \
    ${ovnkube_metrics_tls_opts} \
    ${multicast_enabled_flag} \
    ${ovn_acl_logging_rate_limit_flag} \
    ${egressip_enabled_flag} \
    ${egressip_healthcheck_port_flag} \
    ${egressfirewall_enabled_flag} \
    ${egressqos_enabled_flag} \
    ${ovnkube_config_duration_enable_flag} \
    --metrics-bind-address ${ovnkube_master_metrics_bind_address} \
    --host-network-namespace ${ovn_host_network_namespace} &

  echo "=============== ovn-master ========== running"
  wait_for_event attempts=3 process_ready ovnkube-master

  process_healthy ovnkube-master
  exit 9
}

add-external-id-configs() {
  ovs-vsctl get open . external-ids:system-id
  if [ $? -eq 1 ]; then
    ovs-vsctl set open . external-ids:system-id="$(uuidgen)"
  fi

  ovs-vsctl set open . external-ids:rundir="/var/run/openvswitch"
  ovs-vsctl set open . external_ids:ovn-encap-ip="$ovn_encap_ip"
  ovs-vsctl set open . external-ids:ovn-remote="{{ .Values.conf.ovn_remote }}"
  ovs-vsctl set open . external-ids:ovn-encap-type="{{ .Values.conf.ovn_encap_type }}"
  ovs-vsctl set open . external-ids:ovn-bridge="{{ .Values.conf.ovn_bridge }}"
  ovs-vsctl set open . external-ids:ovn-bridge-mappings="{{ .Values.conf.ovn_bridge_mappings }}"
  ovs-vsctl set open . external-ids:ovn-cms-options="{{ .Values.conf.ovn_cms_options }}"

  {{- if .Values.conf.use_fqdn.compute }}
    ovs-vsctl set open . external-ids:hostname="$ovn_pod_host.compute"
  {{- else }}
    ovs-vsctl set open . external-ids:hostname="$ovn_pod_host"
  {{- end }}
}

# ovn-controller - all nodes
ovn-controller() {
  add-external-id-configs

  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovn-controller.pid

  echo "ovn_nbdb ${ovn_nbdb}   ovn_sbdb ${ovn_sbdb}"
  echo "ovn_nbdb_conn ${ovn_nbdb_conn}"

  echo "=============== ovn-controller  start_controller"
  rm -f /var/run/ovn-kubernetes/cni/*
  rm -f ${OVN_RUNDIR}/ovn-controller.*.ctl

  local ovn_controller_ssl_opts=""
  [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
    ovn_controller_ssl_opts="
          --ovn-controller-ssl-key=${ovn_controller_pk}
          --ovn-controller-ssl-cert=${ovn_controller_cert}
          --ovn-controller-ssl-ca-cert=${ovn_ca_cert}
      "
  }
  run_as_ovs_user_if_needed \
    ${OVNCTL_PATH} --no-monitor start_controller \
    --ovn-controller-priority=0 \
    ${ovn_controller_ssl_opts} \
    --ovn-controller-log="${ovn_loglevel_controller}" \
    ${ovn_controller_opts}

  tail --follow=name ${OVN_LOGDIR}/ovn-controller.log &
  controller_tail_pid=$!

  wait_for_event attempts=3 process_ready ovn-controller
  echo "=============== ovn-controller ========== running"

  process_healthy ovn-controller ${controller_tail_pid}
  exit 10
}

# ovn-node - all nodes
ovn-node() {
  trap 'kill $(jobs -p) ; rm -f /etc/cni/net.d/10-ovn-kubernetes.conf ; exit 0' TERM
  check_ovn_daemonset_version "3"
  rm -f ${OVN_RUNDIR}/ovnkube.pid

  if [[ ${ovnkube_node_mode} != "dpu-host" ]]; then
    echo "=============== ovn-node - (wait for ovs)"
    wait_for_event ovs_ready
  fi

  echo "ovn_nbdb ${ovn_nbdb}   ovn_sbdb ${ovn_sbdb}  ovn_nbdb_conn ${ovn_nbdb_conn}"

  if [[ ${ovnkube_node_mode} != "dpu-host" ]]; then
    echo "=============== ovn-node - (ovn-node  wait for ovn-controller.pid)"
    wait_for_event process_ready ovn-controller
  fi

  ovn_routable_mtu_flag=
  if [[ -n "${routable_mtu}" ]]; then
	  routable_mtu_flag="--routable-mtu ${routable_mtu}"
  fi

  hybrid_overlay_flags=
  if [[ ${ovn_hybrid_overlay_enable} == "true" ]]; then
    hybrid_overlay_flags="--enable-hybrid-overlay"
    if [[ -n "${ovn_hybrid_overlay_net_cidr}" ]]; then
      hybrid_overlay_flags="${hybrid_overlay_flags} --hybrid-overlay-cluster-subnets=${ovn_hybrid_overlay_net_cidr}"
    fi
  fi

  disable_snat_multiple_gws_flag=
  if [[ ${ovn_disable_snat_multiple_gws} == "true" ]]; then
      disable_snat_multiple_gws_flag="--disable-snat-multiple-gws"
  fi

  disable_pkt_mtu_check_flag=
  if [[ ${ovn_disable_pkt_mtu_check} == "true" ]]; then
      disable_pkt_mtu_check_flag="--disable-pkt-mtu-check"
  fi

  multicast_enabled_flag=
  if [[ ${ovn_multicast_enable} == "true" ]]; then
      multicast_enabled_flag="--enable-multicast"
  fi

  egressip_enabled_flag=
  if [[ ${ovn_egressip_enable} == "true" ]]; then
      egressip_enabled_flag="--enable-egress-ip"
  fi

  egressip_healthcheck_port_flag=
  if [[ -n "${ovn_egress_ip_healthcheck_port}" ]]; then
      egressip_healthcheck_port_flag="--egressip-node-healthcheck-port=${ovn_egress_ip_healthcheck_port}"
  fi

  disable_ovn_iface_id_ver_flag=
  if [[ ${ovn_disable_ovn_iface_id_ver} == "true" ]]; then
      disable_ovn_iface_id_ver_flag="--disable-ovn-iface-id-ver"
  fi

  netflow_targets=
  if [[ -n ${ovn_netflow_targets} ]]; then
      netflow_targets="--netflow-targets ${ovn_netflow_targets}"
  fi

  sflow_targets=
  if [[ -n ${ovn_sflow_targets} ]]; then
      sflow_targets="--sflow-targets ${ovn_sflow_targets}"
  fi

  ipfix_targets=
  if [[ -n ${ovn_ipfix_targets} ]]; then
      ipfix_targets="--ipfix-targets ${ovn_ipfix_targets}"
  fi

  ipfix_config=
  if [[ -n ${ovn_ipfix_sampling} ]]; then
      ipfix_config="--ipfix-sampling ${ovn_ipfix_sampling}"
  fi
  if [[ -n ${ovn_ipfix_cache_max_flows} ]]; then
      ipfix_config="${ipfix_config} --ipfix-cache-max-flows ${ovn_ipfix_cache_max_flows}"
  fi
  if [[ -n ${ovn_ipfix_cache_active_timeout} ]]; then
      ipfix_config="${ipfix_config} --ipfix-cache-active-timeout ${ovn_ipfix_cache_active_timeout}"
  fi

  monitor_all=
  if [[ -n ${ovn_monitor_all} ]]; then
     monitor_all="--monitor-all=${ovn_monitor_all}"
  fi

  ofctrl_wait_before_clear=
  if [[ -n ${ovn_ofctrl_wait_before_clear} ]]; then
     ofctrl_wait_before_clear="--ofctrl-wait-before-clear=${ovn_ofctrl_wait_before_clear}"
  fi

  enable_lflow_cache=
  if [[ -n ${ovn_enable_lflow_cache} ]]; then
     enable_lflow_cache="--enable-lflow-cache=${ovn_enable_lflow_cache}"
  fi

  lflow_cache_limit=
  if [[ -n ${ovn_lflow_cache_limit} ]]; then
     lflow_cache_limit="--lflow-cache-limit=${ovn_lflow_cache_limit}"
  fi

  lflow_cache_limit_kb=
  if [[ -n ${ovn_lflow_cache_limit_kb} ]]; then
     lflow_cache_limit_kb="--lflow-cache-limit-kb=${ovn_lflow_cache_limit_kb}"
  fi

  egress_interface=
  if [[ -n ${ovn_ex_gw_network_interface} ]]; then
      egress_interface="--exgw-interface ${ovn_ex_gw_network_interface}"
  fi

  ovn_encap_ip_flag=
  if [[ ${ovn_encap_ip} != "" ]]; then
    ovn_encap_ip_flag="--encap-ip=${ovn_encap_ip}"
  else
    ovn_encap_ip=$(ovs-vsctl --if-exists get Open_vSwitch . external_ids:ovn-encap-ip)
    if [[ $? == 0 ]]; then
      ovn_encap_ip=$(echo ${ovn_encap_ip} | tr -d '\"')
      if [[ "${ovn_encap_ip}" != "" ]]; then
        ovn_encap_ip_flag="--encap-ip=${ovn_encap_ip}"
      fi
    fi
  fi

  ovnkube_node_mode_flag=
  if [[ ${ovnkube_node_mode} != "" ]]; then
    ovnkube_node_mode_flag="--ovnkube-node-mode=${ovnkube_node_mode}"
    if [[ ${ovnkube_node_mode} == "dpu" ]]; then
      # encap IP is required for dpu, this is either provided via OVN_ENCAP_IP env variable or taken from ovs
      if [[ ${ovn_encap_ip} == "" ]]; then
        echo "ovn encap IP must be provided if \"ovnkube-node-mode\" set to \"dpu\". Exiting..."
        exit 1
      fi
    fi
  fi

  ovnkube_node_mgmt_port_netdev_flag=
  if [[ ${ovnkube_node_mgmt_port_netdev} != "" ]]; then
    ovnkube_node_mgmt_port_netdev_flag="--ovnkube-node-mgmt-port-netdev=${ovnkube_node_mgmt_port_netdev}"
  fi

  local ovn_node_ssl_opts=""
  if [[ ${ovnkube_node_mode} != "dpu-host" ]]; then
      [[ "yes" == ${OVN_SSL_ENABLE} ]] && {
        ovn_node_ssl_opts="
            --nb-client-privkey ${ovn_controller_pk}
            --nb-client-cert ${ovn_controller_cert}
            --nb-client-cacert ${ovn_ca_cert}
            --nb-cert-common-name ${ovn_controller_cname}
            --sb-client-privkey ${ovn_controller_pk}
            --sb-client-cert ${ovn_controller_cert}
            --sb-client-cacert ${ovn_ca_cert}
            --sb-cert-common-name ${ovn_controller_cname}
          "
      }
  fi

  ovn_unprivileged_flag="--unprivileged-mode"
  if test -z "${OVN_UNPRIVILEGED_MODE+x}" -o "x${OVN_UNPRIVILEGED_MODE}" = xno; then
    ovn_unprivileged_flag=""
  fi

  ovn_metrics_bind_address="${metrics_endpoint_ip}:9476"
  ovnkube_node_metrics_bind_address="${metrics_endpoint_ip}:9410"

  local ovnkube_metrics_tls_opts=""
  if [[ ${OVNKUBE_METRICS_PK} != "" && ${OVNKUBE_METRICS_CERT} != "" ]]; then
    ovnkube_metrics_tls_opts="
        --node-server-privkey ${OVNKUBE_METRICS_PK}
        --node-server-cert ${OVNKUBE_METRICS_CERT}
      "
  fi

  echo "=============== ovn-node   --init-node"
  /usr/bin/ovnkube --init-node ${K8S_NODE} \
    --cluster-subnets ${net_cidr} --k8s-service-cidr=${svc_cidr} \
    --nb-address=${ovn_nbdb} --sb-address=${ovn_sbdb} \
    ${ovn_unprivileged_flag} \
    --nodeport \
    --mtu=${mtu} \
    ${routable_mtu_flag} \
    ${ovn_encap_ip_flag} \
    --loglevel=${ovnkube_loglevel} \
    --logfile-maxsize=${ovnkube_logfile_maxsize} \
    --logfile-maxbackups=${ovnkube_logfile_maxbackups} \
    --logfile-maxage=${ovnkube_logfile_maxage} \
    ${hybrid_overlay_flags} \
    ${disable_snat_multiple_gws_flag} \
    ${disable_pkt_mtu_check_flag} \
    --gateway-mode=${ovn_gateway_mode} ${ovn_gateway_opts} \
    --gateway-router-subnet=${ovn_gateway_router_subnet} \
    --pidfile ${OVN_RUNDIR}/ovnkube.pid \
    --logfile /var/log/ovn-kubernetes/ovnkube.log \
    ${ovn_node_ssl_opts} \
    ${ovnkube_metrics_tls_opts} \
    --inactivity-probe=${ovn_remote_probe_interval} \
    ${monitor_all} \
    ${ofctrl_wait_before_clear} \
    ${enable_lflow_cache} \
    ${lflow_cache_limit} \
    ${lflow_cache_limit_kb} \
    ${multicast_enabled_flag} \
    ${egressip_enabled_flag} \
    ${egressip_healthcheck_port_flag} \
    ${disable_ovn_iface_id_ver_flag} \
    ${netflow_targets} \
    ${sflow_targets} \
    ${ipfix_targets} \
    ${ipfix_config} \
    --ovn-metrics-bind-address ${ovn_metrics_bind_address} \
    --metrics-bind-address ${ovnkube_node_metrics_bind_address} \
     ${ovnkube_node_mode_flag} \
    ${egress_interface} \
    --host-network-namespace ${ovn_host_network_namespace} \
     ${ovnkube_node_mgmt_port_netdev_flag} &

  wait_for_event attempts=3 process_ready ovnkube
  if [[ ${ovnkube_node_mode} != "dpu" ]]; then
    setup_cni
  fi
  echo "=============== ovn-node ========== running"

  process_healthy ovnkube
  exit 7
}

# cleanup-ovn-node - all nodes
cleanup-ovn-node() {
  check_ovn_daemonset_version "3"

  rm -f /etc/cni/net.d/10-ovn-kubernetes.conf

  echo "=============== time: $(date +%d-%m-%H:%M:%S:%N) cleanup-ovn-node - (wait for ovn-controller to exit)"
  retries=0
  while [[ ${retries} -lt 80 ]]; do
    process_ready ovn-controller
    if [[ $? != 0 ]]; then
      break
    fi
    echo "=============== time: $(date +%d-%m-%H:%M:%S:%N) cleanup-ovn-node - (ovn-controller still running, wait)"
    sleep 1
    ((retries += 1))
  done

  echo "=============== time: $(date +%d-%m-%H:%M:%S:%N) cleanup-ovn-node --cleanup-node"
  /usr/bin/ovnkube --cleanup-node ${K8S_NODE} --gateway-mode=${ovn_gateway_mode} ${ovn_gateway_opts} \
    --k8s-token=${k8s_token} --k8s-apiserver=${K8S_APISERVER} --k8s-cacert=${K8S_CACERT} \
    --loglevel=${ovnkube_loglevel} \
    --logfile /var/log/ovn-kubernetes/ovnkube.log

}

# v3 - Runs ovn-kube-util in daemon mode to export prometheus metrics related to OVS.
ovs-metrics() {
  check_ovn_daemonset_version "3"

  echo "=============== ovs-metrics - (wait for ovs_ready)"
  wait_for_event ovs_ready

  ovs_exporter_bind_address="${metrics_endpoint_ip}:9310"
  /usr/bin/ovn-kube-util \
    --loglevel=${ovnkube_loglevel} \
    ovs-exporter \
    --metrics-bind-address ${ovs_exporter_bind_address}

  echo "=============== ovs-metrics with pid ${?} terminated ========== "
  exit 1
}

echo "================== ovnkube.sh --- version: ${ovnkube_version} ================"

echo " ==================== command: ${cmd}"
display_version

# display_env

# Start the requested daemons
# daemons come up in order
# ovs-db-server  - all nodes  -- not done by this script (v3)
# ovs-vswitchd   - all nodes  -- not done by this script (v3)
# run-ovn-northd Runs ovn-northd as a process does not run nb_ovsdb or sb_ovsdb (v3)
# nb-ovsdb       Runs nb_ovsdb as a process (no detach or monitor) (v3)
# sb-ovsdb       Runs sb_ovsdb as a process (no detach or monitor) (v3)
# ovn-dbchecker  Runs ovndb checker alongside nb-ovsdb and sb-ovsdb containers (v3)
# ovn-master     - master only (v3)
# ovn-controller - all nodes (v3)
# ovn-node       - all nodes (v3)
# cleanup-ovn-node - all nodes (v3)

get_ovn_db_vars

case ${cmd} in
"nb-ovsdb") # pod ovnkube-db container nb-ovsdb
  nb-ovsdb
  ;;
"sb-ovsdb") # pod ovnkube-db container sb-ovsdb
  sb-ovsdb
  ;;
"ovn-dbchecker") # pod ovnkube-db container ovn-dbchecker
  ovn-dbchecker
  ;;
"run-ovn-northd") # pod ovnkube-master container run-ovn-northd
  run-ovn-northd
  ;;
"ovn-master") # pod ovnkube-master container ovnkube-master
  ovn-master
  ;;
"ovs-server") # pod ovnkube-node container ovs-daemons
  ovs-server
  ;;
"ovn-controller") # pod ovnkube-node container ovn-controller
  ovn-controller
  ;;
"ovn-node") # pod ovnkube-node container ovn-node
  ovn-node
  ;;
"ovn-northd")
  ovn-northd
  ;;
"display_env")
  display_env
  exit 0
  ;;
"display")
  display
  exit 0
  ;;
"ovn_debug")
  ovn_debug
  exit 0
  ;;
"cleanup-ovs-server")
  cleanup-ovs-server
  ;;
"cleanup-ovn-node")
  cleanup-ovn-node
  ;;
"nb-ovsdb-raft")
  ovsdb-raft nb ${ovn_nb_port} ${ovn_nb_raft_port} ${ovn_nb_raft_election_timer}
  ;;
"sb-ovsdb-raft")
  ovsdb-raft sb ${ovn_sb_port} ${ovn_sb_raft_port} ${ovn_sb_raft_election_timer}
  ;;
"ovs-metrics")
  ovs-metrics
  ;;
*)
  echo "invalid command ${cmd}"
  echo "valid v3 commands: ovs-server nb-ovsdb sb-ovsdb run-ovn-northd ovn-master " \
    "ovn-controller ovn-node display_env display ovn_debug cleanup-ovs-server " \
    "cleanup-ovn-node nb-ovsdb-raft sb-ovsdb-raft"
  exit 0
  ;;
esac

exit 0
