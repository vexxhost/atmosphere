# Getting Started

We've got a few different Molecule scenarios which help you get up to speed fast
in order to develop for a specific feature set.  The primary requirement for
those scenarios is that you have a working Docker installation.

## Molecule

If you'd like to validate one of the feature sets, you can simply run the
following command on your local system with the name of the scenario you'd like

```bash
molecule converge -s <scenario>
```

If you want to expose your local instance to the outside world, or if you are
running this on a remote system, you can use the `HOST_IP` environment variable.

```bash
HOST_IP=1.2.3.4 molecule converge -s <scenario>
```

### Scenarios

- SSO (Keycloak + Monitoring + Keystone + Horizon): `keycloak`
