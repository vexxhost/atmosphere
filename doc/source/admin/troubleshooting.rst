#####################
Troubleshooting Guide
#####################

This document aims to provide solutions to common issues encountered during the deployment and operation of Atmosphere. The guide is organized by component and issue type to help you quickly find the most relevant information.

**************************
Open Virtual Network (OVN)
**************************

Recovering clusters
===================

If any of the OVN database pods fail, they will no longer be ready.  You can
recover the cluster by deleting the pods and allowing them to be recreated.

For example, if the ``ovn-ovsdb-nb-0`` pod fails, you can recover the cluster by
deleting the pod:

.. code-block:: console

    $ kubectl -n openstack delete pods/ovn-ovsdb-nb-0

If the entire cluster fails, you can recover the cluster by deleting all of the
pods.  For example, if the southbound database fails, you can recover the
cluster with this command:

.. code-block:: console

    $ kubectl -n openstack delete pods -lcomponent=ovn-ovsdb-sb

If the state of Neutron is lost from the cluster, you can recover it by running
the repair command:

.. code-block:: console

    $ kubectl -n openstack exec deploy/neutron-server -- \
      neutron-ovn-db-sync-util \
        --debug \
        --config-file /etc/neutron/neutron.conf \
        --config-file /tmp/pod-shared/ovn.ini \
        --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
        --ovn-neutron_sync_mode repair


Troubleshooting the customers network
=====================================

When you need to troubleshoot the customers network you can assign a Neutron port to the network and create a port and namespace to troubleshoot the network

1. Create a Netron network port inside the network that needs to be troubleshooted
1. Select the node you want to run this pod on on the nodeSelectorTerms 
2. Change the values of HM_PORT_ID and use the ID of the Neutron port
3. Change the values of HW_PORT_MAC and use the MAC address of the Neutron port
4. Change the values of HW_IP_ADDR and use the IP address of the Neutron port
5. Change the values of HW_IP_GW

