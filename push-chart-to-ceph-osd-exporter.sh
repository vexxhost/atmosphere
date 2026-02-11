#!/bin/bash
# Script to push the Helm chart to ceph_osd_exporter repository
# This script should be run by someone with write access to vexxhost/ceph_osd_exporter

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PATCH_FILE="$SCRIPT_DIR/ceph-osd-exporter-chart.patch"

echo "=== Ceph OSD Exporter Chart Migration Script ==="
echo

if [ ! -f "$PATCH_FILE" ]; then
    echo "ERROR: Patch file not found at $PATCH_FILE"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "ERROR: This script should be run from a git repository"
    exit 1
fi

# Check if this is the ceph_osd_exporter repo
REMOTE_URL=$(git config --get remote.origin.url || echo "")
if [[ ! "$REMOTE_URL" =~ "ceph_osd_exporter" ]]; then
    echo "ERROR: This doesn't appear to be the ceph_osd_exporter repository"
    echo "Current remote: $REMOTE_URL"
    echo
    echo "Please clone the repository first:"
    echo "  git clone git@github.com:vexxhost/ceph_osd_exporter.git"
    echo "  cd ceph_osd_exporter"
    echo "  /path/to/this/script.sh"
    exit 1
fi

echo "Repository check: OK"
echo "Patch file: $PATCH_FILE"
echo

# Create feature branch
BRANCH_NAME="add-helm-chart"
echo "Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"

# Apply the patch
echo "Applying patch..."
if git am "$PATCH_FILE"; then
    echo "✓ Patch applied successfully"
else
    echo "ERROR: Failed to apply patch"
    echo "You may need to resolve conflicts manually"
    exit 1
fi

echo
echo "=== Verification ==="

# Verify chart
if command -v helm &> /dev/null; then
    echo "Running helm lint..."
    helm lint ./chart
else
    echo "WARNING: helm not found, skipping lint"
fi

echo
echo "=== Next Steps ==="
echo
echo "1. Review the changes:"
echo "   git log -1"
echo "   git show HEAD"
echo
echo "2. Push to your fork (if you have one):"
echo "   git push -u origin $BRANCH_NAME"
echo
echo "3. OR push directly to vexxhost (requires write access):"
echo "   git push -u origin $BRANCH_NAME"
echo
echo "4. Create a PR on GitHub:"
echo "   https://github.com/vexxhost/ceph_osd_exporter/compare/main...$BRANCH_NAME"
echo
echo "5. After merge, enable GitHub Pages:"
echo "   - Go to repository Settings → Pages"
echo "   - Set source to 'gh-pages' branch"
echo
echo "6. Update atmosphere repository to use the new chart location"
echo
