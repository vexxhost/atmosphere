########
RabbitMQ
########

Atmosphere deploys a dedicated RabbitMQ cluster for each OpenStack service that
requires message queuing. This provides isolation between services and enables
per-service resource tuning.

***********************
Per-service tuning
***********************

To customize RabbitMQ resources for a specific OpenStack service, define a
variable named ``<service>_rabbitmq_spec``. For example, to increase resources
for Nova's RabbitMQ cluster:

.. code-block:: yaml

   nova_rabbitmq_spec:
     resources:
       requests:
         cpu: 500m
         memory: 4Gi
       limits:
         cpu: 1
         memory: 4Gi

The following services support per-service RabbitMQ overrides:

- ``nova_rabbitmq_spec``
- ``neutron_rabbitmq_spec``
- ``cinder_rabbitmq_spec``
- ``octavia_rabbitmq_spec``
- ``heat_rabbitmq_spec``
- ``barbican_rabbitmq_spec``
- ``designate_rabbitmq_spec``
- ``magnum_rabbitmq_spec``
- ``manila_rabbitmq_spec``

*********************
Available options
*********************

The ``rabbitmq_spec`` dictionary merges with the default configuration and
supports the following options:

.. code-block:: yaml

   nova_rabbitmq_spec:
     # Resource requests and limits
     resources:
       requests:
         cpu: 500m
         memory: 4Gi
       limits:
         cpu: 1
         memory: 4Gi

     # Number of RabbitMQ replicas (optional)
     replicas: 3

     # Persistent volume storage size (optional)
     persistence:
       storage: 20Gi

     # Additional RabbitMQ configuration (optional)
     rabbitmq:
       additionalConfig: |
         vm_memory_high_watermark.relative = 0.9

*****************************
Skipping spec diff approval
*****************************

By default, Atmosphere will prompt for approval when the RabbitMQ cluster
specification changes. To skip this approval step when using per-service
overrides, set:

.. code-block:: yaml

   rabbitmq_skip_spec_diff: true
