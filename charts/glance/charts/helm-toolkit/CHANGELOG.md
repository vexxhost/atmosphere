# Release notes

## 2025.1.0-51

- Add priorityClassName and runtimeClassName snippets
- Modify job_ks_user template to be able to create multiple Keystone users

### New Features

- Update apparmor values to use security_context instead of annotations.
- Add support for runtimeClassName and priorityClassName

## 2025.1.0

- Mount volumes requested into the job's pod.
- 0.1.0 Initial Chart
- 0.1.1 Add extra DNS names to Ingress
- 0.1.2 Make database backups work with openstack Train
- 0.1.3 Fix ks-user script case matching for domain
- 0.1.4 Update ingress tpl in helmtoolkit
- 0.1.5 Add capability to delete a backup archive
- 0.2.0 Update default Kubernetes API for use with Helm v3
- 0.2.1 Change Issuer to ClusterIssuer
- 0.2.2 Revert Change Issuer to ClusterIssuer
- 0.2.3 Allow openstack service list to retry in event of keystone connection issues
- 0.2.4 Added detailed FiXME for ks-service script bug and code changes
- 0.2.5 Added logic to support cert-manager versioning
- 0.2.6 Add metadata in job templates
- 0.2.7 Replace brace expansion with more standardized Posix approach
- 0.2.8 Override the expiry of Ingress TLS certificate
- 0.2.9 Jobs; put labels only in the template spec
- 0.2.10 Add more S3 configuration options
- 0.2.11 Revert S3 User & Bucket job scripts to v0.2.9
- 0.2.12 Remove hook-delete-policy
- 0.2.13 Modify connection args for s3 bucket creation when TLS is enabled
- 0.2.14 Remove TLS_OPTION argument from s3 bucket creation job
- 0.2.15 Adding TLS rabbitmq logic
- 0.2.16 Add manual mode to the created backup file name
- 0.2.17 Update db backup/restore retry for sending to remote
- 0.2.18 Make Rabbit-init job more robust
- 0.2.19 Revoke all privileges for PUBLIC role in postgres dbs
- 0.2.20 Modify the template of rbac_role to make secrets accessible
- 0.2.21 Fix issue with db backup error return code being eaten
- 0.2.22 Add ability to set labels to add to resources
- 0.2.23 Helm 3 - Fix Job labels
- 0.2.24 Migrate Ingress resources to networking.k8s.io/v1
- 0.2.25 Set Security Context to ks-user job
- 0.2.26 Revert Set Security Context to ks-user job
- 0.2.27 Correct private key size input for Certificates and remove minor version support
- 0.2.28 Set Security context to ks-user job at pod and container level
- 0.2.29 Enhance mariadb backup
- 0.2.30 Add ability to image pull secrets on pods
- 0.2.31 Add log strings for alert generation
- 0.2.32 Consolidate mon_endpoints discovery
- 0.2.33 Remove set -x
- 0.2.34 Modify database backup logic to maintain minimum number of backups
- 0.2.35 Database B/R improvements
- 0.2.36 Enable taint toleration for Openstack services jobs
- 0.2.37 Updated chart naming for subchart compatibility
- 0.2.38 Minor change to display archive directory with files in sub-directory
- 0.2.39 Removed tillerVersion from Chart to pass helm3 linting
- 0.2.40 Revert chart naming for subchart compatibility
- 0.2.41 Database B/R - archive name parser added
- 0.2.42 Database B/R - fix to make script compliant with a retention policy
- 0.2.43 Support having a single external ingress controller
- 0.2.44 Added OCI registry authentication
- 0.2.45 Modify use_external_ingress_controller place in openstack-helm values.yaml
- 0.2.46 Fixed for getting kibana ingress value parameters
- 0.2.47 Adjusting of kibana ingress value parameters
- 0.2.48 Added verify_databases_backup_archives function call to backup process and added remote backup sha256 hash verification
- 0.2.49 Moved RabbitMQ Guest Admin removal to init
- 0.2.50 Allow tls for external ingress without specifying key and crt
- 0.2.51 Added a random delay up to 300 seconds to remote backup upload/download for load spreading purpose
- 0.2.52 Decreased random delay to up to 30 seconds and switched remote backup verification protocol to md5
- 0.2.53 Update create db user queries
- 0.2.54 Fix dependency resolver to ignore non-existing dependencyKey when dependencyMixinParam is a slice
- 0.2.55 Updated deprecated IngressClass annotation
- 0.2.56 Expose S3 credentials from Rook bucket CRD secret
- 0.2.57 Safer file removal
- 0.2.58 Backups verification improvements
- 0.2.59 Added throttling remote backups
- 0.2.60 Change default ingress pathType to Prefix
- 0.2.61 Add custom pod annotations snippet
- 0.2.62 Add custom secret annotations snippet
- 0.2.63 Add custom job annotations snippet and wire it into job templates
- 0.2.64 Use custom secret annotations snippet in other secret templates
- 0.2.65 Escape special characters in password for DB connection
- 0.2.66 Align db scripts with sqlalchemy 2.0
- 0.2.67 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.2.68 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.2.69 Use quay.io/airshipit/kubernetes-entrypoint:latest-ubuntu_focal by default
- 0.2.70 Decode url-encoded password for rabbit connection
- 0.2.71 Add snippet with service parameters
- 0.2.72 Add snippet configmap_oslo_policy
- 0.2.73 Add ability to get multiple hosts endpoint
- 0.2.74 Remove trailing slash in endpoinds
- 0.2.75 Add daemonset_overrides_root util
- 0.2.76 update tookit to support fqdn alias
- 0.2.77 Add recommended kubernetes name label to pods definition
- 0.2.78 Fix db-init and db-drop scripts to make them work with sqlalchemy >2.0
- 0.2.79 Update Chart.yaml apiVersion to v2
- 2024.2.0 Update version to align with the Openstack release cycle

## 2024.2.0

Before 2024.2.0 all the OpenStack-Helm charts were versioned independently.
Here we provide all the release notes for the chart for all versions before 2024.2.0.
