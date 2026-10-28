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
begins on the destination host, so the guest arrives with only the DAC label:

.. code-block:: yaml

   libvirt_helm_values:
     conf:
       hooks:
         enabled: true
         scripts:
           qemu: |
             #!/usr/bin/env python3
             # Called as: /etc/libvirt/hooks/qemu <guest> <operation> <sub-op> <extra>
             #
             # For "migrate begin", libvirt passes the incoming domain XML on
             # stdin and uses whatever this script prints in its place. Printing
             # nothing keeps the original XML, which this script does for every
             # other operation, when there is nothing to strip, and on errors, so
             # the hook is never the reason a migration fails.

             import sys
             import xml.etree.ElementTree as ET
             from io import StringIO


             def strip_apparmor(xml):
                 # Keep the original namespace prefixes (such as the "nova:"
                 # metadata) instead of generated ns0/ns1 ones.
                 for _, (prefix, uri) in ET.iterparse(StringIO(xml), events=("start-ns",)):
                     ET.register_namespace(prefix, uri)

                 root = ET.fromstring(xml)
                 removed = 0
                 # Domain level <seclabel> and per-device <source><seclabel>.
                 for parent in root.iter():
                     for child in list(parent):
                         if child.tag == "seclabel" and child.get("model") == "apparmor":
                             parent.remove(child)
                             removed += 1

                 if not removed:
                     return None
                 return ET.tostring(root, encoding="unicode")


             def main():
                 if len(sys.argv) < 3 or sys.argv[2:4] != ["migrate", "begin"]:
                     return 0

                 xml = sys.stdin.read()
                 try:
                     out = strip_apparmor(xml)
                 except Exception as exc:
                     sys.stderr.write("qemu hook: leaving XML unchanged: %s\n" % exc)
                     return 0

                 if out:
                     sys.stdout.write(out)
                 return 0


             if __name__ == "__main__":
                 sys.exit(main())

The chart renders each script as a Helm template, so escape any literal
``{{`` sequences in your scripts.

.. note::

   Libvirt only looks for hook scripts when it starts. Adding, changing or
   removing a script triggers a rolling restart of the libvirt pods, one node
   at a time.
