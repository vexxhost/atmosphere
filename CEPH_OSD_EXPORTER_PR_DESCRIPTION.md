# Add Helm Chart for Ceph OSD Exporter

This PR adds a Helm chart for deploying ceph-osd-exporter as a DaemonSet on Kubernetes clusters.

## Overview

This chart enables Prometheus monitoring of Ceph OSD performance by deploying the ceph-osd-exporter on nodes running Ceph OSDs.

## What's Included

### Helm Chart (`chart/`)

Complete Helm chart with:
- **DaemonSet**: Deploys exporter on nodes with label `ceph-osd-exporter: enabled`
- **RBAC**: ClusterRole, ClusterRoleBinding, Role, and RoleBinding for pod listing
- **ServiceAccount**: Dedicated service account
- **Service**: Metrics endpoint on port 9282
- **ServiceMonitor**: Optional Prometheus Operator integration
- **PrometheusRule**: Optional alerting rules
- **Ingress**: Optional ingress configuration
- **README.md**: Comprehensive documentation with parameters table

### GitHub Actions Workflow (`.github/workflows/release.yaml`)

Automated chart release workflow that:
- Triggers on changes to `chart/**` on main branch
- Uses `helm/chart-releaser-action@v1.6.0`
- Packages and publishes charts to GitHub Pages
- Creates GitHub releases for each chart version
- Requires GitHub Pages to be enabled (see Post-Merge Setup)

### Chart Releaser Configuration (`.github/cr.yaml`)

Configuration for chart-releaser specifying:
- Repository: `vexxhost/ceph_osd_exporter`
- Chart URL: `https://vexxhost.github.io/ceph_osd_exporter`

## Installation

After this PR is merged and GitHub Pages is enabled:

```bash
# Add the repository
helm repo add ceph-osd-exporter https://vexxhost.github.io/ceph_osd_exporter
helm repo update

# Install the chart
helm install ceph-osd-exporter ceph-osd-exporter/ceph-osd-exporter
```

Or install directly from the chart directory:

```bash
helm install ceph-osd-exporter ./chart
```

## Configuration

Key parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image | `registry.atmosphere.dev/library/ceph-osd-exporter` |
| `image.tag` | Image tag | `latest` |
| `nodeSelector` | Node selector | `{ceph-osd-exporter: enabled}` |
| `serviceMonitor.enabled` | Enable ServiceMonitor | `false` |
| `prometheusRule.enabled` | Enable PrometheusRule | `false` |

See `chart/README.md` for full parameters documentation.

## Testing

The chart has been tested and validated:

```bash
# Lint check
$ helm lint ./chart
==> Linting ./chart
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

# Template rendering
$ helm template test-release ./chart --namespace test
# (Successfully renders all manifests)
```

## Post-Merge Setup

After this PR is merged, enable GitHub Pages:

1. Go to repository Settings → Pages
2. Set source to "gh-pages" branch
3. The chart will be available at: `https://vexxhost.github.io/ceph_osd_exporter`

The GitHub Actions workflow will automatically:
- Create a `gh-pages` branch if it doesn't exist
- Package the chart and update the index
- Create a GitHub release with the chart package

## Integration with Atmosphere

After the chart is published, update `vexxhost/atmosphere`:

1. Update `.charts.yml`:
   ```yaml
   - name: ceph-osd-exporter
     version: 0.1.0
     repository:
       url: https://vexxhost.github.io/ceph_osd_exporter
   ```

2. Remove vendored chart from `charts/ceph-osd-exporter/`
3. Run `make vendor-charts` to fetch from new location

## Related

- Atmosphere PR: https://github.com/vexxhost/atmosphere/pull/2457
- Issue: ATMOSPHERE-161

## Checklist

- [x] Chart follows Helm best practices
- [x] Helm lint passes
- [x] Chart renders correctly
- [x] README documentation complete
- [x] GitHub Actions workflow configured
- [x] Chart Releaser configured
- [x] DCO sign-off included
