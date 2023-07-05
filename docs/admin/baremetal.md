# Bare Metal Service

The bare metal service is a service that allows you to provision bare metal
servers.

## Deployment

In order to deploy the bare metal service successfully, you must carry some
careful planning in order to ensure that the service is deployed correctly.

### Networking

The bare metal service requires a total of 3 networks in order to be deployed:

Public
: This network is used to provide access to the bare metal servers for
  the end users.

Bare metal
: This network is used by the bare metal service to complete operations such as
  provisioning & decommissioning of bare metal servers.

BMC
: This network is used by the bare metal service to communicate with the BMC of
  the bare metal servers.

You can reference the following table to get an idea of which network needs to
be available to which service:

|                                 | Public | Bare metal | BMC |
|---------------------------------|--------|------------|-----|
| **Neutron Network**             |    ✅   |      ✅     |  ❌  |
| **Accessible by everyone**      |    ✅   |      ❌     |  ❌  |
| **Accessible by control plane** |    ✅   |      ✅     |  ✅  |

!!! note

    If you have an environment where you are not able to let the bare metal
    service manage your switches (to change VLANs), it's suggested to use the
    public network for the bare metal network, you can do so by setting the
    following:

    ```yaml
    ironic_bare_metal_network_manage: false
    ironic_bare_metal_network_name: public
    ```
