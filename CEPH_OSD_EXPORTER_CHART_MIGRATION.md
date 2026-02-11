# Ceph OSD Exporter Chart Migration Guide

## Overview

This document describes the process of moving the Ceph OSD Exporter Helm chart from the `vexxhost/atmosphere` repository (PR #2457) to the `vexxhost/ceph_osd_exporter` repository where it belongs.

## Background

PR #2457 in the atmosphere repository added initial support for the Ceph OSD Exporter, including a Helm chart. However, following the pattern of other exporters and tools, the chart should be maintained in the `ceph_osd_exporter` repository itself, not in atmosphere.

## Chart Files to Move

The following files from `charts/ceph-osd-exporter/` in atmosphere PR #2457 need to be moved:

- `.helmignore`
- `Chart.yaml`
- `values.yaml`
- `templates/_helpers.tpl`
- `templates/clusterrole.yaml`
- `templates/clusterrolebinding.yaml`
- `templates/daemonset.yaml`
- `templates/ingress.yaml`
- `templates/prometheusrule.yaml`
- `templates/role.yaml`
- `templates/rolebinding.yaml`
- `templates/service.yaml`
- `templates/serviceaccount.yaml`
- `templates/servicemonitor.yaml`

## Additional Files to Add to ceph_osd_exporter

### 1. Chart README (`chart/README.md`)

A comprehensive README has been prepared that includes:
- Introduction and prerequisites
- Installation instructions
- Parameters documentation
- Configuration examples
- License information

### 2. GitHub Actions Workflow (`.github/workflows/release.yaml`)

A workflow for automated chart releases using `helm/chart-releaser-action` that:
- Triggers on changes to the `chart/**` path
- Uses chart-releaser to package and publish charts to GitHub Pages
- Creates GitHub releases for each chart version

### 3. Chart Releaser Configuration (`.github/cr.yaml`)

Configuration file for chart-releaser specifying:
- Repository owner and name
- Charts repository URL (https://vexxhost.github.io/ceph_osd_exporter)

## Implementation Steps

A complete implementation has been prepared in `/tmp/ceph_osd_exporter` with all necessary files. To apply these changes to the ceph_osd_exporter repository:

### Option 1: Using the Prepared Patch File

A git patch file has been created at `/tmp/ceph_osd_exporter/0001-feat-chart-add-Helm-chart-for-ceph-osd-exporter.patch` that contains all the changes.

To apply this patch to the ceph_osd_exporter repository:

```bash
# Clone the ceph_osd_exporter repository
git clone https://github.com/vexxhost/ceph_osd_exporter.git
cd ceph_osd_exporter

# Create a new branch
git checkout -b add-helm-chart

# Apply the patch
git am /tmp/ceph_osd_exporter/0001-feat-chart-add-Helm-chart-for-ceph-osd-exporter.patch

# Push to your fork and create a PR
git push origin add-helm-chart
```

### Option 2: Manual Copy

Alternatively, manually copy the prepared files:

```bash
# Clone the ceph_osd_exporter repository
git clone https://github.com/vexxhost/ceph_osd_exporter.git
cd ceph_osd_exporter

# Create a new branch
git checkout -b add-helm-chart

# Copy the chart directory
cp -r /tmp/ceph_osd_exporter/chart ./

# Copy the GitHub workflows and config
cp /tmp/ceph_osd_exporter/.github/workflows/release.yaml .github/workflows/
cp /tmp/ceph_osd_exporter/.github/cr.yaml .github/

# Commit and push
git add -A
git commit -s -m "feat(chart): add Helm chart for ceph-osd-exporter"
git push origin add-helm-chart
```

## Chart Structure

The chart follows the standard Helm chart structure:

```
chart/
├── .helmignore
├── Chart.yaml          # Chart metadata
├── README.md           # Chart documentation
├── values.yaml         # Default configuration values
└── templates/          # Kubernetes manifests
    ├── _helpers.tpl
    ├── clusterrole.yaml
    ├── clusterrolebinding.yaml
    ├── daemonset.yaml
    ├── ingress.yaml
    ├── prometheusrule.yaml
    ├── role.yaml
    ├── rolebinding.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    └── servicemonitor.yaml
```

## After the Chart is Released

Once the chart is available in the ceph_osd_exporter repository and released:

1. Update `.charts.yml` in atmosphere to reference the correct chart URL:
   ```yaml
   - name: ceph-osd-exporter
     version: 0.1.0
     repository:
       url: https://vexxhost.github.io/ceph_osd_exporter
   ```

2. Remove the vendored chart from `charts/ceph-osd-exporter/` in atmosphere

3. Run `make vendor-charts` to fetch the chart from the new repository

## GitHub Pages Setup

After merging the PR in ceph_osd_exporter, you'll need to enable GitHub Pages:

1. Go to the repository settings
2. Navigate to "Pages"
3. Set the source to "gh-pages" branch
4. The chart will be available at `https://vexxhost.github.io/ceph_osd_exporter`

## Testing the Chart

Before using the chart in atmosphere, test it locally:

```bash
# Install the chart
helm install ceph-osd-exporter ./chart

# Check the deployment
kubectl get pods -l app=ceph-osd-exporter

# Verify the service
kubectl get svc ceph-osd-exporter

# Test with custom values
helm install ceph-osd-exporter ./chart -f custom-values.yaml
```

## References

- Original PR in atmosphere: https://github.com/vexxhost/atmosphere/pull/2457
- Related PR in ceph_osd_exporter: https://github.com/vexxhost/ceph_osd_exporter/pull/4
- Chart Releaser Action: https://github.com/helm/chart-releaser-action
- Helm Charts Best Practices: https://helm.sh/docs/chart_best_practices/

## Notes

- The chart version in `Chart.yaml` is set to `0.1.0` to match the initial release
- The `appVersion` is also set to `0.1.0` to match the ceph-osd-exporter version
- The chart includes ServiceMonitor and PrometheusRule resources for Prometheus Operator integration
- Node selector is configured to deploy only on nodes with label `ceph-osd-exporter: enabled`
- Security context is configured with `runAsUser: 0` (root) as required for accessing Ceph data
