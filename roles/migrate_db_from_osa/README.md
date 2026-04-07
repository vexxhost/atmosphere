# `migrate_db_from_osa`

This is a role that is designed to migrate the database of service from an
OpenStack Ansible deployment to an Atmosphere deployment.  It will take care
of the following:

* Ensure that the database does not exist in the Atmosphere database
* Shut off all of the containers that are using the database
* Dump the database from the OpenStack Ansible database
* Restore the database into the Atmosphere database
