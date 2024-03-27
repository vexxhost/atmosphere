# Building Custom OpenStack Images

## Pre-requisits

- Install [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) on your system.
- Source your OpenStack credentials ( you can use clouds.yaml or a openrc file ).

## Example of building a ubuntu cloud image with docker installed.

This example shows a simple use case of building a custom image for OpenStack. 

**NOTE** Make sure you source your OpenStack credentials to run the packer builds.

The script below spins up a VM under the user's project, installs docker, and creates an customomized image out of it. Note that a parent image is being used, in this case, a [ubuntu cloud image](https://cloud-images.ubuntu.com), which has all the necessary software to be booblable on a OpenStack Cloud.

```yaml
packer {
  required_plugins {
    openstack = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/openstack"
    }
  }
}

source "openstack" "ubuntu_custom" {
  flavor       = "<flavor name>"
  image_name   = "Ubuntu Focal Custom - Docker"
  source_image = "<image_id>"
  ssh_username = "ubuntu"
}

build {
  sources = [
    "source.openstack.ubuntu_custom"
  ]

  provisioner "shell" {
    script = "./setup-docker.sh"
  }
}
```

If successfull, you should expect as output a new image_id as the new custom cloud image.

For more examples, refer to the [official openstack builder](https://github.com/hashicorp/packer-plugin-openstack) and [packer](https://learn.hashicorp.com/tutorials/packer/docker-get-started-build-image) documentation.