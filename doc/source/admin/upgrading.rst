#############
Upgrade Guide
#############

This document shows the most common way of upgrading your Atmosphere deployment.

.. admonition:: Avoid jumping Atmosphere major releases
    :class: warning

    It is important to avoid jumping major versions in Atmosphere, which is the
    same advice in OpenStack.

    For example, If you are running Atmosphere Zed release (version 1) and want
    to move to Bobcat (version 3) you should perform 2 upgrades: version 1 to
    version 2 and then version 3.

    If you dont do this, you may face database inconsistencies and failures on
    services like Nova or Neutron, or failed upgrades of components such as
    RabbitMQ.

**************************
Preparing the environment
**************************

On the deployment box, or any other place that you have your Ansible inventory,
you should update the ``requirements.yml`` file and point to the target
Atmosphere release you want to upgrade to.

.. code-block:: yaml

  collections:
  - name: vexxhost.atmosphere
    version: X.Y.Z

Once that is done, you should update your collections by running:

.. code-block:: console

    $ ansible-galaxy install -r requirements.yml --force

It's important to review your inventory, specifically image overrides to make
sure that the image overrides are still necessary, otherwise you may end up
with a broken deployment since the images will not be the ones the Atmosphere
collection expects.

*******************
Running the upgrade
*******************

You can either execute the entire upgrade by running your site-local playbook
which imports ``vexxhost.atmosphere.site``, call the individual playbooks out
of Atmosphere or run a specific tag if you want to upgrade service-by-service
which gives you the most granular control.

.. code-block:: console

    $ ansible-playbook -i hosts.ini playbooks/site.yml

You can also run the Atmosphere provided playbooks by pointing to a specific
playbook of the Ansible collection, in this case, the Ceph playbook:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.ceph

You also have the most granular control by running the tags of the playbooks,
for example, if you want to upgrade the Keystone service, you can run the
following command:

.. code-block:: console

    $ ansible-playbook -i hosts.ini vexxhost.atmosphere.openstack --tags keystone

During the upgrade, you may find it useful to have a monitor on all of the pods
in the cluster to ensure that they are becoming ready and not failing. You can
do this by running the following command:

.. code-block:: console

    $ watch -n1 "kubectl get pods --all-namespaces -owide | egrep -v '(Completed|1/1|2/2|3/3|4/4|6/6|7/7)'"

******************************
Release-specific upgrade notes
******************************

Upgrading to 8.x (OpenStack 2026.1)
===================================

* The OpenStack service images are now built on Debian 13 with Python 3.13
  (see :doc:`../arch/images`). Remove image overrides for OpenStack services
  unless the images are built for OpenStack 2026.1 on the same base, since
  images built for an older release or on Ubuntu are not compatible.
* If you override ``wsgi_keystone`` in ``keystone_helm_values``, change
  ``WSGIScriptAlias`` to ``/var/www/cgi-bin/keystone/wsgi.py``.
* RabbitMQ is upgraded to 4.2 and the Percona XtraDB Cluster operator to 1.19.
  Both only support upgrades from specific versions, so the deployment stops
  with an error before changing a cluster that is too old.
* If you override ``rabbitmq.additionalConfig``, keep
  ``deprecated_features.permit.transient_nonexcl_queues = true`` in it. The
  OpenStack services need it, and RabbitMQ 4.3 in the next release requires it
  on every node before upgrading.
* The libvirt and QEMU versions on the compute nodes do not change, so live
  migration keeps working in both directions during the upgrade.

Upgrading to 9.x (OpenStack 2026.2)
===================================

* Upgrade to 8.x first. OpenStack 2026.2 does not support upgrades from
  2025.2, and RabbitMQ 4.4 and the Percona XtraDB Cluster operator 1.20 need
  the versions that 8.x installs.
* The Compute service no longer supports Linux bridge networking. If a
  deployment migrated from OpenStack-Ansible still uses Linux bridge, move it
  to Open vSwitch or OVN before upgrading.
* RabbitMQ 4.3 and later only support the Khepri metadata store. The upgrade
  enables Khepri on every RabbitMQ cluster before upgrading it, which needs a
  majority of each cluster's nodes to be online.
* The compute nodes move to libvirt 12.0.0 and QEMU 10.2.1 on Ubuntu 26.04.
  Guests started on a host that still runs 8.x can live-migrate to an upgraded
  host, but guests cannot migrate from an upgraded host back to one running
  8.x. Running guests keep their QEMU version until they are live-migrated or
  restarted, so once every compute node is upgraded, live-migrate guests
  between upgraded hosts to move them to the new QEMU.
