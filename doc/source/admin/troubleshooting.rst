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