.. code-block:: yaml 

    apiVersion: v1
    kind: Pod
    metadata:
      name: netshoot-ovn
      labels:
        app: netshoot-ovn
    spec:
      hostNetwork: true
      restartPolicy: Never
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchFields:
              - key: metadata.name
                operator: In
                values:
                - compute1
    
      initContainers:
      - name: ovn-init
        image: quay.io/vexxhost/openvswitch:latest
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN"]
        env:
          - name: HM_PORT_ID
            value: "34b82bc6-003b-4fe2-a45c-fdb8d00df490"
          - name: HM_PORT_MAC
            value: "fa:16:3e:55:3d:c2"
          - name: HW_IP_ADDR
            value: "192.168.0.176"
          - name: HW_IP_GW
            value: "192.168.0.1"
        command:
          - /bin/sh
          - -c
          - |
            set -ex
            hostname
            TAPNAME="nsh-$(echo ${HM_PORT_ID}|cut -b-11)"
    
            echo "[ovn-init] Waiting for OVS socket..."
            ovs-vsctl --no-wait show
    
            echo "[ovn-init] Adding network namespaces"
            ip netns add netshoot-ns
    
            echo "[ovn-init] Creating OVN port ${TAPNAME}"
            ovs-vsctl --may-exist add-port br-int ${TAPNAME} \
              -- set Interface ${TAPNAME} type=internal \
              -- set Interface ${TAPNAME} external-ids:iface-status=active \
              -- set Interface ${TAPNAME} external-ids:attached-mac=$HM_PORT_MAC \
              -- set Interface ${TAPNAME} external-ids:iface-id=$HM_PORT_ID \
              -- set Interface ${TAPNAME} external-ids:skip_cleanup=false
    
            echo "[ovn-init] Moving interface to namespace"
            ip link set ${TAPNAME} netns netshoot-ns
            ip netns exec netshoot-ns ip link set dev ${TAPNAME} address $HM_PORT_MAC
            ip netns exec netshoot-ns ip link set ${TAPNAME} up
            ip netns exec netshoot-ns ip addr add ${HW_IP_ADDR}/24 dev ${TAPNAME}
            ip netns exec netshoot-ns ip route add default via ${HW_IP_GW} dev ${TAPNAME}
            
            echo "[ovn-init] OVN port setup complete."
    
        volumeMounts:
          - name: host-run
            mountPath: /var/run/openvswitch
          - name: host-netns
            mountPath: /run/netns
            mountPropagation: Bidirectional
          - name: run
            mountPath: /run
    
      containers:
      - name: netshoot
        image: nicolaka/netshoot:latest
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN"]
        env:
          - name: HM_PORT_ID
            value: "34b82bc6-003b-4fe2-a45c-fdb8d00df490"
          - name: HM_PORT_MAC
            value: "fa:16:3e:55:3d:c2"
        command:
          - /bin/sh
          - -c
          - |
            echo "[netshoot] Entering netshoot-ns namespace"
    
            ip netns exec netshoot-ns /bin/bash
            sleep 3600
        volumeMounts:
          - name: host-run
            mountPath: /var/run/openvswitch
          - name: host-netns
            mountPath: /run/netns
          - name: run
            mountPath: /run
    
      - name: cleanup
        image: quay.io/vexxhost/openvswitch:latest
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN"]
        env:
          - name: HM_PORT_ID
            value: "34b82bc6-003b-4fe2-a45c-fdb8d00df490"
          - name: HM_PORT_MAC
            value: "fa:16:3e:55:3d:c2"
        lifecycle:
          preStop:
            exec:
              command:
                - /bin/sh
                - -c
                - |
                  echo "[cleanup] Removing OVN port and namespace"
                  TAPNAME="nsh-$(echo ${HM_PORT_ID}|cut -b-11)"
    
                  # Delete interface from netns
                  ip netns exec netshoot-ns ip link delete ${TAPNAME}
    
                  # Delete the namespace
                  ip netns delete netshoot-ns
    
                  # Delete port from OVS/OVN bridge
                  ovs-vsctl --if-exists del-port br-int ${TAPNAME}
    
                  echo "[cleanup] Cleanup complete"
        volumeMounts:
    
          - name: host-run
            mountPath: /var/run/openvswitch
          - name: host-netns
            mountPath: /run/netns
            mountPropagation: Bidirectional
          - name: run
            mountPath: /run
    
      volumes:
        - name: host-run
          hostPath:
            path: /var/run/openvswitch
        - name: host-netns
          hostPath:
            path: /run/netns
        - name: run
          hostPath:
            path: /run

.. important::
   The clean up does not work currently you need todo this by hand with the commands:

   1. Take the openvswitch pod that is located on the right node:
         kubectl -n openstack exec -it openvswitch-hbgxs -- ovs-vsctl del-port br-int nsh-34b82bc6-00
   2. Delete the network namespace from the node
         ip netns delete netshoot-ns
**********************
Compute Service (Nova)
**********************

Provisioning Failure Due to ``downloading`` Volume
==================================================

If you're trying to provision a new instance that is using a volume where the
backend needs to download images directly from Glance (such as PowerStore for
example) and it fails with the following error:

.. code-block:: text

    Build of instance 54a41735-a4cb-4312-b812-52e4f3d8c500 aborted: Volume 728bdc40-fc22-4b65-b6b6-c94ee7f98ff0 did not finish being created even after we waited 187 seconds or 61 attempts. And its status is downloading.

This means that the volume service could not download the image before the
compute service timed out.  Out of the box, Atmosphere ships with the volume
cache enabled to help offset this issue.  However, if you're using a backend
that does not support the volume cache, you can increase the timeout by setting
the following in your ``inventory/group_vars/all/nova.yml`` file:

.. code-block:: yaml

    nova_helm_values:
      conf:
        enable_iscsi: true
        nova:
          DEFAULT:
            block_device_allocate_retries: 300

*******************************
Load Balancer Service (Octavia)
*******************************

Accessing Amphorae
==================

Atmosphere configures an SSH keypair which allows you to login to the Amphorae
for debugging purposes.  The ``octavia-worker`` containers are fully configured
to allow you to SSH to the Amphorae.

If you have an Amphora running with the IP address ``172.24.0.148``, you can login
to it by simply executing the following:

.. code-block:: console

    $ kubectl -n openstack exec -it deploy/octavia-worker -- ssh 172.24.0.148


