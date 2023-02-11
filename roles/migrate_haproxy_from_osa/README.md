# `migrate_haproxy_from_osa`

This is a role that is designed to migrate a specific service from pointing
to an OpenStack Ansible deployment to an Atmosphere deployment.  It will take
care of the following:

* Comment out all of the previous records pointing at the OpenStack Ansible
  deployment
* Add a new record pointing at the Atmosphere deployment
* Reload HAproxy in order to start sending traffic to Atmosphere
