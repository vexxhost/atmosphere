# `keystone_pre`

This role performs the Keycloak-side setup required by Keystone — realm
creation, MFA configuration, OpenID Connect client registration, and the
OpenID metadata ConfigMap. It runs in parallel with the main `keystone`
role so the Keystone Helm install does not have to wait for Keycloak to
finish starting up.
