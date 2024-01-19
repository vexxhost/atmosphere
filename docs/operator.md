# Operator Documentation

## OVN

## Recovering cluster

If any of the OVN database pods fail, they will no longer be ready.  You can
recover the cluster by deleting the pods and allowing them to be recreated.

For example, if the `ovn-ovsdb-nb-0` pod fails, you can recover the cluster by
deleting the pod:

```bash
kubectl -n openstack delete pods/ovn-ovsdb-nb-0
```

If the entire cluster fails, you can recover the cluster by deleting all of the
pods.  For example, if the southbound database fails, you can recover the
cluster with this command:

```bash
kubectl -n openstack delete pods -lcomponent=ovn-ovsdb-sb
```

If the state of Neutron is lost from the cluster, you can recover it by running
the repair command:

```bash
kubectl -n openstack exec deploy/neutron-server -- \
  neutron-ovn-db-sync-util \
    --debug \
    --config-file /etc/neutron/neutron.conf \
    --config-file /tmp/pod-shared/ovn.ini \
    --config-file /etc/neutron/plugins/ml2/ml2_conf.ini \
    --ovn-neutron_sync_mode repair
```

## Octavia

### Accessing Amphorae

Atmosphere configures an SSH keypair which allows you to login to the Amphorae
for debugging purposes.  The `octavia-worker` containers are fully configured
to allow you to SSH to the Amphorae.

If you have an Amphora running with the IP address `172.24.0.148`, you can login
to it by simply executing the following:

```bash
kubectl -n openstack exec -it deploy/octavia-worker -- ssh 172.24.0.148
```
