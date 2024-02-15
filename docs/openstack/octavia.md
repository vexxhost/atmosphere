# Octavia

## Accessing Amphorae

Atmosphere configures an SSH keypair which allows you to login to the Amphorae
for debugging purposes.  The `octavia-worker` containers are fully configured
to allow you to SSH to the Amphorae.

If you have an Amphora running with the IP address `172.24.0.148`, you can login
to it by simply executing the following:

```bash
kubectl -n openstack exec -it deploy/octavia-worker -- ssh 172.24.0.148
```
