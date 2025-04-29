==================
Building Inventory
==================

Atmosphere relies on an Ansible inventory in order to drive the deployment of
all the components.

In order to deploy Atmosphere, you will need to build a directory structure
that will contain all the configuration files and secrets required to deploy
the platform.

The recommended layout is as follows:

.. code-block:: text

    cloud-config
    ├── inventory
    │   ├── group_vars
    │   │   ├── all
    │   │   │   ├── ceph.yml
    │   │   │   ├── cluster_issuer.yml
    │   │   │   ├── endpoints.yml
    │   │   │   ├── keepalived.yml
    │   │   │   ├── kube-prometheus-stack.yml
    │   │   │   ├── kubernetes.yml
    │   │   │   ├── neutron.yml
    │   │   │   └── secrets.sops.yml
    │   │   ├── cephs
    │   │   │   └── osds.yml
    │   └── hosts.ini
    ├── playbooks
    │   └── site.yml
    └── requirements.yml

The ``requirements.yml`` file is used to specify the atmosphere ansible collection
version that will be used to deploy the platform. Please refer to the `Release Notes`
for the version information. The file contents should look like this:

.. code-block:: yaml

    collections:
      - name: vexxhost.atmosphere
        version: 4.3.1

To generate the inventory configuration files, you can use the ``generate_workspace``
playbook to simplify the process. The following command will generate the
inventory in the specified directory:

.. code-block:: bash

    ansible-playbook -e domain_name="yourdomain.com" \
                     -e workspace_path="$(pwd)/cloud-config/inventory" \
                     vexxhost.atmosphere.generate_workspace

The ``cloud-config`` directory can be managed by any SCM tool of your choice, such as Git,
and can be used to store all the configuration files and secrets required to deploy the
platform.  You also need to assign the domain name of your cluster to the domain_name
variable for production deployments.

Refer to the other sections of the `Deployment Guide` to update the configuration files
according to your network and hardware specification in the inventory directory.

The file contents should look like this:

.. code-block:: yaml

    collections:
      - name: vexxhost.atmosphere
        version: 4.3.1


*************
``hosts.ini``
*************

The ``hosts.ini`` file is the Ansible inventory file that will be used to deploy
the platform. It's recommended to use the following layout:

.. code-block:: ini

    [controllers]
    ctl1.cloud.atmosphere.dev
    ctl2.cloud.atmosphere.dev
    ctl3.cloud.atmosphere.dev

    [computes]
    kvm1.cloud.atmosphere.dev
    kvm2.cloud.atmosphere.dev
    kvm3.cloud.atmosphere.dev

    [cephs]
    ceph1.cloud.atmosphere.dev
    ceph2.cloud.atmosphere.dev
    ceph3.cloud.atmosphere.dev

.. admonition:: FQDN is required!

      The hostname listed in the inventory file must be a FQDN that resolves to
      the IP address of the host. If they don't, you will have failures such
      as agents failing to start, live migration failures and other transient
      and hard to diagnose issues.

**********
HTTP proxy
**********

If you nodes can only access the internet through an HTTP proxy, you will need
to set the following variables within your inventory which will make sure that
the ``containerd`` and ``dockerd`` services are able to pull images through
this HTTP proxy, as well as the ``download_artifact`` role which is used to
download artifacts for deploying the cluster.

.. code-block:: yaml

    http_proxy: http://proxy.example.com:3128
    https_proxy: http://proxy.example.com:3128
    no_proxy: localhost,127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,169.254.0.0/16,.svc,.cluster.local

If you have any other services that need to access the internet without going
through the proxy, you can add them to the ``no_proxy`` variable.
