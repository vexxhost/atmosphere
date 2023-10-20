# Repositories

Atmosphere uses a few different Git repositories to host the code for the
project.  This document explains how to work with the different repositories,
their purpose, and how to maintain them.

## Creating a new fork

In order to create a new fork of a repository, we'll need to create a fork
under the `vexxhost` organization.  In this example, we'll assume that you're
creating a fork of the `openstack/horizon` project.

In order to fork the project, you'll start with the following command which
assumes that you have the `gh` command line tool installed:

```bash
./hack/repos/fork openstack/horizon
```

> **Note**
>
> If this is an OpenStack project, once you're done, you'll also need to update
> the `FORKED_PROJECTS` variable in the
> `internal/pkg/image_repositories/build_workflow.go` file to include the newly
> forked project.

## Applying patches

The only time that it is necessary to apply patches to the forked repositories
is when there is a fix that has not yet been merged upstream.  In order to
apply a patch, you can use the following command which includes the project
name and either a Gerrit URL or a GitHub pull request URL:

```bash
./hack/repos/patch horizon https://review.opendev.org/c/openstack/horizon/+/874351/
```

This command will take care of automatically cloning the project, downloading
the patch, and applying it to the repository.  Once the patch has been applied,
it will push it in a new branch to the forked repository and create a pull
request.

> **Note**
>
> If the process fails because of a merge conflict, you'll need to resolve the
> conflict and then run the command again.

## Cherry-picking patches

If you need to cherry-pick a patch from one branch of a forked repository to
another, you can use the following command:

```bash
./hack/repos/cherry-pick magnum fbfd3ce9a3 stable/zed
```

In the example above, this will cherry-pick the commit `fbfd3ce9a3` from the
`master` branch of the `magnum` repository and create a pull request to apply
it to the `stable/zed` branch.

## OpenStack

Atmosphere has a few forks of the OpenStack repositories.  These are used to
apply patches to the upstream code that contain fixes which have not yet been
merged upstream.  The list of forked repositories is as follows:

* [openstack/horizon](https://github.com/vexxhost/horizon)
* [openstack/keystone](https://github.com/vexxhost/keystone)
* [openstack/magnum](https://github.com/vexxhost/magnum)
* [openstack/magnum-ui](https://github.com/vexxhost/magnum-ui)
