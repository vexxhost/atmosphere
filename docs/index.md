# Atmosphere

## Quick-start

### All-in-one

The easiest way to get started with Atmosphere is to deploy the all-in-one
installation.  This will install an entire stack of Atmosphere, with Ceph
and all the OpenStack services inside a single machine.

!!! info

    The all-in-one installation is not for production use, it's perfect
    for testing and development.

!!! warning

    The all-in-one will fully take-over the machine by making system-level
    changes.  It's recommended to run it inside a virtual machine or a
    physical machine that can be dedicated to this purpose.

You can deploy the all-in-one environment inside the following operating
systems:

- Ubuntu 20.04
- Ubuntu 22.04 (recommended)

You can use the following commands to deploy the all-in-one environment:

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install git python3-pip
sudo pip install poetry

# Clone the repository
git clone https://github.com/vexxhost/atmosphere.git

# Deploy AIO
cd atmosphere
sudo poetry install --with dev
sudo poetry run molecule converge -s aio
```
