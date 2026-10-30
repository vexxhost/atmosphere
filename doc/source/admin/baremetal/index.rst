##########
Bare metal
##########

Atmosphere can deploy Ironic to provision bare metal nodes. It is not part of
the default OpenStack playbook, so add its role to your own playbook:

.. code-block:: yaml

    - hosts: controllers[0]
      become: true
      roles:
        - vexxhost.atmosphere.ironic

Set the hostname for the Ironic API in your inventory:

.. code-block:: yaml

    openstack_helm_endpoints_ironic_api_host: baremetal.cloud.example.com

To let users create bare metal instances through Nova, enable
``nova-compute-ironic``, which is not deployed by default:

.. code-block:: yaml

    nova_helm_values:
      manifests:
        statefulset_compute_ironic: true

.. toctree::
   :maxdepth: 2

   console
