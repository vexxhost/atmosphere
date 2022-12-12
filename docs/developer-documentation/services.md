# Services

## OpenStack

Atmosphere deploys a set of OpenStack services to provide a cloud environment
for users. The OpenStack services are deployed using the Helm charts which are
provided by the [OpenStack-Helm](https://opendev.org/openstack/openstack-helm)
project.

The idea is that the use and combination of those services should be transparent
to the user consuming those services, which makes Atmosphere an opinionated
deployment tool.

### Fully Supported Services

The following OpenStack services are included, fully supported and integrated
together out of the box inside Atmosphere.

- [Keystone](https://docs.openstack.org/keystone/latest/)
- [Barbican](https://docs.openstack.org/barbican/latest/)
- [Glance](https://docs.openstack.org/glance/latest/)
- [Cinder](https://docs.openstack.org/cinder/latest/)
- [Placement](https://docs.openstack.org/placement/latest/)
- [Neutron](https://docs.openstack.org/neutron/latest/)
- [Nova](https://docs.openstack.org/nova/latest/)
- [Senlin](https://docs.openstack.org/senlin/latest/)
- [Heat](https://docs.openstack.org/heat/latest/)
- [Horizon](https://docs.openstack.org/horizon/latest/)
- [Octavia](https://docs.openstack.org/octavia/latest/)
- [Designate](https://docs.openstack.org/designate/latest/)

### Planned Supported Services

The following OpenStack services are planned to be included, fully supported and
integrated together out of the box inside Atmosphere.  This is a priority-ordered
list of services that are planned to be included in the future.

- [Magnum](https://docs.openstack.org/magnum/latest/)
- [Swift](https://docs.openstack.org/swift/latest/) via RADOS Gateway
- [Manila](https://docs.openstack.org/manila/latest/)
- [Ironic](https://docs.openstack.org/ironic/latest/)
- [Masakari](https://docs.openstack.org/masakari/latest/)
- [Trove](https://docs.openstack.org/trove/latest/)
- [Sahara](https://docs.openstack.org/sahara/latest/)
- [Zaqar](https://docs.openstack.org/zaqar/latest/)

!!! note

   The list of services is not final and may change over time, with no promised
   timeline on the addition of those feature.  If you would like to sponsor the
   development of a specific service, please [contact us](https://vexxhost.com/contact-us/).
