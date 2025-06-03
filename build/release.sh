#!/bin/bash -xe

# Use reno to suggest the next version
SUGGESTED_VERSION=$(reno semver-next)

# Prompt user for input
echo "Suggested version: $SUGGESTED_VERSION"
read -p "Use suggested version? [Y/n] (or enter custom version): " USER_INPUT

# Process user input
if [[ "$USER_INPUT" == "" || "$USER_INPUT" == "Y" || "$USER_INPUT" == "y" ]]; then
    VERSION=$SUGGESTED_VERSION
    echo "Using suggested version: $VERSION"
elif [[ "$USER_INPUT" == "n" || "$USER_INPUT" == "N" ]]; then
    read -p "Enter version to use: " VERSION
    echo "Using manual version: $VERSION"
else
    VERSION=$USER_INPUT
    echo "Using provided version: $VERSION"
fi

if [ -z "$VERSION" ]; then
  echo "No version specified. Exiting."
  exit 1
fi

echo "Updating local repository with latest remote information..."
git fetch --all --prune
git pull --rebase

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_RELEASE=$(echo $CURRENT_BRANCH | grep -oE '[0-9]{4}\.[0-9]' || echo "")

if [ -z "$CURRENT_RELEASE" ]; then
  echo "Could not determine version from branch name: $CURRENT_RELEASE"
  exit 1
fi

LATEST_RELEASE=$(git branch -r | grep 'origin/stable/[0-9]\{4\}\.[0-9]' |
                 sed 's/.*origin\/stable\///' |
                 grep -v 'zed' |
                 sort -V |
                 tail -1)

LATEST_FLAG="false"
if [ "$CURRENT_RELEASE" = "$LATEST_RELEASE" ]; then
  LATEST_FLAG="true"
fi

echo "Current version: $CURRENT_RELEASE"
echo "Latest version: $LATEST_RELEASE"
echo "Setting latest flag to: $LATEST_FLAG"

# Generate release notes
RELEASE_NOTES=$(reno report 2>/dev/null | uv run --isolated --with rst-to-myst rst2myst stream --no-sphinx - | egrep -v '^(%|\(release-notes|# Release Notes)' | awk '/^## /{if(count==1) exit; if(count==0) {count++; next}} count==1')

# Show release notes to user
echo "====================== RELEASE NOTES ======================"
echo "$RELEASE_NOTES"
echo "=========================================================="

# Final confirmation before making changes
echo "Ready to release version $VERSION with latest=$LATEST_FLAG"
read -p "Proceed with release? [Y/n]: " CONFIRM
if [[ "$CONFIRM" == "n" || "$CONFIRM" == "N" ]]; then
  echo "Release cancelled."
  exit 0
fi

# Update the version
sed -i s/^version:.*/version:\ $VERSION/ galaxy.yml
sed -i s/^atmosphere_version:.*/atmosphere_version:\ $VERSION/ roles/defaults/defaults/main.yml

# Create release commit
git add galaxy.yml roles/defaults/defaults/main.yml
git commit -m "Release $VERSION"

# Push the release commit
git push

# Generate release notes again and save to a temp file
TEMP_NOTES_FILE=$(mktemp)
echo "$RELEASE_NOTES" > "$TEMP_NOTES_FILE"

# Create GitHub release with gh CLI
gh release create v$VERSION --target $(git rev-parse HEAD) --notes-file "$TEMP_NOTES_FILE" --latest=$LATEST_FLAG

# Clean up temp file
rm -f "$TEMP_NOTES_FILE"
