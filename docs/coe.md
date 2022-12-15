# Coe

Create COE k8s cluster templates.

```shell
for version in v1.23.13 v1.24.7 v1.25.3; do
  openstack coe cluster template create \
        --image $(openstack image show ubuntu-2004-${version} -c id -f value) \
        --external-network public \
        --dns-nameserver 8.8.8.8 \
        --master-lb-enabled \
        --master-flavor m1.medium \
        --flavor m1.medium \
        --network-driver calico \
        --docker-storage-driver overlay2 \
        --coe kubernetes \
        --label kube_tag=${version} \
        k8s-${version};
done;
```

A container registry which includes all container images required for COE k8s
clusters is installed along side with Magnum. Instead of using external container
registries, you can use this internal one.

Append `--label container_infra_prefix="${magnum_registry_host}/magnum/"` in
cluster create command. Replace `magnum_registry_host` with
`openstack_helm_endpoints_magnum_registry_host` ansible variable.
