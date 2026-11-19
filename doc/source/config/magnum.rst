######
Magnum
######

Atmosphere deploys Magnum with the `Cluster API driver for Magnum
<https://github.com/vexxhost/magnum-cluster-api>`_, together with Cluster API
and the Cluster API provider for OpenStack.

***********************
Keystone authentication
***********************

The Magnum chart sets ``keystone_authtoken.www_authenticate_uri`` to a Keystone
v3 URL for trustee authentication. It uses the internal identity endpoint by
default, including when the shared endpoint path is ``/``. Existing
``auth_uri`` overrides supply the base URL, and explicit
``www_authenticate_uri`` values take precedence.

Recent identity middleware releases no longer read the deprecated ``auth_uri``
option. The supported option lets commands such as ``openstack coe cluster
list`` authenticate the trustee domain administrator without an HTTP 500 error.

To use a different URL, set the following Helm override:

.. code-block:: yaml

   magnum_helm_values:
     conf:
       magnum:
         keystone_authtoken:
           www_authenticate_uri: https://identity.example.com/v3

*****************************************
Kubelet serving certificate verification
*****************************************

Clusters created with the ``kubelet_serving_cert_verification_enabled=true``
label give every kubelet a serving certificate signed by the cluster CA, and
the Kubernetes API server verifies it when it connects to a kubelet, for example
for ``kubectl logs`` and ``exec``.

Kubernetes doesn't approve these certificates on its own, so Atmosphere installs
`cluster-api-csr-approver <https://github.com/vexxhost/cluster-api-csr-approver>`_
next to Cluster API.  It approves a request only when every name and IP address
in it belongs to the OpenStack server behind that node, and it doesn't need any
configuration.

See the `driver documentation
<https://vexxhost.github.io/magnum-cluster-api/admin/kubelet-serving-certificates/>`_
for details and troubleshooting.
