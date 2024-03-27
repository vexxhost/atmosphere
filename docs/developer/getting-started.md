# Getting Started

Atmosphere uses [Molecule](https://ansible.readthedocs.io/projects/molecule/)
to test the entire set of roles and modules that deploy Atmosphere.  However,
you can easily get started with a simple VM that has Docker installed on it.

## Dependencies

You can get started on any type of system, however, we recommend using an Ubuntu
system since that is what we use for our CI/CD pipelines, however you may adapt
these instructions to your own operating system.

!!! danger

    These instructions must be ran on a clean system, and they will perform
    destructive actions on your system.  Please make sure that you **DO NOT**
    run this on your own laptop or something similar.

1. Remove packages known to cause issues 

   ```bash
   sudo apt-get purge snapd
   ```

1. Install operating system dependencies

   ```bash
   sudo apt-get install gcc python3.10-dev ... poetry docker # TODO
   ```

1. Install Python dependencies

   ```bash
   poetry install --with dev
   ```

## Scenarios

You can choose to deploy any of the following scenarios, however, we recommend
starting with the Ceph scenario since it is the easiest to get started with.

- Ceph (basic, recommended for testing): `ceph`
- SSO (Keycloak + Monitoring + Keystone + Horizon): `keycloak`

If you'd like to deploy an environment with one of the scenarios, you can simply
run the following command on your local system with the name of the scenario
you'd like

```bash
poetry run molecule converge -s <scenario>
```

If you want to expose your local instance to the outside world, or if you are
running this on a remote system, you can use the `HOST_IP` environment variable.

```bash
HOST_IP=1.2.3.4 poetry run molecule converge -s <scenario>
```

Once this is done, you're able to login to the Docker container that is running
Atmosphere by running the following command:

```bash
poetry run molecule login -s <scenario>
```
