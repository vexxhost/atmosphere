=======
Ingress
=======

The ingress component is the primary entry point for all traffic to the cluster,
it is currently deployed as an instance of ``ingress-nginx``.  It is tuned to work
out of the box and should require no changes

.. admonition:: Warning
  :class: warning

  The ingress component is a critical part of the cluster, and should be
  managed with care.  Any changes to the ingress configuration should be
  carefully reviewed and tested before being applied to the cluster.

  If you make any changes to the ingress configuration, you may see a small
  outage as the ingress controller is restarted.

**********
Helm Chart
**********

The ingress component is deployed using the ``ingress-nginx`` helm chart.  The
chart is configured with a number of values to ensure it works correctly with
the cluster out of the box, however, you can override these values by adding
the following to your inventory:

.. code-block:: yaml

  ingress_nginx_helm_values:
    foo: bar

These values will be merged with the default values in the chart, and will be
used to configure the ingress controller.

***********************
TLS Version and Ciphers
***********************

To provide the most secure baseline configuration possible, ``ingress-nginx``
defaults to using TLS 1.2 and 1.3 only, with a `secure set of TLS ciphers <https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#ssl-ciphers>`_.

Verifying TLS Version and Ciphers
=================================

In order to check the TLS version and ciphers used by the ingress controller,
you can use the [sslscan](https://github.com/rbsec/sslscan) tool:

.. code-block:: console

  sslscan dashboard.cloud.example.com

Legacy TLS
==========

The default configuration, though secure, does not support some older browsers
and operating systems.

In order to change this behaviour, you can make to make the following changes
to the ``ingress_nginx_helm_values`` variable, the following example is using the
`Mozilla SSL Configuration Generator <https://ssl-config.mozilla.org/#server=nginx&config=old>`_
configured for the *old* profile:

.. code-block:: yaml

  ingress_nginx_helm_values:
    controller:
      config:
        ssl-protocols: "TLSv1 TLSv1.1 TLSv1.2 TLSv1.3"
        ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA"
