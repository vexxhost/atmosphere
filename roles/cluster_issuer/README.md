# `cluster_issuer`

This role deploys a cert-manager `ClusterIssuer` for automated TLS certificate
management. It supports ACME (Let's Encrypt) with multiple DNS-01 solvers
including Route53, Cloudflare, GoDaddy, Infoblox, and RFC 2136.

## Route53 DNS-01 Solver — Authentication Modes

The Route53 solver supports three authentication modes, selected via
`cluster_issuer_acme_route53_auth`:

| Mode         | Description                                                        | Requires AWS keys? |
|--------------|--------------------------------------------------------------------|--------------------|
| `static`     | Long-lived IAM access key and secret (default)                     | Yes                |
| `ambient`    | Pod environment credentials (EC2 IMDS, env vars, credentials file) | No                 |
| `kubernetes` | OIDC-based `AssumeRoleWithWebIdentity` (IRSA)                      | No                 |

---

## Method 1: Static Access Key (Default)

The simplest method — provide an IAM user's access key directly:

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: route53
cluster_issuer_acme_route53_auth: static
cluster_issuer_acme_route53_region: eu-west-1
cluster_issuer_acme_route53_hosted_zone_id: Z0123456789EXAMPLE
cluster_issuer_acme_route53_access_key_id: AKIAIOSFODNN7EXAMPLE
cluster_issuer_acme_route53_secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Method 2: Ambient Credentials

cert-manager picks up credentials from its pod environment automatically. Useful
when running on EC2 with an instance profile or when using IAM Roles Anywhere.

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: route53
cluster_issuer_acme_route53_auth: ambient
cluster_issuer_acme_route53_region: eu-west-1
cluster_issuer_acme_route53_hosted_zone_id: Z0123456789EXAMPLE
# Optional: IAM role to assume after resolving ambient credentials
cluster_issuer_acme_route53_role_arn: arn:aws:iam::123456789012:role/my-route53-role
```

---

## Method 3: OIDC / IRSA (`kubernetes`) — Recommended for Keyless Auth

This is the most secure method for operators who cannot use long-lived AWS keys.
cert-manager assumes an IAM role using a projected ServiceAccount token via
`sts:AssumeRoleWithWebIdentity`. **This works with any Kubernetes cluster
(including on-premises) — it does NOT require running on AWS.**

### Atmosphere Configuration

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: route53
cluster_issuer_acme_route53_auth: kubernetes
cluster_issuer_acme_route53_region: eu-west-1
cluster_issuer_acme_route53_hosted_zone_id: Z0123456789EXAMPLE
cluster_issuer_acme_route53_role_arn: arn:aws:iam::123456789012:role/cert-manager-route53
# Optional; defaults to "cert-manager-route53"
cluster_issuer_acme_route53_service_account_name: cert-manager-route53
```

### Prerequisites (One-Time Setup)

Before applying the Atmosphere configuration above, you must complete these
prerequisite steps to make your Kubernetes cluster's OIDC issuer publicly
discoverable by AWS.

#### Step 1: Set Variables

Choose your S3 bucket name and AWS region. The `ISSUER_HOSTPATH` will become
the publicly accessible URL that AWS uses to verify tokens.

```bash
S3_BUCKET_NAME="my-oidc-bucket"
AWS_REGION="eu-west-1"
ISSUER_HOSTPATH="${S3_BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com"
```

> **Note:** You can also use a custom domain or a global S3 endpoint instead.
> The key requirement is that AWS IAM must be able to reach this URL over HTTPS.

#### Step 2: Create the S3 Bucket

```bash
aws s3api create-bucket \
  --bucket $S3_BUCKET_NAME \
  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION
```

#### Step 3: Fetch OIDC Discovery Documents from Your Cluster

These documents allow AWS to verify ServiceAccount tokens issued by your
Kubernetes API server.

**If you have direct API access:**

```bash
# Fetch JWKS (JSON Web Key Set)
kubectl get --raw /openid/v1/jwks > jwks.json

# Fetch OIDC discovery document
kubectl get --raw /.well-known/openid-configuration > openid-configuration.json
```

**If you need a proxy (no direct API access):**

```bash
kubectl proxy &
curl http://127.0.0.1:8001/openid/v1/jwks > jwks.json
curl http://127.0.0.1:8001/.well-known/openid-configuration > openid-configuration.json
```

#### Step 4: Update the Discovery Document URLs

The downloaded `openid-configuration.json` contains internal Kubernetes URLs.
You need to rewrite `jwks_uri` and `issuer` to point to your public S3 bucket.

> **Important:** From this point forward, decide what you want for
> `ISSUER_HOSTPATH` — the regional S3 bucket name, the global S3 endpoint, or
> a custom domain. Kubernetes API servers must also be able to reach S3 and IAM
> AWS service endpoints.

```bash
# Update jwks_uri to point to the S3-hosted JWKS
cat openid-configuration.json | \
  jq --arg uri "https://${ISSUER_HOSTPATH}/openid/v1/jwks" \
     '.jwks_uri = $uri' \
  > openid-configuration-updated.json

# Update issuer to match the S3 host path
cat openid-configuration-updated.json | \
  jq --arg iss "https://${ISSUER_HOSTPATH}" \
     '.issuer = $iss' \
  > openid-configuration-final.json
```

#### Step 5: Upload Documents to S3

```bash
# Upload JWKS
aws s3 cp jwks.json \
  s3://${S3_BUCKET_NAME}/openid/v1/jwks \
  --content-type "application/json"

# Upload OIDC discovery document
aws s3 cp openid-configuration-final.json \
  s3://${S3_BUCKET_NAME}/.well-known/openid-configuration \
  --content-type "application/json"
```

#### Step 6: Make the Documents Publicly Accessible

AWS IAM needs to fetch these documents without authentication. Use a dedicated
bucket (no sensitive data) since you are opening it to public reads.

```bash
# Disable "Block all public access"
aws s3api put-public-access-block \
  --bucket $S3_BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Apply bucket policy allowing public reads on the OIDC documents only
cat <<EOF > bucket-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": [
        "arn:aws:s3:::${S3_BUCKET_NAME}/.well-known/openid-configuration",
        "arn:aws:s3:::${S3_BUCKET_NAME}/openid/v1/jwks"
      ]
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket $S3_BUCKET_NAME \
  --policy file://bucket-policy.json
```

#### Step 7: Verify Public Access

```bash
curl https://${ISSUER_HOSTPATH}/.well-known/openid-configuration
curl https://${ISSUER_HOSTPATH}/openid/v1/jwks
```

Both commands should return valid JSON.

#### Step 8: Update the Kubernetes API Server

Your `kube-apiserver` must use the S3 URL as its service account issuer so that
tokens it mints are verifiable by AWS via the public OIDC documents.

Edit `/etc/kubernetes/manifests/kube-apiserver.yaml` on **all control-plane
nodes** (typically 3):

Find the existing flag:

```yaml
- --service-account-issuer=https://kubernetes.default.svc.cluster.local
```

Replace it with the following set of flags:

```yaml
- --service-account-issuer=https://<ISSUER_HOSTPATH>
- --service-account-issuer=https://kubernetes.default.svc.cluster.local
- --service-account-jwks-uri=https://<ISSUER_HOSTPATH>/openid/v1/jwks
- --api-audiences=https://kubernetes.default.svc.cluster.local,https://<ISSUER_HOSTPATH>,sts.amazonaws.com
```

> **Note:** Replace `<ISSUER_HOSTPATH>` with your actual value (e.g.,
> `my-oidc-bucket.s3.eu-west-1.amazonaws.com`).

After saving the file, the kubelet will detect the change and automatically
restart the `kube-apiserver` pod. Wait for it to come back up before
proceeding.

#### Step 9: Verify the API Server Configuration

Create a test pod and inspect the mounted ServiceAccount token:

```bash
kubectl run token-test --image=busybox --restart=Never -- sleep 3600
kubectl exec token-test -- cat /run/secrets/kubernetes.io/serviceaccount/token
```

Decode the token at https://jwt.io and verify:

- **`iss`** (issuer) is `https://<ISSUER_HOSTPATH>`
- **`aud`** (audience) list contains all three values:
  - `https://kubernetes.default.svc.cluster.local`
  - `https://<ISSUER_HOSTPATH>`
  - `sts.amazonaws.com`

Clean up when done:

```bash
kubectl delete pod token-test
```

#### Step 10: Register the OIDC Provider in AWS IAM

```bash
# Get the thumbprint of the S3 bucket's TLS certificate (or use a known CA thumbprint)
THUMBPRINT=$(openssl s_client -connect ${ISSUER_HOSTPATH}:443 -servername ${ISSUER_HOSTPATH} \
  </dev/null 2>/dev/null | openssl x509 -fingerprint -noout | sed 's/://g' | cut -d= -f2)

aws iam create-open-id-connect-provider \
  --url "https://${ISSUER_HOSTPATH}" \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "${THUMBPRINT}"
```

#### Step 11: Create the IAM Role with Trust Policy

Create an IAM role that cert-manager can assume. The trust policy restricts
access to the specific ServiceAccount:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_PROVIDER="${ISSUER_HOSTPATH}"

cat <<EOF > trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_PROVIDER}:sub": "system:serviceaccount:cert-manager:cert-manager-route53",
          "${OIDC_PROVIDER}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name cert-manager-route53 \
  --assume-role-policy-document file://trust-policy.json
