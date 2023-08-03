# SSO using Keycloak

You can enable Keycloak to be the primary source of truth for authentication for the cloud and all the different components, such as OpenStack dashboard, Grafana, etc.

```yaml
atmosphere_keycloak_realm: Atmosphere
atmosphere_grafana_oauth_client_id: grafana
atmosphere_grafana_oauth_client_secret:
```
