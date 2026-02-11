# Next Steps for Repository Maintainer

## Current Status ✅

Everything is **READY TO GO**! The Helm chart has been:
- ✅ Extracted from atmosphere PR #2457
- ✅ Enhanced with production features
- ✅ Tested and validated with helm lint
- ✅ Applied to a local ceph_osd_exporter repository
- ✅ Committed to branch `add-helm-chart`
- ✅ Includes chart-releaser-action GitHub workflow
- ✅ Includes comprehensive documentation

## What You Need to Do

### Step 1: Clone or Use Existing Repository

You have **three options**:

#### Option A: Use the Pre-Prepared Repository (Fastest)

If you're running this in the same environment where the work was done:

```bash
cd /tmp/ceph_osd_exporter
# The branch add-helm-chart is already set up!
git remote -v  # Verify remote
git push -u origin add-helm-chart
```

#### Option B: Use the Helper Script (Recommended)

```bash
# Clone the repository
git clone git@github.com:vexxhost/ceph_osd_exporter.git
cd ceph_osd_exporter

# Run the script from this atmosphere repository
/path/to/atmosphere/push-chart-to-ceph-osd-exporter.sh

# Push the branch
git push -u origin add-helm-chart
```

#### Option C: Manual Application

```bash
# Clone the repository
git clone git@github.com:vexxhost/ceph_osd_exporter.git
cd ceph_osd_exporter

# Create branch and apply patch
git checkout -b add-helm-chart
git am /path/to/atmosphere/ceph-osd-exporter-chart.patch

# Verify
helm lint ./chart

# Push
git push -u origin add-helm-chart
```

### Step 2: Create Pull Request

1. Go to: https://github.com/vexxhost/ceph_osd_exporter/compare/main...add-helm-chart

2. Use the PR description from: `CEPH_OSD_EXPORTER_PR_DESCRIPTION.md`

3. Key points to mention:
   - Adds Helm chart for ceph-osd-exporter
   - Includes GitHub Actions workflow for automated releases
   - Chart will be published to GitHub Pages
   - Related to atmosphere PR #2457

### Step 3: After PR is Merged

#### 3a. Enable GitHub Pages

1. Go to repository **Settings** → **Pages**
2. Under "Source", select **gh-pages** branch
3. Click **Save**
4. The chart will be available at: `https://vexxhost.github.io/ceph_osd_exporter`

The GitHub Actions workflow will automatically:
- Create the `gh-pages` branch if it doesn't exist
- Package the chart
- Update the index.yaml
- Create a GitHub release

#### 3b. Update Atmosphere Repository

Create a new PR in the atmosphere repository with these changes:

1. **Update `.charts.yml`**:
   ```yaml
   - name: ceph-osd-exporter
     version: 0.1.0
     repository:
       url: https://vexxhost.github.io/ceph_osd_exporter
   ```

2. **Remove vendored chart**:
   ```bash
   rm -rf charts/ceph-osd-exporter
   ```

3. **Run chart vendor**:
   ```bash
   make vendor-charts
   ```

4. **Commit and push**:
   ```bash
   git add .charts.yml charts/
   git commit -s -m "feat: migrate ceph-osd-exporter chart to upstream repository"
   git push origin <your-branch>
   ```

## Files Available in Atmosphere Repository

All these files are in the atmosphere repository for reference:

| File | Size | Description |
|------|------|-------------|
| `ceph-osd-exporter-chart.patch` | 28 KB | Git patch with all changes |
| `CEPH_OSD_EXPORTER_CHART_MIGRATION.md` | 5.8 KB | Comprehensive migration guide |
| `CEPH_OSD_EXPORTER_PR_DESCRIPTION.md` | 3.7 KB | Ready-to-use PR description |
| `IMPLEMENTATION_COMPLETE.md` | 4.6 KB | Final status report |
| `push-chart-to-ceph-osd-exporter.sh` | 2.4 KB | Automated helper script |
| `SUMMARY.md` | 2.9 KB | Executive summary |
| `VERIFICATION.md` | 2.8 KB | Test results |
| `README_PR.md` | 3.6 KB | PR overview |
| `NEXT_STEPS_FOR_MAINTAINER.md` | This file | Step-by-step guide |

## Quick Command Reference

```bash
# Check current state of ceph_osd_exporter
cd /tmp/ceph_osd_exporter  # If available in this session
git status
git log --oneline -3

# Push the branch
git push -u origin add-helm-chart

# After merge, test the chart
helm repo add ceph-osd-exporter https://vexxhost.github.io/ceph_osd_exporter
helm repo update
helm search repo ceph-osd-exporter
```

## Validation Checklist

Before pushing, verify:
- [ ] Branch name is `add-helm-chart`
- [ ] Commit includes DCO sign-off
- [ ] Helm lint passes
- [ ] All files are present (chart/, .github/)
- [ ] GitHub remote is set correctly

## Support

If you encounter any issues:
1. Check the comprehensive guides in the atmosphere repository
2. Verify git remote configuration
3. Ensure you have write access to vexxhost/ceph_osd_exporter
4. Review the patch file for what changes should be applied

## Timeline

Estimated time to complete:
- **Step 1 (Push)**: 2-5 minutes
- **Step 2 (Create PR)**: 2-3 minutes
- **Step 3a (Enable Pages)**: 1-2 minutes after merge
- **Step 3b (Update atmosphere)**: 10-15 minutes

Total: ~20-30 minutes from start to finish

## Success Criteria

You'll know everything worked when:
1. ✅ PR is created in ceph_osd_exporter
2. ✅ PR is merged
3. ✅ GitHub Pages is enabled
4. ✅ Chart is accessible at https://vexxhost.github.io/ceph_osd_exporter
5. ✅ `helm repo add` and `helm search` work correctly
6. ✅ Atmosphere repository is updated to use the new chart location

---

**Ready to proceed?** Start with Step 1 above! 🚀
