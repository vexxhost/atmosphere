########
RabbitMQ
########

Atmosphere deploys a dedicated RabbitMQ cluster for each OpenStack service that
requires message queuing. This provides isolation between services and enables
per-service resource tuning.

***********************
Per-service overrides
***********************

To customize the RabbitMQ cluster for a specific service, define a variable
named ``<chart>_rabbitmq_spec`` in your inventory, where ``<chart>`` matches the
chart name under ``charts/`` (for example: ``nova``, ``neutron``, ``glance``,
``keystone``).

Example (increase Nova RabbitMQ resources):

.. code-block:: yaml

   nova_rabbitmq_spec:
     resources:
       requests:
         cpu: 500m
         memory: 4Gi
       limits:
         cpu: "1"
         memory: 4Gi

*********************
Common tuning options
*********************

Overrides are merged into the default ``RabbitmqCluster`` spec (recursively).
You may set any valid ``RabbitmqCluster.spec`` fields; common ones include
resources, replicas, persistence, and additional configuration.

.. code-block:: yaml

   nova_rabbitmq_spec:
     # Resource requests and limits
     resources:
       requests:
         cpu: 500m
         memory: 4Gi
       limits:
         cpu: "1"
         memory: 4Gi

     # Number of RabbitMQ replicas (optional)
     replicas: 3

     # Persistent volume storage size (optional)
     persistence:
       storage: 20Gi

     # Additional RabbitMQ configuration (optional)
     rabbitmq:
       additionalConfig: |
         deprecated_features.permit.management_metrics_collection = true
         vm_memory_high_watermark.relative = 0.9

.. note::

   Setting ``rabbitmq.additionalConfig`` replaces the default value (it's not
   appended). If you override it, include any defaults you still want applied.

*****************************
Skipping spec diff approval
*****************************

By default, Atmosphere will prompt for approval when the RabbitMQ cluster
specification changes. To skip this approval step when using per-service
overrides, set:

.. code-block:: yaml

   rabbitmq_skip_spec_diff: true

******************
Verifying changes
******************

RabbitMQ clusters are deployed as ``RabbitmqCluster`` resources in the
``openstack`` namespace and are named ``rabbitmq-<chart>``.

.. code-block:: console

   kubectl -n openstack get rabbitmqclusters
   kubectl -n openstack get rabbitmqcluster rabbitmq-nova -o yaml
