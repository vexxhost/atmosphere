# `host_libvirt_sockets`

This role stops and masks host libvirt socket-activated services before the
Kubernetes-managed libvirt DaemonSet is installed. This prevents host systemd
units from binding libvirt sockets that should be owned by the Atmosphere
deployment.

## Role Variables

* `host_libvirt_sockets_enabled`: Whether to stop and mask host libvirt units.
* `host_libvirt_sockets_units`: List of systemd units to stop and mask.
