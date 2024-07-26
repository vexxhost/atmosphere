#############
Upgrade Guide
#############

There can be prepare works before perform upgrade Atmosphere cross branch.

This document will provide guideline for Atmosphere upgrade.

General Upgrade process
=======================

Upgrade Atmosphere in general just need to tag new Atmosphere version.
You can reference deployment guideline for more detail.

Cross branch Upgrade
====================

Here we documentation some breaking changes that need to be in place for upgrade.

stable/zed to stable/2023.1
---------------------------

Here are items that need to check before run upgrade from stable/zed to stable/2023.1:
  * Add Ansible Global Variables `rabbitmq_skip_spec_diff` with value `true`.
    Because RabbitMQ cluster spec changed when across stable/zed to stable/2023.1.

  * Following Helm releases should be uninstall due to CRD changed:

    * prometheus-pushgateway
    * rabbitmq-messaging-topology-operator
    * node-feature-discovery-worker
