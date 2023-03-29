# `manila`

## Manila Configs:

We currently only enable NFS for share backend protocol
With single backend option that enables DHSS(driver_handles_share_servers)
Here's detail for default backend configs in /etc/manila/manila.conf
```
[generic]
driver_handles_share_servers = true
service_image_name = manila-service-image
service_instance_flavor_id = {manila_flavor_id}
service_instance_password = manila
service_instance_user = manila
share_backend_name = GENERIC
share_driver = manila.share.drivers.generic.GenericShareDriver
```
What this backend config shows:
* Enabled DHSS that uses OpenStack Cinder, Nova, Neutron,
  and Glance to create and manage Manila share service and NFS servers.

* Using image https://object-storage.public.mtl1.vexxhost.net/swift/v1/b98c5fdfb9be4e39a34b93d0b425ac2b/atmosphere-images/manila-{{ atmosphere_version }}.qcow2 (manila-ubuntu-minimal)

* For every share will create one Nova instance with this spec, that run as NFS server fsing flavor with specs:
  * manila_flavor_name: m1.manila
  * manila_flavor_vcpus: 2
  * manila_flavor_ram: 2048
  * manila_flavor_disk: 20

* access key (public and private): Keys are generated and stored in Kubernetes secret (default to manila-ssh-keys) under OpenStack namespace and also mounted in manila service pods. With above key, you can access to any manila share instance that build based on this backend. You can find the key path in backend config:
  * path_to_private_key: /etc/manila/ssh-keys/id_rsa
  * path_to_public_key: /etc/manila/ssh-keys/id_rsa.pub

It's possible to config multiple backends, so share type can pick different setting if valid.
And define different section in config like `[generic2]` or  `[generic_no_dhss]`
But if only DHSS mode, than probably single backend config is enough.

by default we created both share type and share group type call default.
Which both mapping to generic share backend.

## Manila User guide:

Before create share NFS service, user need to make sure there is neutron network and subnet created and routed.
And now, we can create share network that point to the neutron network and subnet so can be use as later share access control.
In Dashboard it's under Project->Share->Share Networks
![Image](https://object-storage.public.mtl1.vexxhost.net/swift/v1/d7594b0298b54bcc9e4e0f252e1da2e4/atmosphere-resources/images/Manila/Share-Details-OpenStack-Dashboard.png)

In CLI:
```shell
    openstack share network create --neutron-net-id private --neutron-subnet-id private-subnet --name share-net
```

As there already a default share type, User can directly create share without specify/create another share type.

In Dashboard it's under Project->Share->Shares
![Image](https://object-storage.public.mtl1.vexxhost.net/swift/v1/d7594b0298b54bcc9e4e0f252e1da2e4/atmosphere-resources/images/Manila/Shares-OpenStack-Dashboard.png)

In CLI:
```shell
    openstack share create --share-network d5b417e6-f07c-4c0f-9ed1-a211c392aaaa --name <SHARE_NAME> NFS <SIZE>
```

At this point, share server is creating, and you can check shares and wait for it to be ready.

When a share is created, check export_locations and use the path for later mount with.
Like `10.254.0.13:/shares/share-448e0e2e-2b50-4304-9808-ee17d358d040` in following Dashboard example:
![Image](https://object-storage.public.mtl1.vexxhost.net/swift/v1/d7594b0298b54bcc9e4e0f252e1da2e4/atmosphere-resources/images/Manila/Share-Details-OpenStack-Dashboard.png)


Once the share service is ready, you can build other Instances to test that share service.
Make sure the test instance created in that network and subnet that you use when creating
share network (private and private-subnet in this case).
And now create access rule for that test instance can access to NFS server.

In Dashboard it's under Project->Share->Shares->Edit Rules

![Image](https://object-storage.public.mtl1.vexxhost.net/swift/v1/d7594b0298b54bcc9e4e0f252e1da2e4/atmosphere-resources/images/Manila/Share-Rules-OpenStack-Dashboard.png)

In CLI:

```shell
openstack share access create <SHARE_NAME> ip <Test_Instance_IP>
```

Now back to the test instance, and you can run mount command like this:
```shell
    mount -vt nfs 10.254.0.13:/shares/share-448e0e2e-2b50-4304-9808-ee17d358d040 /mnt
```

Note: in the test instance, make sure you have NFS tools ready before you mount NFS server.
Like in ubuntu sudo apt install nfs-common

## Manila Admin guide:
The default share type provide general NFS share service.

If you also planning to have snapshot or other method support, you can create new share type:

In Dashboard it's under Admin->Share->Share Types
![Image](https://object-storage.public.mtl1.vexxhost.net/swift/v1/d7594b0298b54bcc9e4e0f252e1da2e4/atmosphere-resources/images/Manila/Share-Types-OpenStack-Dashboard.png)

For more info about share type extra spec, you can reference [`Capabilities and Extra specs`](https://docs.openstack.org/manila/latest/admin/capabilities_and_extra_specs.html#share-type-common-capability-extra-specs-that-are-visible-to-end-users)

In CLI:
```shell
    openstack share type create --snapshot-support true --create-share-from-snapshot-support true  --revert-to-snapshot-support false --mount-snapshot-support false --public true sharetype1 true
```
    Note: --revert-to-snapshot-support and --mount-snapshot-support are not supported in Generic (Cinder as back-end) Backend.

Make sure the type function is correct.
You can cross reference with the function mapping in (https://docs.openstack.org/manila/latest/admin/share_back_ends_feature_support_mapping.html).

In advance, Share Security service also recommended for advance using.
That will help to integrate either LDAP, Kerberos, or Microsoft Active Directory
for share network authentication and authorization,
please check [`this doc`](https://docs.openstack.org/manila/latest/admin/shared-file-systems-security-services.html) for more detail