Listener with ``provisioning_status`` stuck in ``ERROR``
========================================================

There are scenarios where the load balancer could be in an ``ACTIVE`` state however
the listener can be stuck in a ``provisioning_status`` of ``ERROR``.  This is usually
related to an expired TLS certificate not cleanly recovering.

Another symptom of this issue will be that you'll see the following inside the
``octavia-worker`` logs:

.. code-block:: text

    ERROR oslo_messaging.rpc.server [None req-ad303faf-7a53-4c55-94a5-28cd61c46619 - e83856ceda5c42df8810df42fef8fc1c - - - -] Exception during message handling: octavia.amphorae.drivers.haproxy.exceptions.InternalServerError: Internal Server Erro
    ERROR oslo_messaging.rpc.server Traceback (most recent call last):
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/oslo_messaging/rpc/server.py", line 165, in _process_incoming
    ERROR oslo_messaging.rpc.server     res = self.dispatcher.dispatch(message)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/oslo_messaging/rpc/dispatcher.py", line 309, in dispatch
    ERROR oslo_messaging.rpc.server     return self._do_dispatch(endpoint, method, ctxt, args)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/oslo_messaging/rpc/dispatcher.py", line 229, in _do_dispatch
    ERROR oslo_messaging.rpc.server     result = func(ctxt, **new_args)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/controller/queue/v2/endpoints.py", line 90, in update_pool
    ERROR oslo_messaging.rpc.server     self.worker.update_pool(original_pool, pool_updates)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/controller/worker/v2/controller_worker.py", line 733, in update_pool
    ERROR oslo_messaging.rpc.server     self.run_flow(
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/controller/worker/v2/controller_worker.py", line 113, in run_flow
    ERROR oslo_messaging.rpc.server     tf.run()
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/taskflow/engines/action_engine/engine.py", line 247, in run
    ERROR oslo_messaging.rpc.server     for _state in self.run_iter(timeout=timeout):
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/taskflow/engines/action_engine/engine.py", line 340, in run_iter
    ERROR oslo_messaging.rpc.server     failure.Failure.reraise_if_any(er_failures)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/taskflow/types/failure.py", line 338, in reraise_if_any
    ERROR oslo_messaging.rpc.server     failures[0].reraise()
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/taskflow/types/failure.py", line 350, in reraise
    ERROR oslo_messaging.rpc.server     raise value
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/taskflow/engines/action_engine/executor.py", line 52, in _execute_task
    ERROR oslo_messaging.rpc.server     result = task.execute(**arguments)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/controller/worker/v2/tasks/amphora_driver_tasks.py", line 157, in execute
    ERROR oslo_messaging.rpc.server     self.amphora_driver.update(loadbalancer)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/amphorae/drivers/haproxy/rest_api_driver.py", line 236, in update
    ERROR oslo_messaging.rpc.server     self.update_amphora_listeners(loadbalancer, amphora)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/amphorae/drivers/haproxy/rest_api_driver.py", line 205, in update_amphora_listeners
    ERROR oslo_messaging.rpc.server     self.clients[amphora.api_version].upload_config(
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/amphorae/drivers/haproxy/rest_api_driver.py", line 758, in upload_config
    ERROR oslo_messaging.rpc.server     return exc.check_exception(r)
    ERROR oslo_messaging.rpc.server   File "/var/lib/openstack/lib/python3.10/site-packages/octavia/amphorae/drivers/haproxy/exceptions.py", line 44, in check_exception
    ERROR oslo_messaging.rpc.server     raise responses[status_code]()
    ERROR oslo_messaging.rpc.server octavia.amphorae.drivers.haproxy.exceptions.InternalServerError: Internal Server Error

You can simply trigger a complete failover of the load balancer which will solve
the issue:

.. code-block:: console

    $ openstack loadbalancer failover ${LOAD_BALANCER_ID}

.. admonition:: Help us improve Atmosphere!
    :class: info

    We're trying to collect data with when these failures occur to better understand
    the root cause.  If you encounter this issue, please reach out to the Atmosphere
    team so we can better understand the issue by filing an issue with the output of
    the ``amphora-agent`` logs from the Amphora.
