# Ceph OSD Exporter Chart Migration

This PR prepares the Ceph OSD Exporter Helm chart for migration from the atmosphere repository to the ceph_osd_exporter repository where it belongs.

## 🎯 Objective

Move the Helm chart from `vexxhost/atmosphere/pull/2457` to `vexxhost/ceph_osd_exporter` repository, following the pattern of other standalone tools and exporters.

## 📦 What's Included

### 1. Ready-to-Apply Patch File
- **File**: `ceph-osd-exporter-chart.patch` (28 KB)
- Contains complete chart with all templates, documentation, and CI/CD workflows
- Includes DCO sign-off
- Tested and verified to apply cleanly

### 2. Comprehensive Documentation
- **CEPH_OSD_EXPORTER_CHART_MIGRATION.md**: Step-by-step migration guide
- **SUMMARY.md**: Executive summary and next steps
- **VERIFICATION.md**: Test results and verification report
- **README_PR.md**: This file

## ✅ What's Ready

The chart includes everything needed for production deployment:

- ✅ Complete Helm chart (Chart.yaml, values.yaml, templates/)
- ✅ DaemonSet deployment for Ceph OSD nodes
- ✅ RBAC resources (ClusterRole, ClusterRoleBinding, Role, RoleBinding)
- ✅ ServiceAccount
- ✅ Service for metrics endpoint (port 9282)
- ✅ ServiceMonitor for Prometheus Operator
- ✅ PrometheusRule for alerting
- ✅ Ingress configuration (optional)
- ✅ Comprehensive README with parameters documentation
- ✅ GitHub Actions workflow for automated releases
- ✅ Chart Releaser configuration
- ✅ Helm lint passes
- ✅ Chart renders correctly
- ✅ Follows Helm best practices
- ✅ DCO sign-off included

## 🚀 How to Use This

### For Maintainers with Write Access to ceph_osd_exporter

1. **Apply the patch**:
   ```bash
   git clone https://github.com/vexxhost/ceph_osd_exporter.git
   cd ceph_osd_exporter
   git checkout -b add-helm-chart
   git am /path/to/ceph-osd-exporter-chart.patch
   git push origin add-helm-chart
   ```

2. **Create a PR** in the ceph_osd_exporter repository

3. **After merge, enable GitHub Pages**:
   - Go to repository Settings → Pages
   - Set source to "gh-pages" branch
   - Chart will be available at https://vexxhost.github.io/ceph_osd_exporter

4. **Update atmosphere** (in a follow-up PR):
   - Update `.charts.yml` to point to the new chart URL
   - Remove vendored chart from `charts/ceph-osd-exporter/`
   - Run chart vendor to fetch from new location

### For Testing

```bash
# Lint the chart
helm lint ./chart

# Render templates
helm template test-release ./chart --namespace test-namespace

# Install (if you have a test cluster)
helm install ceph-osd-exporter ./chart
```

## 📋 Next Steps

1. ✅ Chart preparation - **COMPLETE**
2. ✅ Documentation - **COMPLETE**
3. ✅ Testing and verification - **COMPLETE**
4. ⏳ Apply patch to ceph_osd_exporter - **PENDING**
5. ⏳ Create PR in ceph_osd_exporter - **PENDING**
6. ⏳ Enable GitHub Pages - **PENDING**
7. ⏳ Update atmosphere repository - **PENDING**

## 📚 Related

- Original atmosphere PR: #2457
- Previous ceph_osd_exporter PR: vexxhost/ceph_osd_exporter#4 (closed)
- Issue: ATMOSPHERE-161

## 🔍 Files in This PR

```
atmosphere/
├── ceph-osd-exporter-chart.patch          # Git patch file (28 KB)
├── CEPH_OSD_EXPORTER_CHART_MIGRATION.md   # Migration guide (5.8 KB)
├── SUMMARY.md                              # Executive summary (2.7 KB)
├── VERIFICATION.md                         # Test results (2.5 KB)
└── README_PR.md                            # This file
```

## ❓ Questions?

Refer to the comprehensive migration guide: `CEPH_OSD_EXPORTER_CHART_MIGRATION.md`
