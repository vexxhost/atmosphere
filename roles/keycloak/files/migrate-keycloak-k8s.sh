#!/usr/bin/env bash

# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

set -Eeuo pipefail

usage() {
  cat <<'EOF'
Run a one-shot Keycloak MySQL/Percona to PostgreSQL logical migration.

Required environment variables:
  KEYCLOAK_IMAGE          Exact source Keycloak image (prefer an image digest)
  SOURCE_DB_HOST          MySQL/Percona Service DNS name
  SOURCE_DB_SECRET        Secret containing the source database credentials
  TARGET_DB_HOST          PostgreSQL Service DNS name
  TARGET_DB_SECRET        Secret containing the target database credentials

Common optional variables:
  NAMESPACE                       default: default
  SOURCE_DB_PORT                  default: 3306
  SOURCE_DB_NAME                  default: keycloak
  SOURCE_DB_USERNAME              default: keycloak
  SOURCE_DB_PASSWORD_KEY          default: password
  SOURCE_JDBC_PARAMETERS          JDBC query string without the leading '?'
  TARGET_DB_PORT                  default: 5432
  TARGET_DB_NAME                  default: keycloak
  TARGET_DB_SCHEMA                default: public
  TARGET_DB_USERNAME_KEY          default: username
  TARGET_DB_PASSWORD_KEY          default: password
  TARGET_JDBC_PARAMETERS          JDBC query string without the leading '?'
  TARGET_PGSSLMODE                default: prefer
  USERS_PER_FILE                  default: 1000
  MIGRATION_VOLUME_SIZE           default: 4Gi (tmpfs)
  MIGRATION_NODE_SELECTOR_YAML    nodeSelector mapping rendered as YAML
  KEYCLOAK_MEMORY_REQUEST         default: 1Gi
  KEYCLOAK_MEMORY_LIMIT           default: 4Gi
  JOB_TIMEOUT_SECONDS             default: 3600
  VERIFY_ONLY                     default: false; compare populated target, never import
  REPORT_FORMAT                   default: summary; use json for machine output
  FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES
                                default: true; return exit 2 on unknown data differences
  ALLOW_KNOWN_KEYCLOAK_DIFFERENCES default: true; accept narrow import normalizations
  DRY_RUN                         default: false; print the Job without creating it
  KEEP_JOB                        default: false; unsafe because export data remains

The PostgreSQL target schema must contain no tables. Both the source and target
Keycloak deployments must be stopped before this script is run.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 0 ]]; then
  usage >&2
  exit 2
fi

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

require_env() {
  local name="$1"
  [[ -n "${!name:-}" ]] || fail "$name is required"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

validate_dns_label() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]] || fail "$name is not a valid Kubernetes DNS label: $value"
  (( ${#value} <= 63 )) || fail "$name must be at most 63 characters"
}

validate_secret_key() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[-._a-zA-Z0-9]+$ ]] || fail "$name is not a valid Secret key: $value"
}

validate_host() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[-._a-zA-Z0-9]+$ ]] || fail "$name contains unsupported characters: $value"
}

validate_integer() {
  local name="$1"
  local value="$2"
  [[ "$value" =~ ^[1-9][0-9]*$ ]] || fail "$name must be a positive integer"
}

validate_no_newlines() {
  local name="$1"
  local value="$2"
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || fail "$name must not contain newlines"
}

yaml_quote() {
  local escaped
  escaped="$(printf '%s' "$1" | sed "s/'/''/g")"
  printf "'%s'" "$escaped"
}

require_command kubectl
require_command sed

require_env KEYCLOAK_IMAGE
require_env SOURCE_DB_HOST
require_env SOURCE_DB_SECRET
require_env TARGET_DB_HOST
require_env TARGET_DB_SECRET

NAMESPACE="${NAMESPACE:-default}"
SOURCE_DB_PORT="${SOURCE_DB_PORT:-3306}"
SOURCE_DB_NAME="${SOURCE_DB_NAME:-keycloak}"
SOURCE_DB_USERNAME="${SOURCE_DB_USERNAME:-keycloak}"
SOURCE_DB_PASSWORD_KEY="${SOURCE_DB_PASSWORD_KEY:-password}"
SOURCE_JDBC_PARAMETERS="${SOURCE_JDBC_PARAMETERS:-}"
TARGET_DB_PORT="${TARGET_DB_PORT:-5432}"
TARGET_DB_NAME="${TARGET_DB_NAME:-keycloak}"
TARGET_DB_SCHEMA="${TARGET_DB_SCHEMA:-public}"
TARGET_DB_USERNAME_KEY="${TARGET_DB_USERNAME_KEY:-username}"
TARGET_DB_PASSWORD_KEY="${TARGET_DB_PASSWORD_KEY:-password}"
TARGET_JDBC_PARAMETERS="${TARGET_JDBC_PARAMETERS:-}"
TARGET_PGSSLMODE="${TARGET_PGSSLMODE:-prefer}"
USERS_PER_FILE="${USERS_PER_FILE:-1000}"
MIGRATION_VOLUME_SIZE="${MIGRATION_VOLUME_SIZE:-4Gi}"
MIGRATION_NODE_SELECTOR_YAML="${MIGRATION_NODE_SELECTOR_YAML:-}"
KEYCLOAK_MEMORY_REQUEST="${KEYCLOAK_MEMORY_REQUEST:-1Gi}"
KEYCLOAK_MEMORY_LIMIT="${KEYCLOAK_MEMORY_LIMIT:-4Gi}"
JOB_TIMEOUT_SECONDS="${JOB_TIMEOUT_SECONDS:-3600}"
VERIFY_ONLY="${VERIFY_ONLY:-false}"
REPORT_FORMAT="${REPORT_FORMAT:-summary}"
if [[ -n "${FAIL_ON_VERIFICATION_DIFFERENCES+x}" && -z "${FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES+x}" ]]; then
  printf 'warning: FAIL_ON_VERIFICATION_DIFFERENCES is deprecated; use FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES.\n' >&2
