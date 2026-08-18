# keycloak_database_migration

Migrates a running Keycloak 24 deployment from MySQL/PXC to a dedicated
PostgreSQL 15 database using Keycloak's directory export and import commands.

Before running the migration, configure these deployment settings:

```yaml
keycloak_database_vendor: postgres
keycloak_postgresql_host: keycloak-postgresql.example.internal
keycloak_postgresql_secret_name: keycloak-postgresql
keycloak_postgresql_secret_key: password
```

The application secret must be in `auth-system`, and the PostgreSQL database
must be empty. The migration stops Keycloak for a consistent export, uses the
image from the current StatefulSet for both jobs, and restores the
MySQL-backed release when a job or cutover fails.
