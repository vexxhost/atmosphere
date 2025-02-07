#############
Upgrade Guide
#############

This document shows the most common way of upgrading your atmosphere deployment.

.. admonition:: Avoid Jumping Atmosphere Major releases!
    :class: warning

    It is important to avoid jumping major versions in atmosphere. It is the same
    advice on OpenStack upgrades. If you are in zed ( v1.x.x ) and want to move
    to bobcat ( v3.x.x ) you should perform 2 upgrades: v1 -> v2 -> v3. If you dont
    do this, you may face database inconsistencies and failures on services like nova
    or neutron.

**************************
Preparing the environment
**************************

On the deployment box, or any other place that you have your cloud-config
inventory, you should update the `requirements.yml` file and point to the
target atmosphere release you want to upgrade.

.. code-block:: yaml

  collections:
  - name: vexxhost.atmosphere
    version: X.Y.Z

Once that is done, you should update your collections by:

.. code-block:: console

    ansible-galaxy install -r requirements.yml --force


Review your inventory for overrides and if you still need them, mainly for
images and if they are necessary for the target release.

You can either create a site.yml playbook to mimic `upstream playbooks <https://github.com/vexxhost/atmosphere/blob/main/playbooks/site.yml>`_
or use the collections directly when running ansible playbooks, a.k.a `vexxhost.atmosphere.<playbook>` in a more controlled way
by executing each phase of the upgrade ( i.e kubernetes, ceph, csi, monitoring, openstack, etc).


*******************
Running the upgrade
*******************

You can either just let the upgrade to follow its flow by executing the playbooks mentioned above
or you can control it by running individual playbooks and its --tags so you can have a more controlled
way and see each service being upgrade.

Running all playbooks consists in:

.. code-block:: console

    ansible-playbook -i <path to inventory>/hosts.ini playbooks/site.yml


Or running individual playbooks and pointing its tags:

.. admonition:: Running with --tags
    :class: info

    The example bellow uses the `openstack.yml <https://github.com/vexxhost/atmosphere/blob/main/playbooks/openstack.yml>`_ playbook
    and pointing to a tag. You can run the tags sequencially as you successfully upgrade the target service.

.. code-block:: console

    ansible-playbook -i <path to inventory>/hosts.ini vexxhost.atmosphere.openstack --tag keystone

.. admonition:: Monitoring the upgrade
    :class: info

    Its usefull to watch the pods during the upgrade to catch issues beforehand, You can use

    .. code-block:: console

       watch -n1 "kubectl get pods --all-namespaces -owide | egrep -v '(Completed|1/1|2/2|3/3|4/4|6/6|7/7)'"
