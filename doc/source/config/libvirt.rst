#######
Libvirt
#######

*************
Hook scripts
*************

Libvirt can run `hook scripts <https://libvirt.org/hooks.html>`_ when certain
events happen, such as a guest starting, stopping or migrating. You can define
these scripts with ``libvirt_helm_values``. Each entry under
``conf.hooks.scripts`` is mounted as an executable file at
``/etc/libvirt/hooks/<name>`` inside the libvirt pods, where ``<name>`` is
one of ``daemon``, ``qemu``, ``lxc``, ``libxl``, ``bhyve`` or ``network``.

For example, guests started by a libvirt with AppArmor enabled carry an
AppArmor security label. The libvirt pods don't use AppArmor, so live migrating
these guests into Atmosphere fails with
``Security driver model 'apparmor' is not available``. The following ``qemu``
hook removes those labels from the incoming guest definition when the migration
begins on the destination host:

.. code-block:: yaml

   libvirt_helm_values:
     conf:
       hooks:
         enabled: true
         scripts:
           qemu: |
             #!/usr/bin/env python3
             import sys
             import xml.etree.ElementTree as ET

             if sys.argv[2:4] != ["migrate", "begin"]:
                 sys.exit(0)

             domain = ET.fromstring(sys.stdin.read())
             for parent in domain.iter():
                 for child in list(parent):
                     if child.tag == "seclabel" and child.get("model") == "apparmor":
                         parent.remove(child)

             print(ET.tostring(domain, encoding="unicode"))

The chart renders each script as a Helm template, so escape any literal
``{{`` sequences in your scripts.

.. note::

   Libvirt only looks for hook scripts when it starts. Adding, changing or
   removing a script triggers a rolling restart of the libvirt pods, one node
   at a time.
