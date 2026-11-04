######
Magnum
######

Atmosphere deploys Magnum with the `Cluster API driver for Magnum
<https://github.com/vexxhost/magnum-cluster-api>`_, together with Cluster API
and the Cluster API provider for OpenStack.

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
