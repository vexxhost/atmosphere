#############
Upgrade Guide
#############

This document shows the most common way of upgrading your Atmosphere deployment.

.. admonition:: Avoid jumping Atmosphere major releases
    :class: warning

    It's important to avoid jumping major versions in Atmosphere, which is the
    same advice in OpenStack.

    For example, If you are running Atmosphere Zed release (version 1) and want
    to move to Bobcat (version 3) you should perform 2 upgrades: version 1 to
    version 2 and then version 3.

    If you don't do this, you may face database inconsistencies and failures on
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

Once that's done, you should update your collections by running:

.. code-block:: console

    $ ansible-galaxy install -r requirements.yml --force

It's important to review your inventory, specifically image overrides to make
sure that the image overrides are still necessary, otherwise you may end up
with a broken deployment since the images won't be the ones the Atmosphere
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
in the cluster to ensure they're becoming healthy and not failing. You can
do this by running the following command:

.. code-block:: console

    $ watch -n1 "kubectl get pods --all-namespaces -owide | egrep -v '(Completed|1/1|2/2|3/3|4/4|6/6|7/7)'"
