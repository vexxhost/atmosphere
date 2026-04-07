======================
Environment Deployment
======================

After you create the inventory, and update the configuration files for OpenStack services,
Kubernetes, Ceph and certificates, you can deploy the Atmosphere platform using the following
commands:

.. code-block:: bash

    python3 -m venv atmosphere-venv && source atmosphere-venv/bin/activate

    pip install -r atmosphere/requirements.txt
    cd cloud-config
    ansible-galaxy install -r requirements.yml
    ansible-playbook -i inventory/hosts.ini  -u ubuntu -b playbooks/site.yml

It's suggested to run the deployment process from a dedicated machine that
has ssh access to all the hosts in the inventory file.

You can edit the site.yml to include only the roles that you need to deploy
if you want to deploy only a subset of the platform at a time.
