# `magnum`

## Creating cluster templates

By default, Atmosphere deploys a set of images for Kubernetes. These cover a
range of Kubernetes versions, from 1.23.13 to 1.25.3.   You can create the
cluster templates for them with the following command:

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
        --label boot_volume_size=40 \
        --label container_infra_prefix=$(kubectl -n openstack get ingress/container-infra-registry -ojsonpath='{.spec.rules[0].host}') \
        k8s-${version};
done;
```

> **Note**
>
> This command will configure the clusters to use the internal container registry
> hosted by Atmosphere to avoid the need to talk to external registries. If you
> want to use an external registry, you can remove the `--label container_infra_prefix`.
