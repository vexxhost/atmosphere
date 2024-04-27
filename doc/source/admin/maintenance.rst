#################
Maintenance Guide
#################

This guide provides instructions for regular maintenance tasks necessary to
ensure the smooth and secure operation of the system.

*********************
Renewing Certificates
*********************

The certificates used by the Kubernetes cluster are valid for one year.  They
are automatically renewed when the cluster is upgraded to a new version of
Kubernetes.  However, if you are running the same version of Kubernetes for
more than a year, you will need to manually renew the certificates.

To renew the certificates, run the following command on each one of your
control plane nodes:

.. code-block:: console

    $ sudo kubeadm certs renew all

Once the certificates have been renewed, you will need to restart the
Kubernetes control plane components to pick up the new certificates.  You need
to do this on each one of your control plane nodes by running the following
command one at a time on each node:

.. code-block:: console

    $ ps auxf | egrep '(kube-(apiserver|controller-manager|scheduler)|etcd)' | awk '{ print $2 }' | xargs sudo kill