fi
FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES="${FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES:-${FAIL_ON_VERIFICATION_DIFFERENCES:-true}}"
ALLOW_KNOWN_KEYCLOAK_DIFFERENCES="${ALLOW_KNOWN_KEYCLOAK_DIFFERENCES:-true}"
DRY_RUN="${DRY_RUN:-false}"
KEEP_JOB="${KEEP_JOB:-false}"
POSTGRES_CLIENT_IMAGE="${POSTGRES_CLIENT_IMAGE:-docker.io/library/postgres:17.6-alpine}"
VERIFIER_IMAGE="${VERIFIER_IMAGE:-docker.io/library/python:3.12.11-alpine3.21}"
JOB_NAME="${JOB_NAME:-keycloak-db-migration-$(date -u +%Y%m%d%H%M%S)-$$}"

validate_dns_label NAMESPACE "$NAMESPACE"
validate_dns_label JOB_NAME "$JOB_NAME"
validate_dns_label SOURCE_DB_SECRET "$SOURCE_DB_SECRET"
validate_dns_label TARGET_DB_SECRET "$TARGET_DB_SECRET"
validate_secret_key SOURCE_DB_PASSWORD_KEY "$SOURCE_DB_PASSWORD_KEY"
validate_secret_key TARGET_DB_USERNAME_KEY "$TARGET_DB_USERNAME_KEY"
validate_secret_key TARGET_DB_PASSWORD_KEY "$TARGET_DB_PASSWORD_KEY"
validate_host SOURCE_DB_HOST "$SOURCE_DB_HOST"
validate_host TARGET_DB_HOST "$TARGET_DB_HOST"
validate_integer SOURCE_DB_PORT "$SOURCE_DB_PORT"
validate_integer TARGET_DB_PORT "$TARGET_DB_PORT"
validate_integer USERS_PER_FILE "$USERS_PER_FILE"
validate_integer JOB_TIMEOUT_SECONDS "$JOB_TIMEOUT_SECONDS"
[[ "$TARGET_DB_SCHEMA" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || fail "TARGET_DB_SCHEMA must be an unquoted PostgreSQL identifier"
[[ "$TARGET_PGSSLMODE" =~ ^(disable|allow|prefer|require|verify-ca|verify-full)$ ]] || fail "TARGET_PGSSLMODE is invalid"
[[ "$VERIFY_ONLY" == "true" || "$VERIFY_ONLY" == "false" ]] || fail "VERIFY_ONLY must be true or false"
[[ "$REPORT_FORMAT" == "summary" || "$REPORT_FORMAT" == "json" ]] || fail "REPORT_FORMAT must be summary or json"
[[ "$FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES" == "true" || "$FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES" == "false" ]] || fail "FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES must be true or false"
[[ "$ALLOW_KNOWN_KEYCLOAK_DIFFERENCES" == "true" || "$ALLOW_KNOWN_KEYCLOAK_DIFFERENCES" == "false" ]] || fail "ALLOW_KNOWN_KEYCLOAK_DIFFERENCES must be true or false"
[[ "$DRY_RUN" == "true" || "$DRY_RUN" == "false" ]] || fail "DRY_RUN must be true or false"
[[ "$KEEP_JOB" == "true" || "$KEEP_JOB" == "false" ]] || fail "KEEP_JOB must be true or false"

for variable in \
  KEYCLOAK_IMAGE SOURCE_DB_NAME SOURCE_DB_USERNAME SOURCE_JDBC_PARAMETERS TARGET_DB_NAME \
  TARGET_JDBC_PARAMETERS MIGRATION_VOLUME_SIZE KEYCLOAK_MEMORY_REQUEST \
  KEYCLOAK_MEMORY_LIMIT POSTGRES_CLIENT_IMAGE VERIFIER_IMAGE; do
  validate_no_newlines "$variable" "${!variable}"
done

SOURCE_JDBC_URL="jdbc:mysql://${SOURCE_DB_HOST}:${SOURCE_DB_PORT}/${SOURCE_DB_NAME}"
TARGET_JDBC_URL="jdbc:postgresql://${TARGET_DB_HOST}:${TARGET_DB_PORT}/${TARGET_DB_NAME}"
if [[ -n "$SOURCE_JDBC_PARAMETERS" ]]; then
  SOURCE_JDBC_URL="${SOURCE_JDBC_URL}?${SOURCE_JDBC_PARAMETERS}"
fi
if [[ -n "$TARGET_JDBC_PARAMETERS" ]]; then
  TARGET_JDBC_URL="${TARGET_JDBC_URL}?${TARGET_JDBC_PARAMETERS}"
fi

created=false
cleanup() {
  local status=$?
  if [[ "$created" == "true" && "$KEEP_JOB" != "true" ]]; then
    kubectl --namespace "$NAMESPACE" delete job "$JOB_NAME" --ignore-not-found --wait=true >/dev/null 2>&1 || true
  fi
  return "$status"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

render_node_selector() {
  local line
  [[ -n "$MIGRATION_NODE_SELECTOR_YAML" ]] || return 0

  printf '      nodeSelector:\n'
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    [[ "$line" != *$'\r'* ]] || fail "MIGRATION_NODE_SELECTOR_YAML must not contain carriage returns"
    printf '        %s\n' "$line"
  done <<<"$MIGRATION_NODE_SELECTOR_YAML"
}

render_manifest() {
  cat <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: $(yaml_quote "$JOB_NAME")
  namespace: $(yaml_quote "$NAMESPACE")
  labels:
    app.kubernetes.io/name: keycloak-db-migration
    app.kubernetes.io/component: database-migration
spec:
  backoffLimit: 0
  activeDeadlineSeconds: ${JOB_TIMEOUT_SECONDS}
  ttlSecondsAfterFinished: 600
  template:
    metadata:
      labels:
        app.kubernetes.io/name: keycloak-db-migration
        app.kubernetes.io/component: database-migration
    spec:
$(render_node_selector)
      automountServiceAccountToken: false
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      initContainers:
        - name: check-empty-target
          image: $(yaml_quote "$POSTGRES_CLIENT_IMAGE")
          imagePullPolicy: IfNotPresent
          command: [/bin/sh, -ec]
          args:
            - |
              if [ "\$VERIFY_ONLY" = "true" ]; then
                schema_count="\$(psql -X -v ON_ERROR_STOP=1 -Atqc "SELECT count(*) FROM information_schema.schemata WHERE schema_name = '${TARGET_DB_SCHEMA}'")"
                if [ "\$schema_count" != "1" ]; then
                  echo "Verification-only mode requires existing target schema ${TARGET_DB_SCHEMA}." >&2
                  exit 1
                fi
                realm_table_count="\$(psql -X -v ON_ERROR_STOP=1 -Atqc "SELECT count(*) FROM information_schema.tables WHERE table_schema = '${TARGET_DB_SCHEMA}' AND table_name = 'realm' AND table_type = 'BASE TABLE'")"
                if [ "\$realm_table_count" != "1" ]; then
                  echo "Verification-only mode requires an already populated Keycloak target; table ${TARGET_DB_SCHEMA}.realm is missing." >&2
                  exit 1
                fi
                realm_count="\$(psql -X -v ON_ERROR_STOP=1 -Atqc "SELECT count(*) FROM ${TARGET_DB_SCHEMA}.realm")"
                if [ "\$realm_count" = "0" ]; then
                  echo "Verification-only mode requires an already populated Keycloak target; no realms were found." >&2
                  exit 1
                fi
                echo "Verification-only mode: target contains \$realm_count realm(s); skipping import."
                exit 0
              fi
              schema_count="\$(psql -X -v ON_ERROR_STOP=1 -Atqc "SELECT count(*) FROM information_schema.schemata WHERE schema_name = '${TARGET_DB_SCHEMA}'")"
              if [ "\$schema_count" != "1" ]; then
                echo "Target PostgreSQL schema ${TARGET_DB_SCHEMA} does not exist." >&2
                exit 1
              fi
              table_count="\$(psql -X -v ON_ERROR_STOP=1 -Atqc "SELECT count(*) FROM information_schema.tables WHERE table_schema = '${TARGET_DB_SCHEMA}' AND table_type = 'BASE TABLE'")"
              if [ "\$table_count" != "0" ]; then
                echo "Target PostgreSQL schema ${TARGET_DB_SCHEMA} is not empty (\$table_count tables)." >&2
                exit 1
              fi
              echo "Target PostgreSQL schema is empty."
          env:
            - name: VERIFY_ONLY
              value: $(yaml_quote "$VERIFY_ONLY")
            - name: PGHOST
              value: $(yaml_quote "$TARGET_DB_HOST")
            - name: PGPORT
              value: $(yaml_quote "$TARGET_DB_PORT")
            - name: PGDATABASE
              value: $(yaml_quote "$TARGET_DB_NAME")
            - name: PGSSLMODE
              value: $(yaml_quote "$TARGET_PGSSLMODE")
            - name: PGUSER
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$TARGET_DB_SECRET")
                  key: $(yaml_quote "$TARGET_DB_USERNAME_KEY")
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$TARGET_DB_SECRET")
                  key: $(yaml_quote "$TARGET_DB_PASSWORD_KEY")
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]

        - name: export-source
          image: $(yaml_quote "$KEYCLOAK_IMAGE")
          imagePullPolicy: IfNotPresent
          command: [/opt/keycloak/bin/kc.sh]
          args:
            - export
            - --dir=/migration/source
            - --users=different_files
            - --users-per-file=${USERS_PER_FILE}
          env:
            - name: KC_DB
              value: mysql
            # PXC/wsrep does not support MySQL XA transactions.
            - name: KC_TRANSACTION_XA_ENABLED
              value: "false"
            - name: KC_DB_URL
              value: $(yaml_quote "$SOURCE_JDBC_URL")
            - name: KC_DB_USERNAME
              value: $(yaml_quote "$SOURCE_DB_USERNAME")
            - name: KC_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$SOURCE_DB_SECRET")
                  key: $(yaml_quote "$SOURCE_DB_PASSWORD_KEY")
          resources:
            requests:
              memory: $(yaml_quote "$KEYCLOAK_MEMORY_REQUEST")
            limits:
              memory: $(yaml_quote "$KEYCLOAK_MEMORY_LIMIT")
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]
          volumeMounts:
            - name: migration-data
              mountPath: /migration

        - name: import-target
          image: $(yaml_quote "$KEYCLOAK_IMAGE")
          imagePullPolicy: IfNotPresent
          command: [/bin/sh, -ec]
          args:
            - |
              if [ "\$VERIFY_ONLY" = "true" ]; then
                echo "Verification-only mode: skipping PostgreSQL import."
                exit 0
              fi
              exec /opt/keycloak/bin/kc.sh import --dir=/migration/source --override=true
          env:
            - name: VERIFY_ONLY
              value: $(yaml_quote "$VERIFY_ONLY")
            - name: KC_DB
              value: postgres
            - name: KC_TRANSACTION_XA_ENABLED
              value: "false"
            - name: KC_DB_URL
              value: $(yaml_quote "$TARGET_JDBC_URL")
            - name: KC_DB_SCHEMA
              value: $(yaml_quote "$TARGET_DB_SCHEMA")
            - name: KC_DB_USERNAME
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$TARGET_DB_SECRET")
                  key: $(yaml_quote "$TARGET_DB_USERNAME_KEY")
            - name: KC_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$TARGET_DB_SECRET")
                  key: $(yaml_quote "$TARGET_DB_PASSWORD_KEY")
          resources:
            requests:
              memory: $(yaml_quote "$KEYCLOAK_MEMORY_REQUEST")
            limits:
              memory: $(yaml_quote "$KEYCLOAK_MEMORY_LIMIT")
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]
          volumeMounts:
            - name: migration-data
              mountPath: /migration

        - name: export-target
          image: $(yaml_quote "$KEYCLOAK_IMAGE")
          imagePullPolicy: IfNotPresent
          command: [/opt/keycloak/bin/kc.sh]
          args:
            - export
            - --dir=/migration/target
            - --users=different_files
            - --users-per-file=${USERS_PER_FILE}
          env:
            - name: KC_DB
              value: postgres
            - name: KC_TRANSACTION_XA_ENABLED
              value: "false"
            - name: KC_DB_URL
              value: $(yaml_quote "$TARGET_JDBC_URL")
            - name: KC_DB_SCHEMA
              value: $(yaml_quote "$TARGET_DB_SCHEMA")
            - name: KC_DB_USERNAME
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$TARGET_DB_SECRET")
                  key: $(yaml_quote "$TARGET_DB_USERNAME_KEY")
            - name: KC_DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: $(yaml_quote "$TARGET_DB_SECRET")
                  key: $(yaml_quote "$TARGET_DB_PASSWORD_KEY")
          resources:
            requests:
              memory: $(yaml_quote "$KEYCLOAK_MEMORY_REQUEST")
            limits:
              memory: $(yaml_quote "$KEYCLOAK_MEMORY_LIMIT")
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]
          volumeMounts:
            - name: migration-data
              mountPath: /migration

      containers:
        - name: verify
          image: $(yaml_quote "$VERIFIER_IMAGE")
          imagePullPolicy: IfNotPresent
          command: [python3, -c]
          env:
            - name: REPORT_FORMAT
              value: $(yaml_quote "$REPORT_FORMAT")
            - name: ALLOW_KNOWN_KEYCLOAK_DIFFERENCES
              value: $(yaml_quote "$ALLOW_KNOWN_KEYCLOAK_DIFFERENCES")
          args:
            - |
              import collections
              import hashlib
              import json
              import os
              import re
              import sys

              REPORT_FORMAT = os.environ.get("REPORT_FORMAT", "summary")
              ALLOW_KNOWN_KEYCLOAK_DIFFERENCES = (
                  os.environ.get("ALLOW_KNOWN_KEYCLOAK_DIFFERENCES", "true") == "true"
              )

              SENSITIVE_HINTS = (
                  "secret",
                  "password",
                  "credential",
                  "privatekey",
                  "private_key",
                  "apikey",
                  "api_key",
                  "api-key",
              )

              TOKEN_VALUE_KEYS = {
                  "token",
                  "access_token",
                  "accesstoken",
                  "refresh_token",
                  "refreshtoken",
                  "id_token",
                  "idtoken",
                  "registrationaccesstoken",
                  "initialaccesstoken",
                  "federatedaccesstoken",
              }

              def sensitive_key(key):
                  lowered = key.lower()
                  return any(hint in lowered for hint in SENSITIVE_HINTS) or (
                      lowered.replace("-", "_") in TOKEN_VALUE_KEYS
                  )

              def normalized(value):
                  if isinstance(value, dict):
                      return {key: normalized(value[key]) for key in sorted(value)}
                  if isinstance(value, list):
                      items = [normalized(item) for item in value]
                      return sorted(items, key=canonical)
                  return value

              def canonical(value):
                  return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

              def digest(value):
                  payload = canonical(normalized(value)).encode("utf-8")
                  return hashlib.sha256(payload).hexdigest()

              def audit_sensitive(value, inherited=False):
                  sensitive = 0
                  masked = 0
                  if isinstance(value, dict):
                      for key, child in value.items():
                          hinted = inherited or sensitive_key(key)
                          child_sensitive, child_masked = audit_sensitive(child, hinted)
                          sensitive += child_sensitive
                          masked += child_masked
                  elif isinstance(value, list):
                      for child in value:
                          child_sensitive, child_masked = audit_sensitive(child, inherited)
                          sensitive += child_sensitive
                          masked += child_masked
                  elif inherited and value is not None:
                      sensitive += 1
                      if isinstance(value, str) and value and set(value) == {"*"}:
                          masked += 1
                  return sensitive, masked

              def record_identity(value):
                  if isinstance(value, dict):
                      return value.get("username") or value.get("id") or digest(value)
                  return digest(value)

              def list_index(source, target):
                  identity_fields = ("clientId", "name", "alias", "username", "id", "type", "providerId")
                  if not all(isinstance(item, dict) for item in source + target):
                      return None
                  for field in identity_fields:
                      if not all(field in item and item[field] is not None for item in source + target):
                          continue
                      source_index = {str(item[field]): item for item in source}
                      target_index = {str(item[field]): item for item in target}
                      if len(source_index) == len(source) and len(target_index) == len(target):
                          return field, source_index, target_index
                  return None

              def item_path(path, identity_field, identity):
                  if identity_field == "clientId" or (
                      identity_field == "name" and ".roles." in path
                  ):
                      return (
                          path
                          + "["
                          + identity_field
                          + "="
                          + json.dumps(identity, ensure_ascii=False)
                          + "]"
                      )
                  return path + "[*]"

              def displayed_value(value, sensitive):
                  if sensitive:
                      return "<redacted>"
                  if isinstance(value, (dict, list)):
                      return "<complex>"
                  encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                  if len(encoded) > 160:
                      return encoded[:157] + "..."
                  return encoded

              def compare_source_value(
                  source, target, path, required, additions, sensitive=False
              ):
                  if source == target:
                      return
                  if type(source) is not type(target):
                      required.append(
                          path
                          + " (type changed; source="
                          + type(source).__name__
                          + ", target="
                          + type(target).__name__
                          + ")"
                      )
                  elif isinstance(source, dict):
                      for key in sorted(source):
                          child_path = path + "." + key
                          child_sensitive = sensitive or sensitive_key(key)
                          if key not in target:
                              required.append(
                                  child_path
                                  + " (missing from target; source="
                                  + displayed_value(source[key], child_sensitive)
                                  + ")"
                              )
                          else:
                              compare_source_value(
                                  source[key],
                                  target[key],
                                  child_path,
                                  required,
                                  additions,
                                  child_sensitive,
                              )
                      for key in sorted(set(target) - set(source)):
                          child_sensitive = sensitive or sensitive_key(key)
                          additions.append(
                              path
                              + "."
                              + key
                              + " (target-only field; target="
                              + displayed_value(target[key], child_sensitive)
                              + ")"
                          )
                  elif isinstance(source, list):
                      indexed = list_index(source, target)
                      if indexed is not None:
                          identity_field, source_index, target_index = indexed
                          for identity in sorted(source_index):
                              child_path = item_path(path, identity_field, identity)
                              if identity not in target_index:
                                  required.append(child_path + " (missing from target)")
                              else:
                                  compare_source_value(
                                      source_index[identity],
                                      target_index[identity],
                                      child_path,
                                      required,
                                      additions,
                                      sensitive,
                                  )
                          for identity in sorted(set(target_index) - set(source_index)):
                              additions.append(
                                  item_path(path, identity_field, identity)
                                  + " (target-only item)"
                              )
                      else:
                          source_items = collections.Counter(canonical(item) for item in source)
                          target_items = collections.Counter(canonical(item) for item in target)
                          for encoded_item, count in (source_items - target_items).items():
                              source_item = json.loads(encoded_item)
                              required.extend(
                                  [
                                      path
                                      + " (source list item missing; source="
                                      + displayed_value(source_item, sensitive)
                                      + ")"
                                  ]
                                  * count
                              )
                          for encoded_item, count in (target_items - source_items).items():
                              target_item = json.loads(encoded_item)
                              additions.extend(
                                  [
                                      path
                                      + " (target-only list item; target="
                                      + displayed_value(target_item, sensitive)
                                      + ")"
                                  ]
                                  * count
                              )
                  else:
                      required.append(
                          path
                          + " (value changed; source="
                          + displayed_value(source, sensitive)
                          + ", target="
                          + displayed_value(target, sensitive)
                          + ")"
                      )

              def snapshot(root):
                  records = collections.Counter()
                  documents = {}
                  stats = collections.Counter()
                  realms = set()
                  masked = 0
                  sensitive = 0
                  files = sorted(name for name in os.listdir(root) if name.endswith(".json"))
                  if not files:
                      raise RuntimeError("no JSON export files found in " + root)

                  def add_document(kind, realm, identity, value):
                      key = (kind, realm, str(identity))
                      if key in documents:
                          raise RuntimeError("duplicate exported record for kind=" + kind + ", realm=" + realm)
                      normalized_value = normalized(value)
                      documents[key] = normalized_value
                      records[(kind, realm, digest(normalized_value))] += 1

                  for name in files:
                      path = os.path.join(root, name)
                      with open(path, "r", encoding="utf-8") as stream:
                          data = json.load(stream)
                      found_sensitive, found_masked = audit_sensitive(data)
                      sensitive += found_sensitive
                      masked += found_masked

                      if name.endswith("-realm.json"):
                          realm = data.get("realm")
                          if not realm:
                              raise RuntimeError("realm name missing in " + name)
                          realms.add(realm)
                          add_document("realm", realm, realm, data)
                          stats["realms"] += 1
                      elif "federated-users-" in name:
                          realm = data.get("realm")
                          users = data.get("federatedUsers")
                          if not realm or not isinstance(users, list):
                              raise RuntimeError("invalid federated-user export file " + name)
                          for user in users:
                              add_document("federated-user", realm, record_identity(user), user)
                          stats["federated_users"] += len(users)
                      elif "users-" in name:
                          realm = data.get("realm")
                          users = data.get("users")
                          if not realm or not isinstance(users, list):
                              raise RuntimeError("invalid user export file " + name)
                          for user in users:
                              add_document("user", realm, record_identity(user), user)
                          stats["users"] += len(users)
                      else:
                          add_document("other-file", name, name, data)
                          stats["other_files"] += 1

                  stats["files"] = len(files)
                  stats["sensitive_values"] = sensitive
                  return records, documents, stats, sorted(realms), masked

              def summarize(counter):
                  summary = collections.Counter()
                  for (kind, realm, unused_digest), count in counter.items():
                      summary[(kind, realm)] += count
                  return [
                      {"kind": kind, "realm": realm, "records": count}
                      for (kind, realm), count in sorted(summary.items())
                  ]

              def compare_documents(source, target):
                  required = []
                  additions = []
                  source_keys = set(source)
                  target_keys = set(target)
                  for kind, realm, identity in source_keys - target_keys:
                      required.append(
                          (
                              kind,
                              realm,
                              "\$record[identity="
                              + json.dumps(identity, ensure_ascii=False)
                              + "] (missing from target)",
                          )
                      )
                  for kind, realm, identity in target_keys - source_keys:
                      additions.append(
                          (
                              kind,
                              realm,
                              "\$record[identity="
                              + json.dumps(identity, ensure_ascii=False)
                              + "] (target-only)",
                          )
                      )
                  for key in source_keys & target_keys:
                      kind, realm, unused_identity = key
                      record_required = []
                      record_additions = []
                      compare_source_value(
                          source[key],
                          target[key],
                          "$",
                          record_required,
                          record_additions,
                      )
                      required.extend((kind, realm, path) for path in record_required)
                      additions.extend((kind, realm, path) for path in record_additions)
                  return required, additions

              def summarize_findings(findings):
                  summary = collections.Counter(findings)
                  return [
                      {"kind": kind, "realm": realm, "path": path, "records": count}
                      for (kind, realm, path), count in sorted(summary.items())[:200]
                  ]

              def known_difference(kind, path):
                  if not ALLOW_KNOWN_KEYCLOAK_DIFFERENCES:
                      return False
                  if kind == "realm" and path in {
                      '$.clients[clientId="realm-management"].bearerOnly '
                      '(value changed; source=true, target=false)',
                      '$.clients[clientId="realm-management"].serviceAccountsEnabled '
                      '(value changed; source=false, target=true)',
                  }:
                      return True
                  if kind == "user" and re.fullmatch(
                      r'[$][.]clientConsents\[clientId="[^"]+"\][.]'
                      r'(createdDate|lastUpdatedDate) '
                      r'\(value changed; source=[0-9]+, target=[0-9]+\)',
                      path,
                  ):
                      return True
                  return False

              def classify_source_differences(findings):
                  known = []
                  unexpected = []
                  for finding in findings:
                      kind, unused_realm, path = finding
                      if known_difference(kind, path):
                          known.append(finding)
                      else:
                          unexpected.append(finding)
                  return known, unexpected

              def realm_management_summary(documents):
                  summary = {}
                  for (kind, realm, unused_identity), document in documents.items():
                      realm_summary = summary.setdefault(
                          realm,
                          {"client": None, "serviceAccountUsers": []},
                      )
                      if kind == "realm":
                          clients = [
                              client
                              for client in document.get("clients", [])
                              if client.get("clientId") == "realm-management"
                          ]
                          roles = (
                              document.get("roles", {})
                              .get("client", {})
                              .get("realm-management", [])
                          )
                          if clients:
                              client = clients[0]
                              realm_summary["client"] = {
                                  "enabled": client.get("enabled"),
                                  "bearerOnly": client.get("bearerOnly"),
                                  "serviceAccountsEnabled": client.get("serviceAccountsEnabled"),
                                  "publicClient": client.get("publicClient"),
                                  "standardFlowEnabled": client.get("standardFlowEnabled"),
                                  "directAccessGrantsEnabled": client.get("directAccessGrantsEnabled"),
                                  "authorizationServicesEnabled": client.get("authorizationServicesEnabled"),
                                  "clientAuthenticatorType": client.get("clientAuthenticatorType"),
                                  "roleCount": len(roles),
                                  "hasUmaProtectionRole": any(
                                      role.get("name") == "uma_protection" for role in roles
                                  ),
                              }
                      elif (
                          kind == "user"
                          and document.get("serviceAccountClientId") == "realm-management"
                      ):
                          realm_summary["serviceAccountUsers"].append(
                              {
                                  "username": document.get("username"),
                                  "enabled": document.get("enabled"),
                              }
                          )
                  return {realm: summary[realm] for realm in sorted(summary)}

              def compact_addition_path(path):
                  return re.sub(r'\[(clientId|name)=".*?"\]', "[*]", path)

              def print_record_statistics(source_stats, target_stats):
                  keys = ("realms", "users", "federated_users", "files", "sensitive_values")
                  values = []
                  for key in keys:
                      source_value = source_stats.get(key, 0)
                      target_value = target_stats.get(key, 0)
                      values.append(key + "=" + str(source_value) + "->" + str(target_value))
                  print("Records: " + ", ".join(values))

              def print_source_findings(heading, findings, accepted=False):
                  summarized = summarize_findings(findings)
                  missing = sum(1 for unused_kind, unused_realm, path in findings if "missing" in path)
                  changed = len(findings) - missing
                  print(
                      heading
                      + ": "
                      + str(changed)
                      + " changed, "
                      + str(missing)
                      + " missing"
                      + (" (accepted)" if accepted else "")
                  )
                  shown = 0
                  for item in summarized[:20]:
                      suffix = " x" + str(item["records"]) if item["records"] > 1 else ""
                      shown += item["records"]
                      print(
                          "  - "
                          + item["kind"]
                          + "/"
                          + item["realm"]
                          + ": "
                          + item["path"]
                          + suffix
                      )
                  if shown < len(findings):
                      print("  - ... " + str(len(findings) - shown) + " more source differences")

              def print_target_additions(findings):
                  if not findings:
                      print("Target additions: none")
                      return
                  grouped = {}
                  resources = []
                  for kind, realm, path in findings:
                      if "target-only item" in path or "\$record[" in path:
                          resources.append((kind, realm, path))
                          continue
                      compact_path = compact_addition_path(path)
                      group = grouped.setdefault(
                          (kind, compact_path), {"records": 0, "realms": set()}
                      )
                      group["records"] += 1
                      group["realms"].add(realm)

                  print(
                      "Target additions: "
                      + str(len(findings))
                      + " total, "
                      + str(len(grouped))
                      + " field groups, "
                      + str(len(resources))
                      + " resources"
                  )
                  grouped_items = sorted(grouped.items())
                  for (kind, path), group in grouped_items[:20]:
                      print(
                          "  - "
                          + kind
                          + ": "
                          + path
                          + " x"
                          + str(group["records"])
                          + " [realms="
                          + ",".join(sorted(group["realms"]))
                          + "]"
                      )
                  if len(grouped_items) > 20:
                      print("  - ... " + str(len(grouped_items) - 20) + " more target field groups")
                  sorted_resources = sorted(resources)
                  for kind, realm, path in sorted_resources[:20]:
                      print("  - " + kind + "/" + realm + ": " + path)
                  if len(sorted_resources) > 20:
                      print("  - ... " + str(len(sorted_resources) - 20) + " more target resources")

              def print_realm_management_changes(realm_management):
                  changed_realms = []
                  source = realm_management["source"]
                  target = realm_management["target"]
                  for realm in sorted(set(source) | set(target)):
                      source_realm = source.get(realm, {})
                      target_realm = target.get(realm, {})
                      changes = []
                      source_client = source_realm.get("client") or {}
                      target_client = target_realm.get("client") or {}
                      for key in sorted(set(source_client) | set(target_client)):
                          if source_client.get(key) != target_client.get(key):
                              changes.append(
                                  key
                                  + "="
                                  + displayed_value(source_client.get(key), False)
                                  + "->"
                                  + displayed_value(target_client.get(key), False)
                              )
                      source_users = source_realm.get("serviceAccountUsers", [])
                      target_users = target_realm.get("serviceAccountUsers", [])
                      if source_users != target_users:
                          changes.append(
                              "serviceAccountUsers="
                              + str(len(source_users))
                              + "->"
                              + str(len(target_users))
                          )
                      if changes:
                          changed_realms.append((realm, changes))

                  if not changed_realms:
                      print("Realm-management changes: none")
                      return
                  print("Realm-management changes:")
                  for realm, changes in changed_realms:
                      print("  - " + realm + ": " + "; ".join(changes))

              try:
                  source, source_documents, source_stats, source_realms, source_masked = snapshot("/migration/source")
                  target, target_documents, target_stats, target_realms, target_masked = snapshot("/migration/target")
                  if source_masked or target_masked:
                      raise RuntimeError(
                          "masked sensitive values detected: source={}, target={}".format(
                              source_masked, target_masked
                          )
                      )
                  realm_management = {
                      "source": realm_management_summary(source_documents),
                      "target": realm_management_summary(target_documents),
                  }
                  required_differences, target_additions = compare_documents(
                      source_documents, target_documents
                  )
                  known_differences, unexpected_differences = classify_source_differences(
                      required_differences
                  )
                  summarized_additions = summarize_findings(target_additions)
                  if unexpected_differences:
                      if REPORT_FORMAT == "json":
                          print(
                              json.dumps(
                                  {
                                      "status": "differences",
                                      "source": dict(source_stats),
                                      "target": dict(target_stats),
                                      "realmManagement": realm_management,
                                      "sourceDifferences": summarize_findings(
                                          required_differences
                                      ),
                                      "knownSourceDifferences": summarize_findings(
                                          known_differences
                                      ),
                                      "unexpectedSourceDifferences": summarize_findings(
                                          unexpected_differences
                                      ),
                                      "targetAdditions": summarized_additions,
                                  },
                                  sort_keys=True,
                              ),
                              file=sys.stderr,
                          )
                      else:
                          print("SOURCE PRESERVATION: DIFFERENCES FOUND", file=sys.stderr)
                          print_record_statistics(source_stats, target_stats)
                          if known_differences:
                              print_source_findings(
                                  "Known Keycloak import differences",
                                  known_differences,
                                  accepted=True,
                              )
                          print_source_findings(
                              "Unexpected source differences", unexpected_differences
                          )
                          print_realm_management_changes(realm_management)
                          print_target_additions(target_additions)
                      # Data differences are an acceptance result, not a Job execution failure.
                      sys.exit(0)
                  result = {
                      "status": (
                          "verified_with_known_differences"
                          if known_differences
                          else (
                              "verified_with_target_additions"
                              if target_additions
                              else "verified"
                          )
                      ),
                      "realms": source_realms,
                      "source": dict(source_stats),
                      "target": dict(target_stats),
                      "realmManagement": realm_management,
                      "knownSourceDifferences": summarize_findings(known_differences),
                      "targetAdditions": summarized_additions,
                  }
                  if REPORT_FORMAT == "json":
                      print(json.dumps(result, sort_keys=True))
                  else:
                      if known_differences:
                          print("SOURCE PRESERVATION: VERIFIED WITH KNOWN DIFFERENCES")
                      else:
                          print("SOURCE PRESERVATION: VERIFIED")
                      print_record_statistics(source_stats, target_stats)
                      if known_differences:
                          print_source_findings(
                              "Known Keycloak import differences",
                              known_differences,
                              accepted=True,
                          )
                      print_realm_management_changes(realm_management)
                      print_target_additions(target_additions)
              except Exception as error:
                  print("Verification failed: " + str(error), file=sys.stderr)
                  sys.exit(1)
          resources:
            requests:
              memory: 128Mi
            limits:
              memory: 512Mi
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]
          volumeMounts:
            - name: migration-data
              mountPath: /migration
              readOnly: true

      volumes:
        - name: migration-data
          emptyDir:
            medium: Memory
            sizeLimit: $(yaml_quote "$MIGRATION_VOLUME_SIZE")
