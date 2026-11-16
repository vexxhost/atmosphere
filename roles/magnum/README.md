# `magnum`

## Creating cluster templates

By default, Atmosphere deploys a set of images for Kubernetes. These cover a
range of Kubernetes versions, from 1.25.11 to 1.27.3. You can create the
cluster templates for them with the following command:

```shell
for version in v1.25.11 v1.26.6 v1.27.3; do
  openstack coe cluster template create \
        --image $(openstack image show ubuntu-2204-kube-${version} -c id -f value) \
        --external-network public \
        --dns-nameserver 8.8.8.8 \
        --master-lb-enabled \
        --master-flavor m1.medium \
        --flavor m1.medium \
        --network-driver calico \
        --docker-storage-driver overlay2 \
        --coe kubernetes \
        --label kube_tag=${version} \
        --label boot_volume_size=40 \
        k8s-${version};
done;
```