```

#### Step 12: Attach Route53 Permissions to the Role

```bash
cat <<EOF > route53-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:GetChange",
        "route53:ChangeResourceRecordSets",
        "route53:ListHostedZonesByName"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name cert-manager-route53 \
  --policy-name Route53Access \
  --policy-document file://route53-policy.json
```

#### Step 13: Apply the Atmosphere Configuration

With all prerequisites complete, set the Atmosphere variables and run the
playbook:

```yaml
cluster_issuer_acme_email: user@example.com
cluster_issuer_acme_solver: route53
cluster_issuer_acme_route53_auth: kubernetes
cluster_issuer_acme_route53_region: eu-west-1
cluster_issuer_acme_route53_hosted_zone_id: Z0123456789EXAMPLE
cluster_issuer_acme_route53_role_arn: arn:aws:iam::123456789012:role/cert-manager-route53
```

---

## Variables Reference

| Variable                                          | Default                                      | Description                                         |
|---------------------------------------------------|----------------------------------------------|-----------------------------------------------------|
| `cluster_issuer_acme_route53_auth`                | `static`                                     | Auth mode: `static`, `ambient`, or `kubernetes`     |
| `cluster_issuer_acme_route53_region`              | —                                            | AWS region for Route53 API calls                    |
| `cluster_issuer_acme_route53_hosted_zone_id`      | —                                            | Route53 hosted zone ID                              |
| `cluster_issuer_acme_route53_access_key_id`       | —                                            | IAM access key (static mode only)                   |
| `cluster_issuer_acme_route53_secret_access_key`   | —                                            | IAM secret key (static mode only)                   |
| `cluster_issuer_acme_route53_role_arn`            | —                                            | IAM role ARN to assume (required for `kubernetes`)  |
| `cluster_issuer_acme_route53_service_account_name`| `cert-manager-route53`                       | ServiceAccount name (`kubernetes` mode)             |
| `cluster_issuer_acme_route53_secret_name`         | `cert-manager-issuer-route53-credentials`    | Secret name for static credentials                  |