EOF
}

context="$(kubectl config current-context 2>/dev/null || printf unknown)"
if [[ "$DRY_RUN" == "true" ]]; then
  render_manifest
  exit 0
fi

if [[ "$VERIFY_ONLY" == "true" ]]; then
  printf 'Creating verification-only Job %s in namespace %s (context %s).\n' "$JOB_NAME" "$NAMESPACE" "$context"
else
  printf 'Creating migration Job %s in namespace %s (context %s).\n' "$JOB_NAME" "$NAMESPACE" "$context"
fi
printf 'Keycloak image: %s\n' "$KEYCLOAK_IMAGE"
render_manifest | kubectl create -f - >/dev/null
created=true

deadline=$(( $(date +%s) + JOB_TIMEOUT_SECONDS + 30 ))
while true; do
  conditions="$(kubectl --namespace "$NAMESPACE" get job "$JOB_NAME" -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}' 2>/dev/null || true)"
  if [[ "$conditions" == *"Complete=True"* ]]; then
    verify_logs="$(kubectl --namespace "$NAMESPACE" logs "job/$JOB_NAME" --container verify 2>&1)"
    printf '%s\n' "$verify_logs"
    if [[ "$verify_logs" == *"SOURCE PRESERVATION: DIFFERENCES FOUND"* || "$verify_logs" == *'"status": "differences"'* ]]; then
      if [[ "$VERIFY_ONLY" == "true" ]]; then
        printf 'Verification completed and found source differences. No import was attempted.\n' >&2
      else
        printf 'Migration completed and the populated target remains available, but verification found source differences.\n' >&2
      fi
      if [[ "$FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES" == "true" ]]; then
        printf 'FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES=true: returning exit code 2.\n' >&2
        exit 2
      fi
      printf 'Unexpected verification differences are informational because FAIL_ON_UNEXPECTED_VERIFICATION_DIFFERENCES=false.\n' >&2
    elif [[ "$verify_logs" == *"SOURCE PRESERVATION: VERIFIED WITH KNOWN DIFFERENCES"* || "$verify_logs" == *'"status": "verified_with_known_differences"'* ]]; then
      if [[ "$VERIFY_ONLY" == "true" ]]; then
        printf 'Verification completed: only explicitly allowed Keycloak import differences were found.\n'
      else
        printf 'Migration and verification completed: only explicitly allowed Keycloak import differences were found.\n'
      fi
    else
      if [[ "$VERIFY_ONLY" == "true" ]]; then
        printf 'Verification completed: every source value matched; reported target additions are allowed.\n'
      else
        printf 'Migration and verification completed: every source value matched; reported target additions are allowed.\n'
      fi
    fi
    break
  fi
  if [[ "$conditions" == *"Failed=True"* ]]; then
    verify_logs=""
    if verify_logs="$(kubectl --namespace "$NAMESPACE" logs "job/$JOB_NAME" --container verify 2>&1)"; then
      if [[ "$VERIFY_ONLY" == "true" ]]; then
        printf 'Verification Job failed because the verifier did not complete normally. No import was attempted.\n' >&2
      else
        printf 'Migration completed, but the verifier failed unexpectedly.\n' >&2
        printf 'The populated target remains available and was not rolled back.\n' >&2
      fi
      printf 'Verifier output follows.\n' >&2
      printf '%s\n' "$verify_logs" >&2
    else
      if [[ "$VERIFY_ONLY" == "true" ]]; then
        printf 'Verification Job failed before the verifier could complete. Container logs follow.\n' >&2
      else
        printf 'Migration Job failed before verification; import may not have completed. Container logs follow.\n' >&2
      fi
      kubectl --namespace "$NAMESPACE" logs "job/$JOB_NAME" --all-containers=true --prefix=true >&2 || true
    fi
    exit 1
  fi
  if (( $(date +%s) >= deadline )); then
    printf 'Migration Job did not complete before the timeout. Container logs follow.\n' >&2
    if ! kubectl --namespace "$NAMESPACE" logs "job/$JOB_NAME" --container verify >&2; then
      kubectl --namespace "$NAMESPACE" logs "job/$JOB_NAME" --all-containers=true --prefix=true >&2 || true
    fi
    exit 1
  fi
  sleep 5
done

if [[ "$KEEP_JOB" == "true" ]]; then
  printf 'KEEP_JOB=true: Job %s and its sensitive in-memory export were left until the Job TTL removes them.\n' "$JOB_NAME" >&2
fi
