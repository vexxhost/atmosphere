# `migrate_db_from_mariadb`

This is a role that is designed to migrate the database of service
from Openstack Helm Mariadb to Atmosphare Percona XtraDB Cluster(PXC)
deployment. It will take care of the following:

* Check if Openstack service uses Mariadb from etc secret of service.
If it uses PXC already, stop.
* Ensure that the database does not exist in the PXC database already.
If exists, stop.
* Shut off all of the containers that are using the database (This step is not included in the role. Need to be done outside of this role scope.)
* Dump the database from the OpenStack Helm Mariadb database
* Restore the database into the PXC database
