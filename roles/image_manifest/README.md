# `image_manifest`

Since Atmosphere uses containers for all of its components, it is important to
make sure that the images are available to the cluster.  By default, all of the
images are loaded by default using the `vexxhost.atmosphere.defaults` role which
is a dependency of all of the other roles.

The `defaults` role will load all of the images from the `atmosphere_images`
variable, which by default will pull all of the different images from the
internet.  You can override this variable to use your own local registry or to
override a specific image.

Atmosphere can help you to generate this list of images (named "image manifest")
as well as mirror them to your own registry.

## Using a custom image for a specific container

If you want to use a custom image for a specific container, you will need to
first generate an image manifest that are used by Atmosphere.

> **Warning**
>
> Ansible's default behaviour is not to merge dictionaries, so if you want to
> override a specific image, you will need to copy the entire image manifest
> and then override the specific image that you want to change.

You can generate an image manifest for Atmosphere by using the following
playbook:

```bash
ansible-playbook vexxhost.atmosphere.image_manifest \
    -e image_manifest_path=/tmp/atmosphere_images.yml
```

Once you have the image manifest, you can override the specific image that you
want to change.  Once you're done, you can include this file as part of your
Atmosphere inventory so that it can be used by the other roles.

If you want to generate an image manifest with a custom registry, you can use
the `image_manifest_registry` variable:

```bash
ansible-playbook vexxhost.atmosphere.image_manifest \
    -e image_manifest_registry=registry.example.com \
    -e image_manifest_path=/tmp/atmosphere_images.yml
```

If you want to mirror the images and generate the image manifest at the same
time, check out the next section.

## Mirroring images to a local registry

If you want to mirror all of the images to a local registry, you can use the
`vexxhost.atmosphere.mirror_images` playbook.  This playbook will mirror all of
the images to a local registry and then generate an image manifest that can be
used by the other roles.

This playbook relies on the `crane` tool to mirror the images.  You can follow
the [`crane` installation instructions](https://github.com/google/go-containerregistry/blob/main/cmd/crane/README.md#installation)
to install it on your Ansible controller.

> **Note**
>
> You will need to be authenticated to the target registry using `crane` before
> you can use the playbook.  You can use the `crane auth login` command to
> authenticate to the registry.  For more information, refer to the [`crane` documentation](https://github.com/google/go-containerregistry/blob/main/cmd/crane/doc/crane_auth_login.md)

The playbook will prompt you for the target registry and the location of the
file that you want to write the image manifest to.

```bash
ansible-playbook vexxhost.atmosphere.image_manifest \
    -e image_manifest_mirror=true \
    -e image_manifest_path=/tmp/atmosphere_images.yml
```

If you want to provide the registry as a command line argument, you
can use the `image_manifest_registry` variable:

```bash
ansible-playbook vexxhost.atmosphere.image_manifest \
    -e image_manifest_registry=registry.example.com \
    -e image_manifest_mirror=true \
    -e image_manifest_path=/tmp/atmosphere_images.yml
```

Once you have the image manifest, you can include this file as part of your
Atmosphere inventory so that it can be used by the other roles, as well as
updated the `atmosphere_image_repository` variable to point to your local
registry.

> **Note**
>
> If needed, you can also set your registry to be insecure inside of the
> container runtime interface (CRI) by using the `containerd_insecure_registries`
> variable.
>
> ```yaml
> containerd_insecure_registries:
>   - registry.example.com
> ```

Once you've deployed Atmosphere, you can use the following command in order to
validate that all images are being loaded from your local registry:

```bash
kubectl get pods --all-namespaces \
    -o jsonpath="{.items[*].spec.containers[*].image}" | \
    tr -s '[[:space:]]' '\n' | \
    sort | \
    uniq -c | \
    sort -n
```

This command will list all of the images that are being used by the pods in the
cluster, which should all be pointing to your local registry.

### Mirroring a single image

If you only want to mirror a single image, you can use the
`vexxhost.atmosphere.image_manifest` playbook, it has an extra option that can
be used to specify a single image to mirror.

You can get the image name from the image manifest that is generated by the
`vexxhost.atmosphere.image_manifest` playbook.

```bash
ansible-playbook vexxhost.atmosphere.image_manifest \
    -e image_manifest_registry=registry.example.com \
    -e image_manifest_mirror=true \
    -e image_manifest_path=/tmp/atmosphere_images.yml \
    -e image_manifest_images=keystone_api
```
