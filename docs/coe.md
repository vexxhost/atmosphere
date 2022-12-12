# Coe

Create COE cluster template.
```shell
# Replace using openstack_helm_endpoints_magnum_registry_host
magnum_registry_host=REPLACE_IT

for version in v1.23.13 v1.24.7 v1.25.3; do \
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
        --label container_infra_prefix="${magnum_registry_host}/magnum/"
        k8s-${version};
done;
```
