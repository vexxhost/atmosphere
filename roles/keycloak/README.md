# `keycloak`

## Database migration

The role detects an existing MySQL-backed Keycloak StatefulSet and migrates it
when the CloudNativePG database is empty. A populated PostgreSQL database is
verified before the cutover, while a partial or otherwise inconsistent database
state stops the upgrade.

The legacy workload remains stopped after the export so that MySQL and
PostgreSQL cannot diverge. The role starts a temporary operator-managed
instance named `keycloak-migration` to test the migrated database. After that
instance is ready, the role removes it and the legacy Helm release, deploys the
final `keycloak` instance, and changes the ingress to use `keycloak-service`.
Fresh databases use the configured `keycloak_admin_username` and
`keycloak_admin_password` to create the bootstrap administrator.

If the migration or cutover fails, the role removes the operator-managed
instances, recreates the legacy Helm release and ingress, and resets the
PostgreSQL database so the migration can be retried.

Run `playbooks/keycloak_database_migration.yml` to invoke the same detection and
migration tasks explicitly.
