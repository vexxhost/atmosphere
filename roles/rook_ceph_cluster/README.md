# `rook_ceph_cluster`

This role connects the Ceph cluster that is deployed by Atmosphere into the
Rook operator, and then it also deploys Rados gateway to enable the Swift API.

## Using with Cyberduck

Cyberduck is a very powerful file transfer client which supports both Windows
and macOS.  It can be very useful at transferring large number of files as
well as large files.

You will need to [Download Cyberduck](https://cyberduck.io/download/) for your
appropriate operating system and install it.

In order to be able to configure the client successfully, you'll need the
following prerequisites:

* OpenStack authentication URL
* OpenStack username & password
* Project Name
* Domain Name (if you're not sure, this is usually `Default`)

> **Note**
>
> If you're not sure what your authentication URL is, you can find it by logging
> into your OpenStack dashboard and clicking on *API Access* in the left-hand
> menu bar under *Project*.  The URL will be listed under *Identity*.

Once you have the above information, you can configure the client to connect to
the Swift API by launching Cyberduck and following these steps:

1. Click on the *Open Connection* button
2. Select *OpenStack Swift (Keystone 3)* from the list of connection types
3. Enter your project, domain and username in the listed format.
4. Enter your password
5. Click *Connect*

> **Note**
>
> While you're connecting, if your cloud is setup with a self-signed
> certificate, you may see a warning about the certificate being invalid.  You
> can click on the *Continue* button to continue connecting.

At that point, you should be able to create buckets and upload files by simply
dragging and dropping them into the Cyberduck window.

> **Note**
>
> Cyberduck is free software with no feature limits.  However, if you find value
> in it, please consider making a [donation](https://cyberduck.io/donate/)
> to help support the project.
