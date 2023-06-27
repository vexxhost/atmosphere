# OpenStack image sharing with specific members

You can share an image from your project with a collaborator in a different
project in OpenStack cloud so you can both launch instances using the same image.
As the owner of the image, you can revoke the sharing privilege at any time.
You can also use these methods to share an image with yourself in other projects,
just think of yourself as the collaborator.

## Prerequisites

* Both you and your collaborator need to use the OpenStack CLI.
You will need to set up the CLI to work with the project where the image to be
shared is located.
If you are sharing an image with yourself, you will need to download the
authentication RC file for both projects (the one you are sharing from and to).

* You will need to know the project name or ID of your collaborator.

## Share an Image With Another Project

* Find the project ID of your collaborator first

The project ID is the string of the UUID format. The project name in the typical
format will not work in the below commands. You will need to have sourced the
RC file of the project where the image is located before running the OpenStack
CLI command to get the project ID:

```sh
openstack project list
```

And the first field of the output is the ID of your collaborator's project ID.
If you know the name of your collaborator's project,
you can find the ID by adding `| grep <project name for collaborator>` to the above command.

* Find the ID of the image you want to share

```sh
openstack image show <image name>
```

Similar to project ID, this will be a long string of letters and
numbers next to the name of your image.
You will use the image ID, rather than the name, in the commands below.

* Share the image with your collaborator's project

```sh
openstack image set --shared <image ID>
openstack image add project <image ID> <project ID for collaborator>
```

* Verify the image is now shared

```sh
openstack image member list <image ID>
```

The status field should say pending until your collaborator accepts the image.

* Give the ID of the shared image to your collaborator so they can follow the
steps in the `Accept a Shared Image` section to add the image to their project.
If you are sharing the image with yourself, you will need to source the RC file
of the second project and then perform the acceptance yourself.

## Accept a Shared Image

Steps to accept a shared image:

* Get the ID of the shared image from the owner. Make sure the owner has performed
the steps in the Share an Image section above, and source the RC file of your project.

* Accept the shared image

```sh
openstack image set --accept <image ID>
```

* Verify the image is now available to your project

```sh
openstack image list
```

If the image is listed in the output, it should also appear in
OpenStack dashboard.

## Unshare an Image

An image's owner can see which projects have access to the image:

```sh
openstack image member list <image ID>
```

The owner can unshare an image like this:

```sh
openstack image remove project <image ID> <project ID>
```

## Share an Image with All Projects

Here we show you how to set up images for share without setting membership.

### Share with `community` option

An image can be shared with all users of the cloud.
Images shared in this way are referred to as `community`
images because they’re available to the entire community of users in a cloud.

For community images:

* Who-users within same project:

  * have this image in the default image list
  * can see image detail for this image
  * can boot from this image

* Who-all users:

  * do not have this image in their default image list
  * can see image detail for this image
  * can boot from this image

```sh
openstack image set --community <image ID>
```

> Note: this action can also be performed in dashboard too.

#### Allow community image to show up in image list

As mentioned above, you don't need to add any member to image to use
the `community` image, but if you wish to allow a community image shows
up in image list you can.
You need to add your project ID as member for that image like this:

```sh
openstack image add project <image ID> <project ID for collaborator>
```

And follow the `Accept a Shared Image` section to grant that request.

### Share with `public` option

An image can be shared with all users of the cloud.
Currently this action can only be performed by cloud administrators.

For public images:

* Who-all users:

  * have this image in the default image-list
  * can see image detail for this image
  * can boot from this image

This generally shouldn't be done unless creating something
that is a public resource that is intended to be used with any project.
Additionally, don't use such an image from a third party unless you
trust the source.

```sh
openstack image set --public <image ID>
```

> Note: this action can also be performed in dashboard too.
