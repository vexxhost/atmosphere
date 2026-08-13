######
Ironic
######

**************************************
Use the bare metal graphical console
**************************************

Atmosphere can deploy ``ironic-novncproxy``, expose its HTTPS endpoint, and let
the Ironic conductor create short-lived console Pods with the Kubernetes
console provider. Graphical console support is disabled by default. Enable it
only after selecting a console application compatible with the target BMC and
pinning that image by digest:

.. code-block:: yaml

   ironic_vnc_image: >-
     registry.example.com/ironic-console@sha256:<digest>
   ironic_vnc_enabled: true

Ironic keeps both ``redfish-graphical`` and ``no-console`` registered. Select
the graphical interface only for nodes whose BMC supports the configured
console image:

.. code-block:: console

   openstack baremetal node set <node> \
     --console-interface redfish-graphical
   openstack baremetal node console enable <node>
   openstack baremetal node console show <node>

Do not configure ``redfish-graphical`` as the global default when the
deployment contains hardware types that do not support it.

The image must implement Ironic's ``APP`` and ``APP_INFO`` contract and listen
for TCP RFB connections on port 5900. To change the console application,
replace the image with another immutable reference:

.. code-block:: yaml

   ironic_vnc_image: >-
     registry.example.com/ironic-console@sha256:<digest>

Disable all bare metal graphical console infrastructure when it is not needed:

.. code-block:: yaml

   ironic_vnc_enabled: false
